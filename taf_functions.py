"""
TAF Functions Module
Contains all the core functionality for the TAF Information Dashboard
"""

import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime


def fetch_taf(airport_ids):
    """Fetch TAF data from aviationweather.gov API"""
    url = f"https://aviationweather.gov/api/data/taf?ids={','.join(airport_ids)}"
    with st.spinner("Fetching TAF data..."):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip().splitlines()
        else:
            st.error("Error fetching TAF data.")
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
    """Highlight weather conditions in TAF text"""
    taf_text = taf_text.replace('\n', '<br>')
    
    # Define regex patterns for weather conditions
    visibility_pattern = r'(?<=\s)(\d{4})(?=\s|<br>|$)'
    cloud_ceiling_pattern = r'(?<!\S)\b(BKN|OVC)(\d{3})\b(?=\s|<br>|$)'
    unmeasured_visibility_pattern = r'(?<!\S)(VV///|VV\d{3}?)(?=\s|<br>|$)'
    freezing_conditions_pattern = r'(?<!\S)([-+]?FZ(?:DZ|RA))(?=\s|<br>|$)'
    snow_pattern = r'(?<!\S)(SN)(?=\s|<br>|$)'

    def highlight_visibility(match):
        visibility = match.group(0)
        visibility_meters = int(visibility)
        return f"<span style='color: red; font-weight: bold;'>{visibility}</span>" if visibility_meters < 3000 else visibility

    def highlight_cloud_ceiling(match):
        cloud_type = match.group(1)
        height = int(match.group(2)) * 100
        return f"<span style='color: pink; font-weight: bold;'>{cloud_type}{match.group(2)}</span>" if height < 1000 else match.group(0)

    def highlight_unmeasured_visibility(match):
        return f"<span style='color: purple; font-weight: bold;'>{match.group(0)}</span>"

    def highlight_freezing_conditions(match):
        return f"<span style='color: blue; font-weight: bold;'>{match.group(0)}</span>"

    def highlight_snow(match):
        return f"<span style='color: green; background-color: blue; font-weight: bold;'>{match.group(0)}</span>"

    # Apply highlighting
    highlighted_taf = re.sub(visibility_pattern, highlight_visibility, taf_text)
    highlighted_taf = re.sub(cloud_ceiling_pattern, highlight_cloud_ceiling, highlighted_taf)
    highlighted_taf = re.sub(unmeasured_visibility_pattern, highlight_unmeasured_visibility, highlighted_taf)
    highlighted_taf = re.sub(freezing_conditions_pattern, highlight_freezing_conditions, highlighted_taf)
    highlighted_taf = re.sub(snow_pattern, highlight_snow, highlighted_taf)

    return highlighted_taf


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
    </style>
    """


def process_destinations_data(filtered_airport_data, airport_data, show_all_airports):
    """Process destinations and alternates TAF data"""
    taf_data = {}
    rows = []
    
    for dest, alternates in filtered_airport_data.items():
        all_airports = [dest] + alternates
        taf_info_lines = fetch_taf(all_airports)
        taf_dict = parse_taf_data(taf_info_lines)
        taf_data[dest] = {airport: taf_dict.get(airport, 'No data available') for airport in all_airports}
    
    for dest, taf_info in taf_data.items():
        highlighted_dest_taf = highlight_taf(taf_info[dest])
        
        if show_all_airports or '<span' in highlighted_dest_taf:
            row = {
                "Airport": dest,
                "Destinations": highlighted_dest_taf,
                "Alternates": "<br><br>".join(highlight_taf(taf_info[alt]) for alt in airport_data[dest])
            }
            rows.append(row)
    
    return rows


def process_enroute_data(selected_region, enroute_data, show_all_airports):
    """Process enroute alternates TAF data"""
    enroute_rows = []
    
    if selected_region == "ALL":
        for region, airports in enroute_data.items():
            if airports:
                enroute_taf_lines = fetch_taf(airports)
                enroute_taf_dict = parse_taf_data(enroute_taf_lines)
                
                collected_tafs = []
                for airport in airports:
                    taf_text = enroute_taf_dict.get(airport, 'No data available')
                    highlighted_taf = highlight_taf(taf_text)
                    if show_all_airports or '<span' in highlighted_taf:
                        collected_tafs.append(f"{airport}: {highlighted_taf}")
                
                if collected_tafs:
                    enroute_rows.append({
                        "Region": region,
                        "EDTO ERAs": "<br><br>".join(collected_tafs)
                    })
    else:
        if selected_region in enroute_data:
            airports = enroute_data[selected_region]
            if airports:
                enroute_taf_lines = fetch_taf(airports)
                enroute_taf_dict = parse_taf_data(enroute_taf_lines)
                
                collected_tafs = []
                for airport in airports:
                    taf_text = enroute_taf_dict.get(airport, 'No data available')
                    highlighted_taf = highlight_taf(taf_text)
                    if show_all_airports or '<span' in highlighted_taf:
                        collected_tafs.append(f"{airport}: {highlighted_taf}")
                
                if collected_tafs:
                    enroute_rows.append({
                        "Region": selected_region,
                        "EDTO ERAs": "<br><br>".join(collected_tafs)
                    })
    
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
                    html_table += '<tr>'
                    html_table += f'<td style="width: 60px; padding: 6px 4px; vertical-align: top;">{row["Airport"]}</td>'
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
                    html_table += '<tr>'
                    html_table += f'<td style="width: 80px; padding: 6px 4px; vertical-align: top;">{row["Region"]}</td>'
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
