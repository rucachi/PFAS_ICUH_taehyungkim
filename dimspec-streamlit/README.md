# DIMSpec Explorer - Python/Streamlit Edition

🔬 **Database Infrastructure for Mass Spectrometry** - A Python/Streamlit application for exploring PFAS mass spectrometry data.

## Features

- ✅ **Table Explorer**: Browse database tables and views with search and pagination
- ✅ **Compound Search**: Search PFAS compounds by name or ID  
- ✅ **Spectrum Viewer**: Interactive mass spectrum visualization
- ✅ **Data Export**: Download data as CSV or Excel
- ✅ **Cross-platform**: Works on Windows, Mac, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download this folder**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Add the database file:**

Copy the SQLite database to the `data/` folder:
- `dimspec_nist_pfas.sqlite` OR
- `pfas_dimspec.db`

The app will automatically detect it.

## Running the Application

### Method 1: Streamlit (Web Interface)

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

### Method 2: Package as Executable (Optional)

Create a standalone .exe file (Windows):

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --add-data "data;data" --add-data "utils;utils" app.py

# Run the executable
dist/app.exe
```

For Mac/Linux, use `:` instead of `;` in the `--add-data` paths.

## Usage Guide

### Home Page
- Overview of application features
- Database connection status

### Table Explorer
1. Select a table from the dropdown
2. Use the search box to find specific data
3. Navigate pages with the page selector
4. Export data as CSV or Excel

### Compound Search
1. Enter a compound name (e.g., "PFOA", "PFOS")
2. Browse search results
3. Select a compound to view detailed information

### Spectrum Viewer
1. Select a peak ID from the dropdown
2. Choose normalization method (max, sum, or mean)
3. View interactive spectrum plot
4. Check spectrum statistics

## Project Structure

```
dimspec-streamlit/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── utils/
│   ├── __init__.py
│   ├── database.py       # Database operations
│   ├── visualizations.py # Plotting functions
│   └── data_processing.py # Data manipulation
└── data/
    └── dimspec_nist_pfas.sqlite  # Database file (add manually)
```

## Technology Stack

- **Framework**: [Streamlit](https://streamlit.io/) 1.28+
- **Database**: SQLite3
- **Visualization**: [Plotly](https://plotly.com/) 5.17+
- **Data Processing**: [Pandas](https://pandas.pydata.org/) 2.0+, NumPy, SciPy

## Troubleshooting

### Database not found
- Ensure the database file is in the `data/` folder
- Check that the filename is either `dimspec_nist_pfas.sqlite` or `pfas_dimspec.db`

### Import errors
- Run `pip install -r requirements.txt` to install all dependencies
- Ensure you're using Python 3.8+

### Port already in use
- Change the port: `streamlit run app.py --server.port 8502`

## About the Original DIMSpec Project

This application is a Python prototype of core features from the original **DIMSpec** project developed by NIST:

- **GitHub**: https://github.com/usnistgov/dimspec
- **Documentation**: https://pages.nist.gov/dimspec/docs/
- **Citation**: Ragland, J. M.; Place, B. J. *J. Am. Soc. Mass Spectrom.* **2024**. DOI: 10.1021/jasms.4c00073

## Version

**v1.0.0** - Python/Streamlit Prototype (2025-11-29)

## Notes

- This is a **read-only** prototype focusing on data exploration
- Advanced features (data upload, QC workflows) are not included
- For full functionality, use the original R Shiny application

## License

This prototype follows the same NIST public domain license as the original DIMSpec project.
