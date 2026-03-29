#!/bin/bash

# Simple TAF Dashboard Launcher
echo "🛩️ Starting TAF Information Dashboard..."

# Navigate to the project folder relative to script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ Warning: venv folder not found. Please run 'python3 -m venv venv' and install dependencies."
fi

# Show access information
echo "📍 Opening in browser at: http://localhost:8502"
echo "🔄 Auto-refresh every 10 minutes"  
echo "⛔ Press Ctrl+C to stop"
echo ""

# Run Streamlit application on port 8502
streamlit run main.py --server.port=8502
