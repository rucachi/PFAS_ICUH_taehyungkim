
import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.pfas_library import load_library_data
from utils.detection import analyze_peak
from utils.unknown_manager import save_unknown_feature, load_unknowns_df

def run_verification():
    print("--- Starting PFAS Detection Verification ---")
    
    # 1. Load Library
    print("\n1. Loading Library...")
    lib_df = load_library_data()
    print(f"   Library size: {len(lib_df)}")
    if lib_df.empty:
        print("   [FAIL] Library is empty!")
        return
        
    # 2. Test Known Compound (PFOA ex-mass 413.97)
    print("\n2. Testing Known Match (PFOA)...")
    res_known = analyze_peak(lib_df, input_mz=413.97, mz_tolerance=10.0)
    cands = res_known['candidates']
    print(f"   Candidates found: {len(cands)}")
    
    found_pfoa = False
    if not cands.empty:
        print(f"   Top match: {cands.iloc[0]['name']} (sim={cands.iloc[0]['similarity']})")
        # Check if 'PFOA' or similar name is in list
        match = cands[cands['name'].str.contains("PFOA|Perfluorooctanoic", case=False)]
        if not match.empty:
            found_pfoa = True
            print("   [PASS] PFOA found in candidates.")
        else:
             print("   [WARN] PFOA not explicitly found in top names.")
    else:
        print("   [FAIL] No candidates for PFOA mass.")
        
    # 3. Test Unknown
    print("\n3. Testing Unknown Input (m/z 200.0, unlikely PFAS)...")
    res_unk = analyze_peak(lib_df, input_mz=200.0, mz_tolerance=5.0)
    print(f"   Is Unknown: {res_unk['is_unknown']}")
    print(f"   Status Label: {res_unk['status_label']}")
    
    if res_unk['is_unknown']:
        print("   [PASS] Correctly tagged as unknown.")
        
        # 4. Test Saving
        print("\n4. Testing Save Unknown...")
        feat = {
            "mz": 200.0,
            "rt": 1.2,
            "predicted_class": res_unk['predicted_class'],
            "candidates": []
        }
        uid = save_unknown_feature(feat)
        print(f"   Saved ID: {uid}")
        
        # Verify load
        udf = load_unknowns_df()
        if uid in udf['id'].values:
            print(f"   [PASS] ID {uid} found in DB.")
        else:
             print("   [FAIL] ID not found in loaded DB.")
    else:
        print("   [FAIL] Should have been unknown.")

if __name__ == "__main__":
    run_verification()
