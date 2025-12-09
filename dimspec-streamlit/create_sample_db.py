
import sqlite3
import pandas as pd
from pathlib import Path
import os
import sys

# Setup paths
BASE_DIR = Path(__file__).parent # dimspec-streamlit
PARENT_DIR = BASE_DIR.parent # dimspec-main
ORIGINAL_DB = PARENT_DIR / "data" / "dimspec_nist_pfas.sqlite" # Found this one locally
if not ORIGINAL_DB.exists():
    ORIGINAL_DB = PARENT_DIR / "data" / "pfas_dimspec.db"
    if not ORIGINAL_DB.exists():
         ORIGINAL_DB = BASE_DIR / "data" / "dimspec_nist_pfas.sqlite" # Try local too

SAMPLE_DB = BASE_DIR / "data" / "dimspec_sample.sqlite"

def create_sample_db():
    print(f"Source DB: {ORIGINAL_DB}")
    print(f"Target DB: {SAMPLE_DB}")
    
    if not ORIGINAL_DB.exists():
        print("Error: Source database not found!")
        return

    src_conn = sqlite3.connect(ORIGINAL_DB)
    tgt_conn = sqlite3.connect(SAMPLE_DB)
    
    # DEBUG: List tables
    print("Source Tables:")
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", src_conn)
    print(tables)
    
    # 1. Compounds (Top 200)
    print("Copying Compounds (Top 200)...")
    try:
        df_comp = pd.read_sql_query("SELECT * FROM compounds LIMIT 200", src_conn)
        df_comp.to_sql("compounds", tgt_conn, if_exists="replace", index=False)
        print(f"  - Copied {len(df_comp)} rows.")
        
        # Get IDs for filtering other tables
        comp_ids = tuple(df_comp['id'].astype(str).tolist())
        if not comp_ids:
            comp_ids = ('-1',) # mild hack for empty tuple
        
        id_list = ",".join([f"'{x}'" for x in comp_ids])
    except Exception as e:
        print(f"  - Error copying compounds: {e}")
        return

    # 2. Samples (All or limited)
    print("Copying Samples...")
    try:
        df_samp = pd.read_sql_query("SELECT * FROM samples LIMIT 50", src_conn)
        df_samp.to_sql("samples", tgt_conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"  - Error copying samples: {e}")

    # 3. Peaks (Related to compounds)
    print("Copying Peaks...")
    try:
        # Just take peaks blindly to avoid schema headaches
        df_peaks = pd.read_sql_query("SELECT * FROM peaks LIMIT 500", src_conn)
        df_peaks.to_sql("peaks", tgt_conn, if_exists="replace", index=False)
        
        # Get peak IDs for MS data
        peak_ids = tuple(df_peaks['id'].astype(str).tolist())
        if not peak_ids: peak_ids = ('-1',)
        p_list = ",".join([f"'{x}'" for x in peak_ids])
        
        print(f"  - Copied {len(df_peaks)} peaks.")
    except Exception as e:
        print(f"  - Error copying peaks (might differ): {e}")

    # 4. MS Data (Related to peaks)
    print("Copying MS Data...")
    try:
        # Try to filter if possible, otherwise blind copy
        if 'id' in df_peaks.columns:
            df_ms = pd.read_sql_query(f"SELECT * FROM ms_data WHERE peak_id IN ({p_list}) LIMIT 2000", src_conn)
        else:
            df_ms = pd.read_sql_query("SELECT * FROM ms_data LIMIT 2000", src_conn)
            
        df_ms.to_sql("ms_data", tgt_conn, if_exists="replace", index=False)
        print(f"  - Copied {len(df_ms)} spectra.")
    except Exception as e:
        print(f"  - Error copying ms_data: {e}")
        
    # 5. Metadata columns (Create empty if needed or copy small tables)
    # Just copy small tables entirely
    small_tables = list(tables['name'].values)
    # Remove huge tables/already processed
    exclude = ['compounds', 'samples', 'peaks', 'ms_data', 'peak_data', 'sqlite_sequence']
    
    for tbl in small_tables:
        if tbl in exclude: continue
        print(f"Copying {tbl}...")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {tbl}", src_conn)
            df.to_sql(tbl, tgt_conn, if_exists="replace", index=False)
        except:
            pass

    src_conn.close()
    tgt_conn.close()
    print("Sample Database Created Successfully!")

if __name__ == "__main__":
    create_sample_db()
