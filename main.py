"""
TAF Information Dashboard - Main Application
Aviation weather monitoring dashboard for airports and EDTO ERAs
"""

import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from taf_functions import (
    load_region_data, load_airport_data, load_enroute_alternates,
    process_destinations_data, process_enroute_data, display_tables
)

# Set the page config to wide mode
st.set_page_config(layout="wide", page_title="TAF Information Dashboard", page_icon="✈️")

# Auto-refresh every 10 minutes
count = st_autorefresh(interval=600000, limit=3000, key="MySunnylcounter")


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
        .main > div:first-child {
            padding-top: 1rem;
        }
        .stApp > header {
            height: 0px;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        h1 {
            margin-bottom: 0.5rem !important;
            font-size: 2rem !important;
        }
        .stSelectbox, .stCheckbox {
            margin-bottom: 0.25rem !important;
        }
    </style>
    <h1>TAF Information Dashboard</h1>
    """, unsafe_allow_html=True)
    
    # Load configuration data
    region_data = load_region_data("./Region.txt")
    airport_data = load_airport_data("./Airport_list.txt")
    enroute_data = load_enroute_alternates("./Enroute_Alternates.txt")
    
    # Create controls and get user selections
    selected_region, show_all_airports = create_controls(region_data)
    
    # Filter airports based on selected region
    filtered_airport_data = get_filtered_airports(selected_region, region_data, airport_data)
    
    # Process data
    destinations_rows = process_destinations_data(filtered_airport_data, airport_data, show_all_airports)
    enroute_rows = process_enroute_data(selected_region, enroute_data, show_all_airports)
    
    # Display tables
    display_tables(destinations_rows, enroute_rows, show_all_airports)


if __name__ == "__main__":
    main()
