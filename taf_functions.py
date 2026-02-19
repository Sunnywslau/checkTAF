"""
TAF Functions Module
Contains all the core functionality for the TAF Information Dashboard
"""

import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- GLOBAL SESSION WITH RETRY ---
def get_session():
    if "api_session" not in st.session_state:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        st.session_state.api_session = session
    return st.session_state.api_session
# ---------------------------------

# --- CONFIGURATION / THRESHOLDS ---
# Dispatcher suitability thresholds
VIS_THRESHOLD = 3000  # Meters
CEILING_THRESHOLD = 1000  # Feet

# Highlight colors
COLOR_CRITICAL_VIS = "red"      # Visibility below threshold
COLOR_CRITICAL_CEIL = "pink"     # Ceiling below threshold
COLOR_UNMEASURED = "purple"     # VV/// or VVnnn
COLOR_FREEZING = "blue"         # Freezing conditions (FZ)
COLOR_SNOW = "green"            # Snow (SN)
# ----------------------------------


@st.cache_data(ttl=300)  # Cache results for 5 minutes
def fetch_taf(airport_ids):
    """Fetch TAF data from aviationweather.gov API with timeout, retries, and caching"""
    if not airport_ids:
        return []
        
    session = get_session()
    url = f"https://aviationweather.gov/api/data/taf?ids={','.join(airport_ids)}"
    try:
        # Spinner is handled outside the cached function for better UI
        response = session.get(url, timeout=20)
        if response.status_code == 200:
            return response.text.strip().splitlines()
        else:
            return []
    except requests.exceptions.RequestException as e:
        return []


def parse_taf_data(taf_lines):
    """Parse TAF data lines into a dictionary"""
    taf_dict = {}
    current_airport = None
    current_taf = []

    for line in taf_lines:
        if line.startswith("TAF") or line.startswith("TAF AMD") or line.startswith("TAF COR"):
            if current_airport and current_taf:
                taf_dict[current_airport] = '\n'.join(current_taf)

            parts = line.split()
            if line.startswith("TAF AMD") or line.startswith("TAF COR"):
                current_airport = parts[2]
            else:
                current_airport = parts[1]

            current_taf = [line]
        elif current_airport:
            current_taf.append(line.strip())

    if current_airport and current_taf:
        taf_dict[current_airport] = '\n'.join(current_taf)

    return taf_dict


def highlight_taf(taf_text):
    """Highlight weather conditions in TAF text using configurable thresholds and keywords"""
    taf_text = taf_text.replace('\n', '<br>')
    
    # Boundary-aware regex patterns (using \b or lookarounds to stay precise)
    # Visibility: 4 digits
    visibility_pattern = r'(?<=\s)(\d{4})(?=\s|<br>|$)'
    # Cloud Ceiling: BKN/OVC followed by 3 digits
    cloud_ceiling_pattern = r'\b(BKN|OVC)(\d{3})\b'
    # Vertical Visibility / Unmeasured
    unmeasured_pattern = r'\b(VV///|VV\d{3})\b'
    # Freezing conditions: FZ anywhere as a weather group (e.g. -FZDZ, FZRA)
    freezing_pattern = r'(?<!\S)(\S*?FZ[A-Z]*)(?!\S)'
    # Snow: SN anywhere as a weather group (e.g. -SN, BLSN, SNRA)
    snow_pattern = r'(?<!\S)(\S*?SN[A-Z]*)(?!\S)'

    def highlight_visibility(match):
        visibility = match.group(0)
        try:
            val = int(visibility)
            if val < VIS_THRESHOLD:
                return f"<span style='color: {COLOR_CRITICAL_VIS}; font-weight: bold;'>{visibility}</span>"
        except ValueError:
            pass
        return visibility

    def highlight_cloud_ceiling(match):
        cloud_type = match.group(1)
        try:
            height = int(match.group(2)) * 100
            if height < CEILING_THRESHOLD:
                return f"<span style='color: {COLOR_CRITICAL_CEIL}; font-weight: bold;'>{cloud_type}{match.group(2)}</span>"
        except ValueError:
            pass
        return match.group(0)

    def highlight_unmeasured(match):
        return f"<span style='color: {COLOR_UNMEASURED}; font-weight: bold;'>{match.group(0)}</span>"

    def highlight_freezing(match):
        return f"<span style='color: {COLOR_FREEZING}; font-weight: bold;'>{match.group(0)}</span>"

    def highlight_snow(match):
        return f"<span style='color: {COLOR_SNOW}; font-weight: bold;'>{match.group(0)}</span>"

    # Sequential regex substitution
    highlighted = re.sub(visibility_pattern, highlight_visibility, taf_text)
    highlighted = re.sub(cloud_ceiling_pattern, highlight_cloud_ceiling, highlighted)
    highlighted = re.sub(unmeasured_pattern, highlight_unmeasured, highlighted)
    highlighted = re.sub(freezing_pattern, highlight_freezing, highlighted)
    highlighted = re.sub(snow_pattern, highlight_snow, highlighted)

    return highlighted


def highlight_notam_text(text, query=""):
    """Highlight critical keywords and search query in NOTAM text"""
    # Critical dispatcher keywords to ALWAYS highlight
    critical_keywords = [
        r'\bCLSD\b', r'\bCLOSED\b', r'\bU/S\b', r'\bUNSERVICEABLE\b', 
        r'\bWIP\b', r'\bWORK IN PROGRESS\b', r'\bMAY BE CLOSED\b'
    ]
    
    # 1. Highlight critical keywords (Yellow background, red text)
    for kw in critical_keywords:
        text = re.sub(kw, lambda m: f"<span class='notam-critical'>{m.group(0)}</span>", text, flags=re.IGNORECASE)
    
    # 2. Highlight Runway patterns (Bold underline)
    rwy_pattern = r'\bRWY\s?\d{2}[LRC]?\b|\bRUNWAY\s?\d{2}[LRC]?\b'
    text = re.sub(rwy_pattern, lambda m: f"<span class='notam-rwy'>{m.group(0)}</span>", text, flags=re.IGNORECASE)

    # 3. Highlight User Search Query (Cyan background)
    if query and len(query) >= 2:
        # Avoid highlighting already created HTML tags
        query_pattern = f"({re.escape(query)})"
        # Only highlight if not inside a tag (simplistic check)
        text = re.sub(query_pattern, lambda m: f"<span class='notam-search'>{m.group(0)}</span>", text, flags=re.IGNORECASE)

    return text


def load_region_data(file_path):
    """Load region to airports mapping from file"""
    region_dict = {}
    try:
        with open(file_path, 'r') as file:
            next(file)  # Skip header if present
            for line in file:
                line = line.strip()
                if line:
                    region, airports = line.split(',', 1)
                    region_dict[region.strip()] = [airport.strip() for airport in airports.split('|')]
    except FileNotFoundError:
        st.error(f"Region configuration file not found: {file_path}")
    return region_dict


def load_airport_data(file_path):
    """Load destination to alternates mapping from file"""
    airport_data = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("airport"):
                    dest, alternates = line.split(',')
                    airport_data[dest.strip()] = [alt.strip() for alt in alternates.split('|')]
    except FileNotFoundError:
        st.error(f"Input file not found: {file_path}")
        return {}
    return airport_data


def load_enroute_alternates(file_path):
    """Load enroute alternates by region from file"""
    enroute_dict = {}
    try:
        with open(file_path, 'r') as file:
            next(file)  # Skip header if present
            for line in file:
                line = line.strip()
                if line:
                    region, airports = line.split(',', 1)
                    enroute_dict[region.strip()] = [airport.strip() for airport in airports.split('|')]
    except FileNotFoundError:
        st.error(f"Enroute alternates file not found: {file_path}")
    return enroute_dict

def get_bootstrap_css():
    """Return Bootstrap CSS and custom styles"""
    return """
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        .table {
            margin-top: 5px;
            font-size: 13px;
            line-height: 1.3;
            table-layout: fixed !important;
            width: 100% !important;
        }
        .table thead th {
            color: white !important;
            font-weight: bold;
            text-align: center;
            font-size: 14px;
            padding: 10px 6px;
            border: 1px solid #dee2e6;
            background-color: #6c757d !important;
        }
        .table tbody td {
            padding: 6px 4px;
            vertical-align: top;
            word-wrap: break-word;
        }
        .table tbody tr:hover {
            background-color: #f8f9fa;
        }
        .destinations-table .table thead th {
            background-color: #007BFF !important;
        }
        .enroute-table .table thead th {
            background-color: #28a745 !important;
        }
        .table-container {
            max-height: 80vh;
            overflow-y: auto;
            margin-top: 0.5rem;
        }
        
        /* Force table headers to be visible */
        table thead {
            display: table-header-group !important;
        }
        
        table thead tr {
            display: table-row !important;
        }
        
        table thead th {
            display: table-cell !important;
            position: sticky;
            top: 0;
            z-index: 10;
            height: 45px;
            line-height: 1.2;
            vertical-align: middle;
        }
        
        /* Set specific column widths for consistent alignment */
        /* Airport column - minimal width */
        .destinations-table table th:nth-child(1), 
        .destinations-table table td:nth-child(1) {
            width: 60px !important;
            min-width: 60px !important;
            max-width: 60px !important;
        }
        
        /* Destinations column - equal width with other content columns */
        .destinations-table table th:nth-child(2), 
        .destinations-table table td:nth-child(2) {
            width: 400px !important;
            min-width: 400px !important;
        }
        
        /* Alternates column - equal width with other content columns */
        .destinations-table table th:nth-child(3), 
        .destinations-table table td:nth-child(3) {
            width: 400px !important;
            min-width: 400px !important;
        }
        
        /* Region column - 10 character width */
        .enroute-table table th:nth-child(1), 
        .enroute-table table td:nth-child(1) {
            width: 80px !important;
            min-width: 80px !important;
            max-width: 80px !important;
        }
        
        /* EDTO ERAs column - equal width with other content columns */
        .enroute-table table th:nth-child(2), 
        .enroute-table table td:nth-child(2) {
            width: 400px !important;
            min-width: 400px !important;
        }

        /* New: separate multiple TAF blocks inside a single table cell */
        .taf-block {
            border-bottom: 1px dotted rgba(0,0,0,0.12);
            padding-bottom: 8px;
            margin-bottom: 8px;
        }
        .taf-block:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .taf-block .airport-label {
            display: inline-block;
            width: 56px;
            font-weight: 600;
            margin-right: 6px;
        }
        
        /* NOTAM Console Styles */
        .notam-console-container {
            background-color: #fcfcfc;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        .notam-card {
            background-color: white;
            border-left: 5px solid #17a2b8;
            margin-bottom: 12px;
            padding: 10px 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-family: 'Courier New', Courier, monospace;
        }
        .notam-card-rwy {
            border-left-color: #ffc107;
            background-color: #fffbef;
        }
        .notam-id-badge {
            background-color: #6c757d;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 8px;
        }
        .notam-critical {
            background-color: #ffcccc;
            color: #b30000;
            font-weight: bold;
            padding: 0 2px;
        }
        .notam-rwy {
            color: #d94100;
            font-weight: bold;
            text-decoration: underline;
        }
        .notam-search {
            background-color: #cce5ff;
            color: #004085;
            font-weight: bold;
            padding: 0 2px;
        }
    </style>
    """

def process_destinations_data(filtered_airport_data, airport_data, show_all_airports):
    """Process destinations and alternates TAF data with Batch Fetching"""
    rows = []
    
    # BATCH FETCHING: Collect ALL unique airport IDs first
    all_needed_airports = set()
    for dest, alternates in filtered_airport_data.items():
        all_needed_airports.add(dest)
        for alt in alternates:
            all_needed_airports.add(alt)
    
    # Single API call for the entire region!
    with st.spinner(f"Fetching TAF for {len(all_needed_airports)} airports..."):
        taf_info_lines = fetch_taf(list(all_needed_airports))
        taf_dict = parse_taf_data(taf_info_lines)
    
    for dest, alternates in filtered_airport_data.items():
        # Destination highlighted
        raw_dest_taf = taf_dict.get(dest, 'No data available')
        highlighted_dest_taf = highlight_taf(raw_dest_taf)
        
        # Build alternates content
        alternates_blocks = []
        for alt in alternates:
            alt_taf_raw = taf_dict.get(alt, 'No data available')
            alt_highlighted = highlight_taf(alt_taf_raw)
            # Only include if show_all_airports or highlighted content exists
            if show_all_airports or '<span' in alt_highlighted:
                # Optimized: Make the airport label itself a link to trigger NOTAM
                notam_btn = f'<a href="/?notam={alt}" target="_self" style="text-decoration: none; color: #17a2b8; font-weight: bold;">{alt}</a>'
                alternates_blocks.append(
                    f'<div class="taf-block"><span class="airport-label">{notam_btn}:</span> {alt_highlighted}</div>'
                )
        
        # Only include the row if destination meets condition or any alternate blocks to show
        if show_all_airports or '<span' in highlighted_dest_taf or alternates_blocks:
            row = {
                "Airport": dest,
                "Destinations": f'<div class="taf-block">{highlighted_dest_taf}</div>',
                "Alternates": ''.join(alternates_blocks) if alternates_blocks else '<div class="taf-block">No data available</div>'
            }
            rows.append(row)
    
    return rows


def process_enroute_data(selected_region, enroute_data, show_all_airports):
    """Process enroute alternates TAF data with Batch Fetching"""
    enroute_rows = []
    
    # BATCH FETCHING: Collect all airports for all selected regions
    all_needed_airports = set()
    regions_to_process = []
    if selected_region == "ALL":
        regions_to_process = list(enroute_data.keys())
    elif selected_region in enroute_data:
        regions_to_process = [selected_region]
        
    for region in regions_to_process:
        for airport in enroute_data[region]:
            all_needed_airports.add(airport)
            
    if not all_needed_airports:
        return []

    # Single API call for enroute data!
    with st.spinner(f"Fetching enroute TAF for {len(all_needed_airports)} airports..."):
        enroute_taf_lines = fetch_taf(list(all_needed_airports))
        enroute_taf_dict = parse_taf_data(enroute_taf_lines)

    for region_name in regions_to_process:
        airports = enroute_data[region_name]
        collected_tafs = []
        for airport in airports:
            taf_text = enroute_taf_dict.get(airport, 'No data available')
            highlighted_taf = highlight_taf(taf_text)
            if show_all_airports or '<span' in highlighted_taf:
                # Optimized: Make the airport label itself a link to trigger NOTAM
                notam_btn = f'<a href="/?notam={airport}" target="_self" style="text-decoration: none; color: #28a745; font-weight: bold;">{airport}</a>'
                collected_tafs.append(f'<div class="taf-block"><span class="airport-label">{notam_btn}:</span> {highlighted_taf}</div>')
        
        if collected_tafs:
            enroute_rows.append({"Region": region_name, "EDTO ERAs": ''.join(collected_tafs)})
    
    return enroute_rows



def display_tables(rows, enroute_rows, show_all_airports):
    """Display the TAF data tables side by side"""
    if rows or enroute_rows:
        st.markdown(get_bootstrap_css(), unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if rows:
                df = pd.DataFrame(rows)
                # Custom HTML with fixed column widths
                html_table = '<table class="table table-striped table-sm" style="table-layout: fixed; width: 100%;">'
                html_table += '<thead><tr>'
                html_table += '<th style="width: 60px; background-color: #007BFF; color: white; text-align: center;">Airport</th>'
                html_table += '<th style="width: 400px; background-color: #007BFF; color: white; text-align: center;">Destinations</th>'
                html_table += '<th style="width: 400px; background-color: #007BFF; color: white; text-align: center;">Alternates</th>'
                html_table += '</tr></thead><tbody>'
                
                for _, row in df.iterrows():
                    airport = row["Airport"]
                    # Simplified link: Since NOTAM is now at the top, just triggering the refresh is enough
                    notam_link = f'<a href="/?notam={airport}" target="_self" style="text-decoration: none; color: white; background: #17a2b8; padding: 2px 5px; border-radius: 3px; font-size: 10px; font-weight: bold;">NOTAM</a>'
                    
                    html_table += '<tr>'
                    html_table += f'<td style="width: 60px; padding: 6px 4px; vertical-align: top;">{airport}<br>{notam_link}</td>'
                    html_table += f'<td style="width: 400px; padding: 6px 4px; vertical-align: top; word-wrap: break-word;">{row["Destinations"]}</td>'
                    html_table += f'<td style="width: 400px; padding: 6px 4px; vertical-align: top; word-wrap: break-word;">{row["Alternates"]}</td>'
                    html_table += '</tr>'
                
                html_table += '</tbody></table>'
                
                st.markdown('<div class="destinations-table table-container">', unsafe_allow_html=True)
                st.markdown(html_table, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                if show_all_airports:
                    st.write("No airports found for the selected region.")
                else:
                    st.write("No significant weather for all relevant airports.")
        
        with col2:
            if enroute_rows:
                enroute_df = pd.DataFrame(enroute_rows)
                # Custom HTML with fixed column widths
                html_table = '<table class="table table-striped table-sm" style="table-layout: fixed; width: 100%;">'
                html_table += '<thead><tr>'
                html_table += '<th style="width: 80px; background-color: #28a745; color: white; text-align: center;">Region</th>'
                html_table += '<th style="width: 400px; background-color: #28a745; color: white; text-align: center;">EDTO ERAs</th>'
                html_table += '</tr></thead><tbody>'
                
                for _, row in enroute_df.iterrows():
                    region = row["Region"]
                    html_table += '<tr>'
                    html_table += f'<td style="width: 80px; padding: 6px 4px; vertical-align: top;">{region}</td>'
                    html_table += f'<td style="width: 400px; padding: 6px 4px; vertical-align: top; word-wrap: break-word;">{row["EDTO ERAs"]}</td>'
                    html_table += '</tr>'
                
                html_table += '</tbody></table>'
                
                st.markdown('<div class="enroute-table table-container">', unsafe_allow_html=True)
                st.markdown(html_table, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                if show_all_airports:
                    st.write("No enroute alternates found for the selected region.")
                else:
                    st.write("No significant weather conditions found in enroute alternates for the selected region.")
    else:
        st.write("No data available for the selected region.")
