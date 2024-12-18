import streamlit as st
import pandas as pd
import requests
import re
import time
from datetime import datetime

# Set the page config to wide mode
st.set_page_config(layout="wide")

# Timer for auto-refresh
if 'last_run' not in st.session_state:
    st.session_state.last_run = time.time()
    st.session_state.last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S HKT")

# Refresh every 60 seconds (1 minute)
if time.time() - st.session_state.last_run > 60:
    st.session_state.last_run = time.time()
    st.session_state.last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S HKT")
#    st.experimental_rerun()

def fetch_taf(airport_ids):
    url = f"https://aviationweather.gov/api/data/taf?ids={','.join(airport_ids)}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip().splitlines()
    else:
        st.error("Error fetching TAF data.")
        return []

def parse_taf_data(taf_lines):
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
    taf_text = taf_text.replace('\n', '<br>')
    visibility_pattern = r'(?<=\s)(\d{4})(?=\s|<br>)'
    cloud_ceiling_pattern = r'(?<!\S)\b(BKN|OVC)(\d{3})\b(?=\s|<br>)'
   # unmeasured_visibility_pattern = r'(?<!\S)\bVV///\b(?=\s|<br>)'
    unmeasured_visibility_pattern = r'(?<!\S)(VV///)(?=\s|<br>)'  # Simplified capturing group
    freezing_conditions_pattern = r'(?<!\S)([-+]?FZ(?:DZ|RA))(?=\s|<br>)'

    def highlight_visibility(match):
        visibility = match.group(0)
        return f"<span style='color: red; font-weight: bold;'>{visibility}</span>" if int(visibility) < 3000 else visibility

    def highlight_cloud_ceiling(match):
        cloud_type = match.group(1)  # BKN or OVC
        height = int(match.group(2)) * 100  # Convert 3-digit height to feet
        return f"<span style='color: pink; font-weight: bold;'>{cloud_type}{match.group(2)}</span>" if height < 1000 else match.group(0)

    def highlight_unmeasured_visibility(match):
        return "<span style='color: purple; font-weight: bold;'>VV///</span>"

    def highlight_freezing_conditions(match):
        return f"<span style='color: blue; font-weight: bold;'>{match.group(0)}</span>"

    highlighted_taf = re.sub(visibility_pattern, highlight_visibility, taf_text)
    highlighted_taf = re.sub(cloud_ceiling_pattern, highlight_cloud_ceiling, highlighted_taf)
    highlighted_taf = re.sub(unmeasured_visibility_pattern, highlight_unmeasured_visibility, highlighted_taf)
    highlighted_taf = re.sub(freezing_conditions_pattern, highlight_freezing_conditions, highlighted_taf)

    return highlighted_taf

def load_region_data(file_path):
    region_dict = {}
    try:
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                line = line.strip()
                if line:
                    region, airports = line.split(',', 1)
                    region_dict[region.strip()] = [airport.strip() for airport in airports.split('|')]
    except FileNotFoundError:
        st.error(f"Region configuration file not found: {file_path}")
    return region_dict

def main():
    st.title("TAF Information Dashboard")

    # Load region data
    region_file_path = "./Region.txt"  # Adjust this path as needed
    region_data = load_region_data(region_file_path)

    # Add "ALL" option to the sidebar selection
    region_options = list(region_data.keys()) + ["ALL"]
    selected_region = st.sidebar.selectbox("Select Region", options=region_options)

    # Manual refresh button
    if st.sidebar.button("Refresh Now"):
        st.session_state.last_run = time.time()
        st.session_state.last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S HKT")
        st.experimental_rerun()

    # Load airport data
    input_file_path = "./Airport_list.txt"  # Adjust this path as needed
    airport_data = {}
    try:
        with open(input_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("airport"):
                    dest, alternates = line.split(',')
                    airport_data[dest.strip()] = [alt.strip() for alt in alternates.split('|')]
    except FileNotFoundError:
        st.error(f"Input file not found: {input_file_path}")
        return

    # Determine relevant airports based on the selected region
    if selected_region == "ALL":
        relevant_airports = set()
        for airports in region_data.values():
            relevant_airports.update(airports)
    else:
        relevant_airports = region_data[selected_region]

    # Filter airport data based on relevant airports
    filtered_airport_data = {dest: alternates for dest, alternates in airport_data.items() if dest in relevant_airports}

    taf_data = {}
    for dest, alternates in filtered_airport_data.items():
        all_airports = [dest] + alternates
        taf_info_lines = fetch_taf(all_airports)
        taf_dict = parse_taf_data(taf_info_lines)
        
        taf_data[dest] = {airport: taf_dict.get(airport, 'No data available') for airport in all_airports}

    # Create a DataFrame for the TAF data
    rows = []
    for dest, taf_info in taf_data.items():
        highlighted_dest_taf = highlight_taf(taf_info[dest])
        
        if '<span' in highlighted_dest_taf:
            row = {
                "Airport Code": dest,
                "Destination TAF": highlighted_dest_taf
            }
            alternates_taf = "<br><br>".join(highlight_taf(taf_info[alt]) for alt in airport_data[dest])
            row["Alternate TAFs"] = alternates_taf
            rows.append(row)

    if rows:
        df = pd.DataFrame(rows)

        # Convert DataFrame to HTML
        html_content = df.to_html(escape=False, index=False)

        # Set fixed widths in the HTML
        html_content = html_content.replace('<table border="1" class="dataframe">',
                                             '<table border="1" class="dataframe" style="table-layout: fixed; width: 100%;">')
        html_content = html_content.replace('<th>Airport Code</th>',
                                             '<th style="width: 8ch;">Airport Code</th>')
        html_content = html_content.replace('<th>Destination TAF</th>',
                                             '<th style="width: 55ch;">Destination TAF</th>')
        html_content = html_content.replace('<th>Alternate TAFs</th>',
                                             '<th style="width: 55ch;">Alternate TAFs</th>')

        # Display the HTML table
        st.markdown(html_content, unsafe_allow_html=True)
    else:
        st.write("Good weather for all relevant airports.")

    # Display the last update time in HKT
    st.sidebar.write(f"Last Updated: {st.session_state.last_update_time} (HKT)")

if __name__ == "__main__":
    main()
