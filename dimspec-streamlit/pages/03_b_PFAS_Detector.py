import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Move to root to ensure relative imports work standardly
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import init_page
from utils.pfas_library import load_library_data
from utils.detection import analyze_peak, DEFAULT_MZ_TOLERANCE_PPM, DEFAULT_RT_MARGIN
from utils.unknown_manager import save_unknown_feature, load_unknowns_df

# Page Init
init_page("PFAS Detector")

st.markdown('<h1 class="main-header">🕵️ PFAS Detector</h1>', unsafe_allow_html=True)
st.caption("Intelligent Pipeline: Classification, Identification, and Unknown Discovery.")

# --- 1. Sidebar Control ---
with st.sidebar:
    st.header("⚙️ Settings")
    mz_tol = st.number_input("m/z Tolerance (ppm)", value=DEFAULT_MZ_TOLERANCE_PPM, min_value=0.1)
    rt_win = st.number_input("RT Margin (min)", value=DEFAULT_RT_MARGIN, min_value=0.0)
    
    st.info("""
    **Pipeline Steps:**
    1. Filter by m/z & RT
    2. Rank by Spectrum Similarity
    3. Predict Family (Class)
    4. Tag 'Unknown' if low sim
    """)

# --- 2. Load Library ---
library_df = load_library_data()
st.toast(f"Loaded {len(library_df)} library entries", icon="📚")

# --- 3. Input Section ---
st.subheader("1. Peak Input")

tab_simple, tab_advanced = st.tabs(["Simple Mode (m/z only)", "Advanced Mode (Spectrum)"])

input_data = {}

with tab_simple:
    col1, col2, col3 = st.columns(3)
    in_mz = col1.number_input("Precursor m/z", value=413.97, format="%.4f", key="sim_mz")
    in_rt = col2.number_input("Retention Time (min)", value=0.0, format="%.2f", key="sim_rt")
    in_pol = col3.selectbox("Polarity", ["Negative", "Positive"], key="sim_pol")
    
    if st.button("🚀 Analyze Peak", key="btn_simple"):
        input_data = {
            "mz": in_mz,
            "rt": in_rt if in_rt > 0 else None,
            "spectrum_mz": [],
            "spectrum_int": []
        }

with tab_advanced:
    st.markdown("**Paste MS/MS Spectrum List** (m/z intensity)")
    c1, c2 = st.columns(2)
    adv_mz = c1.number_input("Precursor m/z", value=413.97, format="%.4f", key="adv_mz")
    adv_rt = c2.number_input("Retention Time (min)", value=0.0, format="%.2f", key="adv_rt")
    
    spec_text = st.text_area("Spectrum Data (Format: mz intensity, one per line)", height=150,
                             placeholder="50.1 100\n119.0 500\n169.0 800\n...")
    
    if st.button("🚀 Analyze with Spectrum", key="btn_adv"):
        # Parse spectrum
        mzs = []
        ints = []
        if spec_text:
            for line in spec_text.split('\n'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        mzs.append(float(parts[0]))
                        ints.append(float(parts[1]))
                    except:
                        pass
        
        input_data = {
            "mz": adv_mz,
            "rt": adv_rt if adv_rt > 0 else None,
            "spectrum_mz": mzs,
            "spectrum_int": ints
        }

# --- 4. Analysis & Results ---
if input_data:
    st.markdown("---")
    st.subheader("2. Analysis Results")
    
    with st.spinner("Running Detection Pipeline..."):
        results = analyze_peak(
            library_df,
            input_mz=input_data['mz'],
            input_rt=input_data['rt'],
            spectrum_mz=input_data['spectrum_mz'],
            spectrum_int=input_data['spectrum_int'],
            mz_tolerance=mz_tol,
            rt_margin=rt_win
        )
    
    # Unpack
    pred_class = results['predicted_class']
    conf = results['class_confidence']
    is_unknown = results['is_unknown']
    candidates = results['candidates']
    status_label = results['status_label']
    
    # Display Summary Cards
    m1, m2, m3 = st.columns(3)
    
    m1.metric("Status", status_label, delta_color="off" if not is_unknown else "inverse")
    m2.metric("Predicted Family", pred_class, f"{conf*100:.1f}% Conf.")
    m3.metric("Candidates Found", len(candidates))
    
    # Specific Alert for Unknown
    if is_unknown:
        st.error(f"⚠️ **Unknown PFAS Detected!** (Similarity < 0.8)")
        if st.button("💾 Save as Unknown Feature"):
            # Prepare data for saving
            feature_data = {
                "mz": input_data['mz'],
                "rt": input_data['rt'],
                "predicted_class": pred_class,
                "best_similarity": candidates.iloc[0]['similarity'] if not candidates.empty else 0.0,
                "candidates": candidates[['pfas_id', 'name', 'similarity']].to_dict('records')
            }
            new_id = save_unknown_feature(feature_data)
            st.success(f"Saved to Unknown Database! ID: **{new_id}**")
            st.balloons()
            
    else:
        st.success(f"✅ Confirmed Match: {candidates.iloc[0]['name']}")
        
    # Candidates Table
    st.markdown("### Top Candidates")
    if not candidates.empty:
        # ... (Display dataframe code)
        display_df = candidates[['pfas_id', 'name', 'Family', 'precursor_mz', 'mz_error_ppm', 'similarity']].copy()
        display_df['mz_error_ppm'] = display_df['mz_error_ppm'].map('{:.2f}'.format)
        display_df['similarity'] = display_df['similarity'].map('{:.3f}'.format)
        
        st.dataframe(
            display_df,
            column_config={
                "similarity": st.column_config.ProgressColumn(
                    "Similarity Score",
                    help="Cosine similarity (0-1)",
                    min_value=0,
                    max_value=1,
                    format="%.3f",
                ),
            },
            use_container_width=True
        )
    else:
        st.warning("No candidates found within tolerance window.")

# --- 5. Unknowns History ---
st.markdown("---")
with st.expander("📚 Recently Discovered Unknowns"):
    udf = load_unknowns_df()
    if not udf.empty:
        st.dataframe(
            udf[['id', 'timestamp', 'input_mz', 'predicted_class', 'status']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No unknown features saved yet.")
