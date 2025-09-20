#!/bin/bash

# Simple TAF Dashboard Launcher
echo "🛩️ Starting TAF Information Dashboard..."

# Navigate to the project folder
cd /Users/sunnywslau/Code/checkTAF

# Activate virtual environment
source venv/bin/activate

# Show access information
echo "📍 Opening in browser at: http://localhost:8502"
echo "🔄 Auto-refresh every 10 minutes"  
echo "⛔ Press Ctrl+C to stop"
echo ""

# Run Streamlit application on port 8502
streamlit run main.py --server.port=8502
