import streamlit as st
from pathlib import Path

st.set_page_config(page_title="About", page_icon="ℹ️")

st.markdown("# ℹ️ About DIMSpec Explorer")

st.markdown("""
## Database Infrastructure for Mass Spectrometry

**DIMSpec Explorer** is a Python/Streamlit application for exploring PFAS mass spectrometry data.
This is a prototype implementation of core features from the original R Shiny DIMSpec application.

This application was produced by **(재)국제도시물정보과학연구원** (International Urban Water Information Science Research Institute).

### Original DIMSpec Project

The original DIMSpec project was developed by the National Institute of Standards and Technology (NIST)
Chemical Sciences Division to provide a comprehensive portable database toolkit supporting 
non-targeted analysis of high resolution mass spectrometry experiments.

- **GitHub**: [https://github.com/usnistgov/dimspec](https://github.com/usnistgov/dimspec)
- **Documentation**: [https://pages.nist.gov/dimspec/docs/](https://pages.nist.gov/dimspec/docs/)

### Features in This Prototype

- ✅ **Table Explorer**: Browse all database tables and views with server-side pagination.
- ✅ **Compound Search**: Multi-criteria search for PFAS compounds.
- ✅ **Spectrum Viewer**: Interactive mass spectra visualization with overlays.
- ✅ **Data Export**: Download data as CSV or Excel.

### Technology Stack

- **Framework**: Streamlit
- **Database**: SQLite
- **Visualization**: Plotly
- **Data Processing**: Pandas, NumPy, SciPy

### Disclaimer

This is a prototype application focusing on core read-only features. 
Advanced features such as data upload, quality control workflows, and complex 
statistical analyses are not included in this version.

---

**Version**: 1.1.0 
**Last Updated**: 2025-12-08
""")
