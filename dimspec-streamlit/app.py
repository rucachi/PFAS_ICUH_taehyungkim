"""
DIMSpec Explorer - Main Entry Point
"""
import streamlit as st
from pathlib import Path
import sys

# Move to root to ensure relative imports work standardly if run from root
sys.path.append(str(Path(__file__).parent))

from utils.config import init_page, get_db_path

# Page configuration
init_page()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-align: center;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🔬 DIMSpec Explorer</h1>', unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555;'>Database Infrastructure for Mass Spectrometry</h3>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #1f77b4; margin-bottom: 2rem;'>(재)국제도시물정보과학연구원</h2>", unsafe_allow_html=True)

st.info("👈 **Please select a tool from the sidebar to begin.**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-box">
    <h3>📊 Table Explorer</h3>
    <p>Browse detailed database tables with advanced filtering options.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-box">
    <h3>🔍 Compound Search</h3>
    <p>Find PFAS compounds by name, m/z, or retention time.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-box">
    <h3>📈 Spectrum Viewer</h3>
    <p>Visualize and compare mass spectra with multi-peak overlays.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick diagnostics
DB_PATH = Path(__file__).parent / "data" / "dimspec_nist_pfas.sqlite"
if DB_PATH.exists():
    st.success(f"✅ Database connected: `{DB_PATH.name}`")
else:
    st.warning("⚠️ Database not found in default path. Please check the `data/` directory.")

st.sidebar.success("Select a page above 👆")
st.sidebar.markdown("---")
st.sidebar.caption("v1.1.0 (Refactored)")
