# TAF Dashboard - Simple Guide

## 🚀 How to Run the Application

**Just run this single command:**

```bash
./start.sh
```

That's it! The application will start automatically.

## 🌐 How to Access

After running `./start.sh`, open your web browser and go to:
- **http://localhost:8501**

## 🛑 How to Stop

Press `Ctrl + C` in the terminal where you ran the script.

## 📝 What This Application Does

- Shows aviation weather forecasts (TAF) for airports
- Highlights bad weather conditions in colors:
  - **Red**: Low visibility (dangerous for flying)
  - **Pink**: Low clouds (dangerous for flying) 
  - **Blue**: Freezing conditions
  - **Purple**: Can't measure visibility
  - **Green/Blue**: Snow

## 🎛️ How to Use

1. **Select Region**: Choose which area's airports to see
2. **Show All Airports**: Check this to see all airports, uncheck to see only bad weather
3. **Refresh**: Click to get latest weather data
4. The app automatically refreshes every 10 minutes

## 📁 Files You Need

These files must be in the same folder:
- `start.sh` - The script to start the app
- `main.py` - The main application
- `taf_functions.py` - The weather processing code
- `Region.txt` - List of regions and airports
- `Airport_list.txt` - Destinations and their alternate airports
- `Enroute_Alternates.txt` - Emergency airports by region

## 🆘 If Something Goes Wrong

1. Make sure you're in the right folder: `/Users/sunnywslau/Code/checkTAF`
2. Make sure the script can run: `chmod +x start.sh`
3. Check all the required files are present
4. Try running `./start.sh` again

That's all you need to know! Keep it simple. 🎯
