# TAF Information Dashboard ✈️

A high-performance Streamlit-based aviation weather monitoring dashboard for Terminal Aerodrome Forecast (TAF) data. Optimized for 1920x1080 displays with side-by-side layout for destinations and EDTO ERAs.

## ✨ Features

- 🚀 **Direct Access**: No password authentication - instant access
- 🔄 **Auto-refresh**: Updates every 10 minutes automatically  
- 🗺️ **Region Filtering**: Filter airports by geographic regions or view all
- 📊 **Side-by-Side Layout**: Destinations & alternates | EDTO ERAs
- 🎨 **Advanced Weather Highlighting**: Real-time color-coded conditions
  - 🔴 **Red**: Low visibility (<3000m)
  - 🩷 **Pink**: Low cloud ceiling (<1000ft) 
  - 🟣 **Purple**: Unmeasured visibility (VV///)
  - 🔵 **Blue**: Freezing conditions (FZRA, FZDZ)
  - 🟢 **Green/Blue**: Snow conditions
- 📱 **Responsive Design**: Optimized for wide monitors with compact controls
- ⚡ **Performance**: Efficient API calls and data processing

## 🚀 Quick Start

### Simple Launch (Recommended)
```bash
./start.sh
```

### Manual Start
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application  
streamlit run main.py
```

## 🌐 Access the Application

- **Local Access**: http://localhost:8502
- **Network Access**: http://[your-ip]:8502

## 📋 Requirements

- **Python**: 3.7+ (tested with Python 3.13)
- **Internet**: Active connection for TAF data fetching
- **Display**: Optimized for 1920x1080 (16:9) monitors
- **Required Files**:
  - `Region.txt` - Region to airports mapping
  - `Airport_list.txt` - Destinations to alternates mapping  
  - `Enroute_Alternates.txt` - EDTO ERA by region

## ⚙️ Project Structure

```
checkTAF/
├── main.py                    # Main Streamlit application
├── taf_functions.py          # Core TAF processing functions
├── start.sh                  # Launch script
├── requirements.txt          # Python dependencies
├── Region.txt               # Region configurations
├── Airport_list.txt         # Airport mappings
├── Enroute_Alternates.txt   # EDTO ERAs by region
└── venv/                    # Virtual environment
```

## 🛠️ Installation

### Automatic Setup
The `start.sh` script handles everything automatically:
1. Activates the virtual environment
2. Launches the application on port 8502
3. Provides access information

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run main.py --server.port=8502
```

## 📁 Configuration Files

### Region.txt Format
```
region_name,AIRPORT1|AIRPORT2|AIRPORT3
```

### Airport_list.txt Format  
```
DEST_AIRPORT,ALTERNATE1|ALTERNATE2|ALTERNATE3
```

### Enroute_Alternates.txt Format
```
region_name,ERA1|ERA2|ERA3
```

## 🎛️ User Interface

### Top Controls (Horizontal Layout)
- **🌍 Region Filter**: Select specific region or "ALL"
- **📋 Show All Toggle**: View all airports vs. significant weather only
- **🔄 Refresh Button**: Manual data refresh
- **⏰ Current Time**: Live timestamp display

### Main Display (Side-by-Side)
- **Left Panel**: Destinations and their alternates
- **Right Panel**: EDTO ERAs by region
- **Responsive Tables**: Fixed column widths, scrollable content

## 🔧 Troubleshooting

### Permission Issues
```bash
chmod +x start.sh
```

### Missing Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Data Files Missing
Ensure all `.txt` configuration files are present:
- `Region.txt`
- `Airport_list.txt` 
- `Enroute_Alternates.txt`

### Port Conflicts
Default port is 8502. To use a different port:
```bash
streamlit run main.py --server.port=8503
```

### Virtual Environment Issues
If `venv` folder is missing:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🛑 Stopping the Application

- Press `Ctrl+C` in the terminal
- Or close the terminal window

## 🚀 Technical Features

- **Modular Architecture**: Separated UI (`main.py`) and logic (`taf_functions.py`)
- **API Integration**: Real-time data from aviationweather.gov
- **Custom HTML Tables**: Fixed-width columns with Bootstrap styling
- **Performance Optimized**: Efficient data processing and rendering
- **Regex-based Highlighting**: Advanced weather pattern recognition
- **Auto-refresh**: Configurable 10-minute intervals

## 🏗️ Architecture Overview

### Code Organization
- **`main.py`**: Streamlit UI layer with compact styling and horizontal controls
- **`taf_functions.py`**: Core business logic for TAF processing and display
- **Modular Functions**: Separated concerns for data loading, processing, and rendering

### Key Optimizations
- **Space Efficiency**: Reduced header padding, maximized table area (80vh)
- **Fixed Column Widths**: Precise alignment across both tables
- **Custom HTML Generation**: Bootstrap integration with inline styles
- **Performance**: Efficient API calls and regex-based weather highlighting

### Display Layout (1920x1080 Optimized)
```
┌─────────────────────────────────────────────────────────────────┐
│ TAF Information Dashboard                                        │
│ [Region ▼] [☐ Show All] [🔄 Refresh] [⏰ Time]                  │
├─────────────────────────────────┬───────────────────────────────┤
│ Destinations & Alternates       │ EDTO ERAs                     │
│ ┌─────┬─────────┬─────────┐     │ ┌────────┬─────────────────┐  │
│ │Code │Dest TAF │Alt TAFs │     │ │Region  │EDTO ERA TAFs    │  │
│ └─────┴─────────┴─────────┘     │ └────────┴─────────────────┘  │
│            (80vh)               │           (80vh)              │
└─────────────────────────────────┴───────────────────────────────┘
```

## 📞 Support

- Check terminal output for detailed error messages
- Ensure internet connectivity for TAF data fetching
- Verify all configuration files are properly formatted
- See `SIMPLE_GUIDE.md` for basic usage instructions
