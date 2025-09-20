# Package Management in Your TAF Dashboard

## 🍺 Homebrew (System Level)
**Purpose:** Manages your Mac's development tools and Python itself

**What Homebrew installed for you:**
- Python 3.13.7 (the main Python program)
- Location: `/opt/homebrew/bin/python3`

**Check what Homebrew manages:**
```bash
brew list | grep python
# Shows: python@3.13
```

## 🐍 Virtual Environment + pip (Project Level)  
**Purpose:** Manages your TAF Dashboard's specific Python packages

**What pip installed in your virtual environment:**
- streamlit (the web framework)
- pandas (data processing)
- requests (to get weather data)
- streamlit-autorefresh (auto-refresh feature)
- + 30+ other supporting packages

**Location:** `/Users/sunnywslau/Code/checkTAF/venv/`

## 🔄 How Your start.sh Works

1. **Uses Homebrew's Python:** `/opt/homebrew/bin/python3`
2. **Activates virtual environment:** `source venv/bin/activate`
3. **Now uses project's packages:** streamlit, pandas, etc.
4. **Runs your app:** `streamlit run main.py`

## 💡 Simple Way to Think About It

**Homebrew = Installing Python on your Mac**
- Like installing Microsoft Word on Windows

**pip + venv = Installing specific tools for your project**  
- Like installing plugins/extensions just for one document

## 🛠️ Common Commands

**Check what Homebrew manages:**
```bash
brew list | grep python
```

**Check what your project uses:**
```bash
cd /Users/sunnywslau/Code/checkTAF
source venv/bin/activate  
pip list
```

**Update Homebrew's Python:**
```bash
brew upgrade python@3.13
```

**Update your project's packages:**
```bash
cd /Users/sunnywslau/Code/checkTAF
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## ✅ Your Setup is Perfect!

You're using **both** correctly:
- **Homebrew** for Python itself (system-wide)  
- **pip + virtual environment** for your TAF app packages (project-specific)

This is the **recommended best practice** for Python development on Mac!
