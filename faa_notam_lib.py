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
        # Added timeout=30
        response = self.session.post(url, data=payload, auth=(self.client_id, self.client_secret), verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        self._access_token = data['access_token']
        # Default expires_in is usually 3599 from FAA, fallback to 1799 if missing
        self._expires_at = time.time() + int(data.get('expires_in', 1799))

    def get_raw_notams(self, location=None):
        self._authenticate()
        endpoint = f"{self.base_url}/nmsapi/v1/notams"
        params = {'location': location} if location else {}
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "nmsResponseFormat": "GEOJSON",
            "Accept": "application/json"
        }
        # Added timeout=30
        response = self.session.get(endpoint, params=params, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()

    # Fixed: Changed ddef to def
    def search_notams(self, location, query="", search_type="keyword", is_regex=False):
        """
        Search and filter NOTAMs.
        :param location: ICAO code (e.g., 'KJFK')
        :param query: text to search for
        :param search_type: 'keyword', 'runway', or 'all' (return everything)
        :param is_regex: Treat query as a regex pattern if True (only for keyword search)
        """
        raw_data = self.get_raw_notams(location)
        if raw_data.get('status') != "Success":
            return []

        features = raw_data.get('data', {}).get('geojson', [])
        filtered_list = []
        
        # Pre-process query
        query_str = str(query).strip()
        if not is_regex:
             query_upper = query_str.upper()

        for item in features:
            core = item.get('properties', {}).get('coreNOTAMData', {})
            notam_info = core.get('notam', {})
            raw_text = notam_info.get('text', '')
            translations = core.get('notamTranslation', [])
            formatted = translations[0].get('formattedText', '') if translations else ''
            
            # Construct a full searchable text blob
            full_text = f"{raw_text} {formatted}".upper()
            
            is_match = False
            
            if not query_str and search_type != "all":
                 # If no query provided and not asking for all, skip? 
                 # Or maybe return all? Let's assume if query is empty loop usually continues unless 'all'
                 if search_type == "all":
                     is_match = True
                 else:
                     is_match = True # Fallback: empty query matches everything usually
            
            elif search_type == "all":
                is_match = True

            elif search_type == "runway":
                # Logic: Must mention 'RWY/RUNWAY' AND the specific number/letter combo
                has_rwy_word = re.search(r"\bRWY\b|\bRUNWAY\b", full_text)
                # Strict runway regex: Look for the number avoiding partials (e.g. searching 07 shouldn't match 075)
                # But allow 07R, 07L, etc.
                if is_regex:
                     # If user passed regex for runway? unlikely but support it
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
                        # Fallback to string match if regex invalid
                        if query_str.upper() in full_text:
                            is_match = True
                else:
                    if query_upper in full_text:
                        is_match = True

            if is_match:
                # Reconstruct ICAO format parts
                series = str(core.get('notam', {}).get('series', '')).strip()
                raw_num = str(core.get('notam', {}).get('number', '0000')).strip()
                
                # 1st Fix: Clean number: Remove series prefix AND any existing year suffix (e.g., A0041/26 -> 0041)
                num_only = raw_num[len(series):] if raw_num.startswith(series) else raw_num
                number = num_only.split('/')[0] # Remove /26 if present in number
                
                raw_year = str(core.get('notam', {}).get('year', '26')).strip()
                year = raw_year[-2:] if len(raw_year) > 2 else raw_year
                
                type_code = core.get('notam', {}).get('type', 'N')
                
                # Filter out NOTAMC (Cancel NOTAMs) as requested
                if type_code == 'C':
                    continue
                
                # ICAO Date Format: YYMMDDHHMM
                def icao_date(dt_str):
                    if not dt_str: return "PERM"
                    clean = re.sub(r'[-:T]', '', str(dt_str))
                    return clean[2:12]

                filtered_list.append({
                    "id": f"{series}{number}/{year} NOTAM{type_code}",
                    "location": notam_info.get('location'),
                    "start": icao_date(notam_info.get('effectiveStart')),
                    "end": icao_date(notam_info.get('effectiveEnd')),
                    "text": raw_text,
                    "full_icao": formatted,
                    "status": notam_info.get('status', 'Active'),
                    "q_line": core.get('notam', {}).get('qCode', 'Q) XXXX/XXXXX/IV/NBO/A/000/999/...'),
                    "schedule": core.get('notam', {}).get('schedule', ''),
                    "keyword": notam_info.get('qCode', 'N/A')
                })
        return filtered_list