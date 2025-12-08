
"""
PFAS Library Management
Handles fetching reference data from DB and caching it for the detection pipeline.
Acts as an abstraction layer over the raw SQL tables.
"""
import pandas as pd
import numpy as np
import streamlit as st
import json
from typing import Optional, List
from utils import database as db
from utils import data_processing as dp
from utils.config import get_db_path

# To simulate a pre-computed fingerprint, we will compute it on load if missing.
# In production, this should be a stored column/table.

@st.cache_data(show_spinner="Loading PFAS Library...")
def load_library_data() -> pd.DataFrame:
    """
    Fetch all compounds and necessary metadata for detection.
    Computes fingerprints for candidates that have spectra.
    """
    conn = db.connect_db(get_db_path())
    
    # 1. Fetch Basic Compound Data
    # prioritizing pfas_summary if exists (it has rt_mean), else compounds
    # For this prototype we will try to join meaningful columns
    
    # Check if pfas_summary exists
    tables = db.get_tables(conn)
    
    if "pfas_summary" in tables:
        # Ideally this view has everything: name, formula, precursor_mz, rt_mean
        query = """
        SELECT * FROM pfas_summary
        """
        try:
            df = pd.read_sql_query(query, conn)
        except Exception:
            df = pd.DataFrame()
    else:
        # Fallback to compounds table
        # We need rt information. If not in compounds, we are in trouble for RT filter.
        # Let's assume compounds has what we need or we mock it.
        # Based on inspection: compounds has 'fixedmass'.
        query = """
        SELECT id as pfas_id, name, formula, fixedmass as precursor_mz, additional 
        FROM compounds
        """
        df = pd.read_sql_query(query, conn)
        # Mock RT if missing (so pipeline doesn't crash, but filtering won't work well)
        if 'rt_mean' not in df.columns:
            df['rt_mean'] = np.nan
            
    # 2. Add Family/Class Info
    # Use our helper to infer class if not present in DB
    if 'Family' not in df.columns:
        from utils.data_processing import get_compound_family
        df['Family'] = df['name'].apply(get_compound_family)
        
    # 3. Fetch/Compute Fingerprints
    # This is expensive. For prototype, we might only do it for a subset or 
    # check if 'ms_data' has linked entries.
    
    # Let's fetch all ms_data aggregated by peak -> compound
    # Since linking compounds-peaks is hard without explicit schema knowledge of this specific DB version,
    # We will try a standard join: compounds.id -> peaks.compound_id -> ms_data.peak_id
    
    # Check if peaks has compound_id
    peak_cols = db.get_column_names(conn, 'peaks')
    
    df['fingerprint'] = None
    df['has_spectrum'] = False
    
    if 'compound_id' in peak_cols:
        # Heavy query: Get one representative spectrum per compound
        # LIMIT 1 per compound to save time
        spec_query = """
        SELECT p.compound_id, m.measured_mz, m.measured_intensity
        FROM peaks p
        JOIN ms_data m ON p.id = m.peak_id
        GROUP BY p.compound_id
        """
        try:
            specs = pd.read_sql_query(spec_query, conn)
            
            # Map specs to library df
            # We need to parse strings to lists and compute fingerprint
            # Optimize: Pre-compute map
            spec_map = {}
            for idx, row in specs.iterrows():
                try:
                    c_id = row['compound_id']
                    mz = [float(x) for x in str(row['measured_mz']).split()]
                    inten = [float(x) for x in str(row['measured_intensity']).split()]
                    
                    # Compute normalized fingerprint vector (numpy)
                    # Use standard bins (50-1200, size 1)
                    fp_df = dp.bin_spectrum_fingerprint(mz, inten, mz_min=50.0, mz_max=1200.0, bin_size=1.0)
                    
                    # Normalize Max=1
                    vals = fp_df['intensity'].values
                    m = np.max(vals)
                    if m > 0: vals = vals / m
                    
                    spec_map[c_id] = vals
                except:
                    continue
                    
            # Assign to main DF
            # Note: storing numpy array in pandas cell is fine
            df['fingerprint'] = df['pfas_id'].map(spec_map)
            df['has_spectrum'] = df['fingerprint'].notna()
            
        except Exception as e:
            # st.warning(f"Could not load spectra: {e}")
            pass
            
    # Do not close cached conn
    
    return df
