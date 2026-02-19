"""
TAF Information Dashboard - Main Application
Aviation weather monitoring dashboard for airports and EDTO ERAs
"""

import streamlit as st
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from taf_functions import (
    load_region_data, load_airport_data, load_enroute_alternates,
    process_destinations_data, process_enroute_data, display_tables,
    highlight_notam_text
)
from faa_notam_lib import FAAClient
import os
import time

# Set the page config to wide mode
st.set_page_config(layout="wide", page_title="TAF Information Dashboard", page_icon="✈️")

# Auto-refresh logic moved to bottom of main() to avoid top-padding issues


def create_controls(region_data):
    """Create the top horizontal control bar"""
    col_control1, col_control2, col_control3, col_control4 = st.columns([2, 2, 2, 1])
    
    with col_control1:
        region_options = list(region_data.keys()) + ["ALL"]
        selected_region = st.selectbox("🌍 Select Region", options=region_options)
    
    with col_control2:
        show_all_airports = st.checkbox("📋 Show All Airports", value=False, help="Check to show all airports, uncheck to show only airports with significant weather")
    
    with col_control3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    with col_control4:
        st.write(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    
    return selected_region, show_all_airports


def get_filtered_airports(selected_region, region_data, airport_data):
    """Get filtered airport data based on selected region"""
    if selected_region == "ALL":
        relevant_airports = set()
        for airports in region_data.values():
            relevant_airports.update(airports)
    else:
        relevant_airports = region_data[selected_region]
    
    return {dest: alternates for dest, alternates in airport_data.items() if dest in relevant_airports}


def main():
    """Main application function"""
    # Compact header with reduced spacing
    st.markdown("""
    <style>
        /* Modern UI: Strip all top padding/headers for absolute compactness */
        [data-testid="stHeader"] {
            display: none;
        }
        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 1rem;
        }
        /* Target the auto-refresh container to ensure it stays invisible and zero-height */
        iframe[title="streamlit_autorefresh.st_autorefresh"] {
            display: none;
        }
        div[data-testid="stVerticalBlock"] > div:has(iframe[title="streamlit_autorefresh.st_autorefresh"]) {
            display: none;
            height: 0;
            margin: 0;
            padding: 0;
        }
        h1 {
            margin-top: 0rem !important;
            margin-bottom: 0.5rem !important;
            font-size: 2rem !important;
        }
        .stSelectbox, .stCheckbox {
            margin-bottom: 0.25rem !important;
        }
    </style>
    <h1>TAF Information Dashboard</h1>
    """, unsafe_allow_html=True)
    
    # --- NOTAM Initialization & URL Sync ---
    if "notam_client" not in st.session_state:
        client_id = st.secrets.get("FAA_CLIENT_ID")
        client_secret = st.secrets.get("FAA_CLIENT_SECRET")
        st.session_state.notam_client = FAAClient(client_id, client_secret)
    
    # Sync URL param to Session State only if param exists
    # If param is missing, it means user closed it or hasn't opened any
    if "notam" in st.query_params:
        st.session_state.selected_airport = st.query_params["notam"]
    else:
        # If not in URL, ensure it's cleared from session state to avoid ghost consoles
        st.session_state.selected_airport = None
    # ----------------------------------------

    # Load configuration data
    region_data = load_region_data("./Region.txt")
    airport_data = load_airport_data("./Airport_list.txt")
    enroute_data = load_enroute_alternates("./Enroute_Alternates.txt")
    
    # Create controls and get user selections
    selected_region, show_all_airports = create_controls(region_data)
    
    # --- Control Change Detection & State Cleanup ---
    # Track both region and "Show All" toggle to clear NOTAM console on any view change
    if "last_controls" not in st.session_state:
        st.session_state.last_controls = (selected_region, show_all_airports)
    
    if st.session_state.last_controls != (selected_region, show_all_airports):
        # Control changed, wipe any persistent NOTAM param to keep UI clean
        st.query_params.clear()
        st.session_state.selected_airport = None
        st.session_state.last_controls = (selected_region, show_all_airports)
        st.rerun()

    # Filter airports based on selected region
    filtered_airport_data = get_filtered_airports(selected_region, region_data, airport_data)
    
    # --- NOTAM Hero Console (Top Position for Reliability) ---
    # Moved here so it's immediately visible without scrolling/jumping
    if st.session_state.selected_airport:
        render_notam_console(st.session_state.selected_airport)
        st.divider()

    # Process TAF data
    destinations_rows = process_destinations_data(filtered_airport_data, airport_data, show_all_airports)
    enroute_rows = process_enroute_data(selected_region, enroute_data, show_all_airports)
    
    # Display TAF tables
    display_tables(destinations_rows, enroute_rows, show_all_airports)

def render_notam_console(airport_code):
    """Render NOTAM information in a high-visibility hero section"""
    # COMPACT HEADER (One Row)
    # Merging Title, Search, and Close into one row to save vertical space
    col_title, col_search, col_close = st.columns([3, 5, 2])
    
    with col_title:
        st.markdown(f"#### 📑 Console: {airport_code}")
    
    with col_search:
        # Simplified: Keyword only, no search mode dropdown
        query = st.text_input("", placeholder="Search NOTAMs (e.g. RWY, ILS, BTN)...", key="notam_search", label_visibility="collapsed")
    
    with col_close:
        if st.button("❌ Close", use_container_width=True, type="primary"):
            st.session_state.selected_airport = None
            st.query_params.clear()
            st.rerun()

    try:
        with st.spinner(f"Scanning FAA Data Feed for {airport_code}..."):
            # Fetch data (Live or Mock)
            if not st.session_state.notam_client.client_id or st.session_state.notam_client.client_id == "YOUR_CLIENT_ID":
                # Enhanced Mock with pro-format
                notams = [
                    {
                        "id": "W0164/26 NOTAMN", 
                        "status": "Active", "start": "2602231700", "end": "2603302200", 
                        "text": "RWY08L/26R CLSD DUE TO MAINT.",
                        "full_icao": "GEOJSON",
                        "q_line": "Q) ZWUQ/QMRLC/IV/NBO/A/000/999/4354N08728E005",
                        "location": airport_code,
                        "schedule": "1700-2200 EVERY MON"
                    },
                    {
                        "id": "A1234/26 NOTAMR", 
                        "status": "Active", "start": "2602190800", "end": "2602192000", 
                        "text": "ILS RWY 25L U/S.",
                        "full_icao": "GEOJSON",
                        "q_line": f"Q) {airport_code[:2]}/QILAS/IV/NBO/A/000/999/...",
                        "location": airport_code,
                        "schedule": ""
                    }
                ]
                time.sleep(0.3)
            else:
                # Simplified search call (keyword only)
                notams = st.session_state.notam_client.search_notams(
                    location=airport_code, 
                    query=query
                )

        if not notams:
            st.info(f"No active NOTAMs found for {airport_code} matching your criteria.")
            return

        # REFINED PRIORITY & RUNWAY DETECTION
        import re
        def get_notam_metrics(n):
            text = n['text'].upper()
            # Broadened regex: match RWY even if followed by numbers (e.g., RWY08L)
            is_rwy = bool(re.search(r'\b(RWY|RUNWAY)', text))
            is_crit = any(x in text for x in ["CLOSED", "CLSD", "U/S", "UNSERVICEABLE"])
            
            # Priority Score (Lower is higher)
            if is_rwy: return 0, is_rwy # Tier 0: Runways
            if is_crit: return 1, is_rwy # Tier 1: Other Critical items
            return 2, is_rwy             # Tier 2: Others

        sorted_notams = sorted(notams, key=lambda x: get_notam_metrics(x)[0])

        st.markdown(f"**Showing {len(sorted_notams)} NOTAMs** (3-Column Power Layout)")
        
        # 3-COLUMN TABLE IMPLEMENTATION
        # Group notams into chunks of 3
        cols_per_row = 3
        notam_groups = [sorted_notams[i:i + cols_per_row] for i in range(0, len(sorted_notams), cols_per_row)]
        
        # Build Bootstrap Table
        html_table = '<div class="notam-table-container" style="overflow-x: auto;">'
        html_table += '<table class="table table-bordered table-sm" style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 11px;">'
        html_table += '<tbody>'
        
        for group in notam_groups:
            html_table += '<tr>'
            for n in group:
                score, is_rwy = get_notam_metrics(n)
                bg_color = "#fffaf0" if is_rwy else "#ffffff"
                border_left = "4px solid #f0ad4e" if is_rwy else "1px solid #dee2e6"
                
                # ICAO Lines
                q_line = n.get('q_line', f"Q) {n.get('location', 'XXXX')}/XXXXX/IV/NBO/A/000/999/...")
                a_line = f"A) {n['location']}"
                b_line = f"B) {n['start']}"
                c_line = f"C) {n['end']}"
                d_line = f"D) {n['schedule']}" if n.get('schedule') else ""
                # Replace actual newlines in text with <br> for HTML rendering
                e_content = n['text'].replace('\n', '<br>')
                
                html_table += f'''<td style="width: 33.33%; padding: 10px; vertical-align: top; background-color: {bg_color}; border-left: {border_left}; border-top: 1px solid #dee2e6; font-family: monospace !important; font-size: 11px !important; line-height: 1.4 !important; color: #333;">
<div style="font-weight: bold; color: #007bff; margin-bottom: 4px;">{n['id']} {'<span style="color:#d9534f">[RWY]</span>' if is_rwy else ''}</div>
{q_line}<br>
{a_line} {b_line} {c_line}<br>
{f"{d_line}<br>" if d_line else ""}
<div style="margin-top: 5px;">E) {e_content}</div>
</td>'''
            
            # Fill remaining cells if row is not full
            for _ in range(cols_per_row - len(group)):
                html_table += '<td style="width: 33.33%; border: none;"></td>'
                
            html_table += '</tr>'
            
        html_table += '</tbody></table></div>'
        
        st.markdown(html_table, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ FAA Data Feed Unreachable: {str(e)}")

    # FINAL PIECE: Auto-refresh moved to bottom to prevent top spacing issues
    st_autorefresh(interval=600000, limit=3000, key="FinalRefreshCounter")


if __name__ == "__main__":
    main()
