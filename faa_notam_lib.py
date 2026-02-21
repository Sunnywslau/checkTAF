import re
import requests
import time
import urllib3

class FAAClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api-staging.cgifederal-aim.com"
        self._access_token = None
        self._expires_at = 0
        self.session = requests.Session()

    def _authenticate(self):
        if self._access_token and time.time() < (self._expires_at - 60):
            return
        url = f"{self.base_url}/v1/auth/token"
        payload = {'grant_type': 'client_credentials'}
        response = self.session.post(url, data=payload, auth=(self.client_id, self.client_secret), verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        self._access_token = data['access_token']
        self._expires_at = int(time.time()) + int(data.get('expires_in', 1799))

    def get_raw_notams(self, location=None):
        self._authenticate()
        endpoint = f"{self.base_url}/nmsapi/v1/notams"
        params = {'location': location} if location else {}
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "nmsResponseFormat": "GEOJSON",
            "Accept": "application/json"
        }
        response = self.session.get(endpoint, params=params, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_notams(self, location, query="", search_type="keyword", is_regex=False):
        """
        Search and filter NOTAMs with robust deduplication.
        """
        raw_data = self.get_raw_notams(location)
        if raw_data.get('status') != "Success":
            return []

        features = raw_data.get('data', {}).get('geojson', [])
        filtered_list = []
        
        query_str = str(query).strip()
        query_upper = query_str.upper() if not is_regex else ""

        for item in features:
            core = item.get('properties', {}).get('coreNOTAMData', {})
            notam_info = core.get('notam', {})
            raw_text = notam_info.get('text', '')
            translations = core.get('notamTranslation', [])
            formatted = translations[0].get('formattedText', '') if translations else ''
            
            full_text = f"{raw_text} {formatted}".upper()
            is_match = False
            
            if not query_str or search_type == "all":
                is_match = True
            elif search_type == "runway":
                has_rwy_word = re.search(r"\bRWY\b|\bRUNWAY\b", full_text)
                if is_regex:
                    has_number = re.search(query_str, full_text, re.IGNORECASE)
                else:
                    number_pattern = r"(?<!\d)" + re.escape(query_upper) + r"(?![0-9])"
                    has_number = re.search(number_pattern, full_text)
                if has_rwy_word and has_number:
                    is_match = True
            else: # keyword search
                if is_regex:
                    try:
                        if re.search(query_str, full_text, re.IGNORECASE):
                            is_match = True
                    except re.error:
                        if query_upper in full_text: is_match = True
                else:
                    if query_upper in full_text:
                        is_match = True

            if is_match:
                # ID Reconstruction logic
                series = str(core.get('notam', {}).get('series') or "").strip()
                raw_num = str(core.get('notam', {}).get('number', '0000')).strip()
                number = raw_num
                if series and raw_num.startswith(series):
                    number = raw_num[len(series):]
                
                # Clean year suffix if present (e.g., 2412/26 -> 2412)
                if '/' in number:
                    parts = number.split('/')
                    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) <= 2:
                        number = parts[0]
                
                raw_year = str(core.get('notam', {}).get('year', '')).strip()
                year = raw_year[-2:] if len(raw_year) > 2 else raw_year
                if not year: year = "26" 
                
                type_code = core.get('notam', {}).get('type', 'N')
                if type_code == 'C': continue 
                
                def icao_date(dt_str):
                    if not dt_str: return "PERM"
                    clean = re.sub(r'[-:T]', '', str(dt_str))
                    return clean[2:12]

                effective_start = str(notam_info.get('effectiveStart') or "")
                effective_end = str(notam_info.get('effectiveEnd') or "")
                classification = notam_info.get('classification', 'DOM')
                
                loc_str = str(notam_info.get('location') or "").upper()
                # Normalize location for dedup (JFK -> KJFK)
                norm_loc = loc_str if loc_str.startswith('K') and len(loc_str) == 4 else (f"K{loc_str}" if len(loc_str) == 3 else loc_str)

                q_code = notam_info.get('selectionCode', 'XXXXX')
                
                # Deduplication Key Normalization
                # Strip Z and seconds for stable matching
                n_start = effective_start.replace('Z', '').split('.')[0]
                n_end = effective_end.replace('Z', '').split('.')[0]
                n_subj = q_code[1:3] if len(q_code) >= 3 else q_code

                # Q-line Reconstruction
                fir = notam_info.get('affectedFir', 'XXXX')
                traffic = notam_info.get('traffic', 'IV')
                purpose = notam_info.get('purpose', 'NBO')
                scope = notam_info.get('scope', 'A')
                low = notam_info.get('minimumFl', '000')
                high = notam_info.get('maximumFl', '999')
                coord = notam_info.get('coordinates', '')
                radius = notam_info.get('radius', '')
                q_coord = f"{coord}{str(radius).zfill(3)}" if coord else "XXXXX/..."
                q_line = f"Q) {fir}/{q_code}/{traffic}/{purpose}/{scope}/{low}/{high}/{q_coord}"

                new_notam = {
                    "id": f"{series}{number}/{year} NOTAM{type_code}",
                    "location": loc_str,
                    "start": icao_date(effective_start),
                    "end": icao_date(effective_end),
                    "text": raw_text,
                    "full_icao": formatted,
                    "status": notam_info.get('status', 'Active'),
                    "q_line": q_line,
                    "schedule": core.get('notam', {}).get('schedule', ''),
                    "keyword": q_code,
                    "classification": classification,
                    "_n_key": (n_subj, n_start, n_end, norm_loc)
                }

                existing_idx = None
                for i, existing in enumerate(filtered_list):
                    if existing['_n_key'] == new_notam['_n_key']:
                        # Text similarity check
                        t1 = re.sub(r'^' + re.escape(loc_str) + r'\s*', '', existing['text'].strip()).upper()
                        t2 = re.sub(r'^' + re.escape(loc_str) + r'\s*', '', new_notam['text'].strip()).upper()
                        
                        # Match if text is similar or inclusive
                        if t1 in t2 or t2 in t1 or abs(len(t1) - len(t2)) < 30:
                            existing_idx = i
                            break
                
                if existing_idx is not None:
                    # Prefer INTL version or the one with longer ID (likely has series)
                    if classification == 'INTL' or len(new_notam['id']) > len(filtered_list[existing_idx]['id']):
                        filtered_list[existing_idx] = new_notam
                else:
                    filtered_list.append(new_notam)

        # Cleanup internal keys
        for n in filtered_list:
            n.pop('_n_key', None)
            
        return filtered_list