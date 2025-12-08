import sys
import os
from pathlib import Path
import pandas as pd

# Add current directory to path to import utils
sys.path.append(str(Path(__file__).parent))

from utils.database import (
    connect_db, get_tables, get_table_data, search_table,
    get_compound_by_name, get_compound_details, get_spectrum_data,
    search_pfas # New function
)

DB_PATH = Path(__file__).parent / "data" / "dimspec_nist_pfas.sqlite"

def test_table_explorer(conn):
    print("\n🧪 Testing Table Explorer...")
    tables = get_tables(conn)
    print(f"  Found {len(tables)} tables.")
    if not tables:
        print("  ❌ No tables found.")
        return False
    
    table = "compounds"
    if table in tables:
        df = get_table_data(conn, table, limit=5)
        print(f"  'compounds' table data shape: {df.shape}")
        if df.empty:
            print("  ❌ 'compounds' table is empty.")
            return False
        
        # Test search
        search_term = "Perfluoro"
        df_search = search_table(conn, table, search_term, limit=5)
        print(f"  Search for '{search_term}' returned {len(df_search)} rows.")
        if df_search.empty:
            print("  ⚠️ Search returned no results (might be expected depending on data).")
    return True

def test_compound_search(conn):
    print("\n🧪 Testing Compound Search...")
    # 1. Basic Name Search
    term = "PFOA"
    results = get_compound_by_name(conn, term)
    print(f"  Name Search '{term}' returned {len(results)} results.")
    
    # 2. Advanced Filter Search (New Feature)
    print("  Testing Advanced Filters (m/z and RT)...")
    # Let's try a wide range first to ensure we get something
    mz_range = (0, 1000)
    rt_range = (0, 100)
    
    results_filtered = search_pfas(conn, mz_range=mz_range, rt_range=rt_range, limit=10)
    print(f"  Filtered Search (mz={mz_range}, rt={rt_range}) returned {len(results_filtered)} results.")
    
    if not results_filtered.empty:
        # Verify filters actually worked (if columns exist)
        cols = results_filtered.columns
        if 'precursor_mz' in cols:
             min_mz = results_filtered['precursor_mz'].min()
             max_mz = results_filtered['precursor_mz'].max()
             print(f"    Result m/z range: {min_mz:.2f} - {max_mz:.2f}")
             if min_mz < mz_range[0] or max_mz > mz_range[1]:
                 print("    ❌ m/z filter failed!")
                 return False
        
        if 'rt' in cols:
             min_rt = results_filtered['rt'].min()
             max_rt = results_filtered['rt'].max()
             print(f"    Result RT range: {min_rt:.2f} - {max_rt:.2f}")
    
    # 3. Details Retrieval
    if not results.empty:
        compound_id = results.iloc[0]['id']
    elif not results_filtered.empty:
        compound_id = results_filtered.iloc[0]['id']
    else:
        # Fallback search
        fallback = get_compound_by_name(conn, "a")
        if not fallback.empty:
            compound_id = fallback.iloc[0]['id']
        else:
             print("  ❌ No compounds found to test details.")
             return False

    details = get_compound_details(conn, compound_id)
    print(f"  Details for ID {compound_id}: {details.keys() if details else 'None'}")
    if not details:
        print("  ❌ Could not get details for found compound.")
        return False
        
    return True

def test_spectrum_viewer(conn):
    print("\n🧪 Testing Spectrum Viewer...")
    # Need a valid peak_id. Let's get one from ms_data or peaks
    cursor = conn.cursor()
    cursor.execute("SELECT peak_id FROM ms_data LIMIT 1")
    row = cursor.fetchone()
    if row:
        peak_id = row[0]
        print(f"  Testing with Peak ID: {peak_id}")
        data = get_spectrum_data(conn, peak_id)
        if data:
            mz, intensity = data
            print(f"  Got spectrum data: {len(mz)} m/z points, {len(intensity)} intensity points.")
            if len(mz) != len(intensity):
                print("  ❌ Mismatch in data lengths.")
                return False
        else:
            print("  ❌ Failed to retrieve spectrum data.")
            return False
    else:
        print("  ⚠️ No data in ms_data table to test with.")
    return True

def main():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)
        
    conn = connect_db(str(DB_PATH))
    if not conn:
        print("❌ Failed to connect to database.")
        sys.exit(1)
        
    print(f"✅ Connected to {DB_PATH.name}")
    
    success = True
    success &= test_table_explorer(conn)
    success &= test_compound_search(conn)
    success &= test_spectrum_viewer(conn)
    
    if success:
        print("\n✅ All backend logic tests passed!")
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
