"""
Configuration and shared constants for DIMSpec Explorer.
"""
import streamlit as st
from pathlib import Path
import sys

# Define base directory (assuming this file is in utils/)
BASE_DIR = Path(__file__).parent.parent

# Database Paths
DEFAULT_DB_PATH = BASE_DIR / "data" / "dimspec_nist_pfas.sqlite"
ALTERNATIVE_DB_PATHS = [
    BASE_DIR.parent / "dimspec_nist_pfas.sqlite",
    Path("dimspec_nist_pfas.sqlite"),
    BASE_DIR / "data" / "dimspec_sample.sqlite", # Added sample DB
    BASE_DIR.parent / "dimspec_sample.sqlite",
]

def get_db_path() -> Path:
    """Resolve the database path."""
    if DEFAULT_DB_PATH.exists():
        return DEFAULT_DB_PATH
    for path in ALTERNATIVE_DB_PATHS:
        if path.exists():
            return path
    return DEFAULT_DB_PATH

# Page Configuration
PAGE_CONFIG = {
    "page_title": "DIMSpec Explorer",
    "page_icon": "🔬",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Custom CSS
CUSTOM_CSS = """
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
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
"""

def init_page(page_title: str = None):
    """Initialize page config and load CSS."""
    config = PAGE_CONFIG.copy()
    if page_title:
        config["page_title"] = f"{page_title} | DIMSpec Explorer"
    
    st.set_page_config(**config)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Constants for Data Selection & Smart Search ---

TABLE_CATEGORIES = {
    "1. Core Data": [
        "compounds", "samples", "peaks", "ms_data", "qc_data", "compound_fragments",
        "annotated_fragments", "ms_spectra"
    ],
    "2. Reference / Metadata": [
        "chromatography_descriptions", "ms_descriptions", "ms_methods", "mobile_phases", 
        "qc_methods", "instrument_properties", "contributors", "affiliations",
        "carrier_mixes", "carrier_additives", "elements", "isotopes"
    ],
    "3. Normalization": [
        "norm_chromatography_types", "norm_column_chemistries", "norm_sample_classes", 
        "norm_carriers", "norm_additives", "norm_ionization", "norm_polarity_types",
        "norm_ms_types", "norm_fragmentation_types", "norm_peak_confidence"
    ],
    "4. Relationship / Alias": [
        "compound_aliases", "fragment_aliases", "sample_aliases", "carrier_aliases", 
        "additive_aliases"
    ],
    "5. Views (Analysis)": [
        "view_compounds", "view_peaks", "view_samples", "view_fragment_mz_stats", 
        "view_logs", "view_qc_methods", "view_separation_types", "view_method",
        "view_chromatography_types", "view_mass_analyzers", "view_mobile_phases",
        "view_compound_fragments", "view_ms_methods"
    ]
}

PFAS_FAMILIES = [
    "PFCA (Carboxylic Acids)",
    "PFSA (Sulfonic Acids)", 
    "FTS (Fluorotelomer Sulfonates)",
    "PAPs (Phosphate Esters)",
    "FOSA/FOSAA (Sulfonamides)",
    "PFEther (Ether Acids)",
    "Other"
]

FUNCTIONAL_GROUPS = [
    "-COOH (Carboxylic Asset)",
    "-SO3H (Sulfonic Acid)",
    "-COO- (Ester)",
    "Sulfonamide (-SO2N-)",
    "Alcohol (-OH)",
    "Ether (-O-)"
]
