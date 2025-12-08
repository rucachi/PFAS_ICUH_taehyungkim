import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.database import (
    connect_db, get_view_data, get_spectrum_data, get_ms1_by_peak
)
from utils.visualizations import plot_spectrum
from utils.data_processing import normalize_spectrum, calculate_statistics
from utils.config import init_page, get_db_path

init_page("Spectrum Viewer")

st.markdown("# 📈 Spectrum Viewer")

DB_PATH = get_db_path()
conn = connect_db(str(DB_PATH)) if DB_PATH.exists() else None

if not conn:
    st.error("Database unavailable.")
    st.stop()

# Layout
col_ctrl, col_main = st.columns([1, 3])

with col_ctrl:
    st.subheader("Controls")
    
    # 1. Select Peak(s)
    # Ideally we'd search, but for now lists top peaks
    # We really need a search box here for peaks, but let's stick to list for prototype
    peaks_df = get_view_data(conn, "peaks", limit=200) # limited list
    
    if not peaks_df.empty:
        peak_options = peaks_df['id'].tolist()
        
        # Multi-select for overlay
        selected_peak_ids = st.multiselect(
            "Select Peak IDs to Overlay", 
            options=peak_options,
            default=[peak_options[0]] if peak_options else None
        )
        
        # 2. Normalization
        norm_method = st.radio(
            "Normalization",
            ["Max (100%)", "Sum (1.0)", "Mean", "None"],
            index=0
        )
        
        method_map = {
            "Max (100%)": "max",
            "Sum (1.0)": "sum", 
            "Mean": "mean",
            "None": "none"
        }
        selected_method = method_map[norm_method]

# Main Area
with col_main:
    if selected_peak_ids:
        traces = []
        
        # Prepare traces
        for pid in selected_peak_ids:
             data = get_ms1_by_peak(conn, pid)
             if data:
                 mz, intensity = data['mz'], data['intensity']
                 
                 # Normalize
                 mz_norm, int_norm = normalize_spectrum(mz, intensity, method=selected_method)
                 
                 traces.append({
                     'mz': mz_norm,
                     'intensity': int_norm,
                     'name': f"Peak {pid}",
                     # 'color': ... (optional, let plotly cycle)
                 })
        
        if traces:
            # We pass the first trace as primary for backward compat or just pass all as 'traces'
            # The refactored plot_spectrum handles 'traces' list
            fig = plot_spectrum(
                mz=None, intensity=None, # Pure overlay mode
                traces=traces,
                title=f"Mass Spectrum Overlay ({len(traces)} peaks)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics for the first selected peak (or table for all)
            st.markdown("### Statistics")
            
            stats_data = []
            for i, t in enumerate(traces):
                 s = calculate_statistics(t['intensity'])
                 s['peak_name'] = t['name']
                 stats_data.append(s)
            
            st.dataframe(pd.DataFrame(stats_data).set_index('peak_name'))
            
        else:
            st.warning("Selected peaks have no spectral data.")
    else:
        st.info("Select peaks from the sidebar to visualize.")
