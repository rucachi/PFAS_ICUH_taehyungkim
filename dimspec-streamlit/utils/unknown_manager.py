
"""
Unknown PFAS Manager
Handles persistence of unknown features to a local JSON file.
"""
import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Path to unknown storage
DATA_DIR = Path(__file__).parent.parent / "data"
UNKNOWN_FILE = DATA_DIR / "unknown_pfas.json"

def save_unknown_feature(feature_data: Dict[str, Any]) -> str:
    """
    Save an unknown feature to the persistent store.
    Returns the assigned ID.
    """
    # Load existing
    unknowns = load_unknowns_raw()
    
    # Generate ID
    idx = len(unknowns) + 1
    new_id = f"UNK_PFAS_{idx:04d}"
    
    # Add metadata
    record = {
        "id": new_id,
        "timestamp": datetime.now().isoformat(),
        "input_mz": feature_data.get("mz"),
        "input_rt": feature_data.get("rt"),
        "predicted_class": feature_data.get("predicted_class"),
        "similarity_score": feature_data.get("best_similarity", 0.0),
        "status": "New",
        # Store simplified candidates for reference
        "candidates_snapshot": [
            {
                "pfas_id": c["pfas_id"], 
                "name": c["name"],
                "similarity": c["similarity"]
            } for c in feature_data.get("candidates", [])[:3] # store top 3
        ] if feature_data.get("candidates") else []
    }
    
    unknowns.append(record)
    
    # Save
    ensure_data_dir()
    with open(UNKNOWN_FILE, 'w', encoding='utf-8') as f:
        json.dump(unknowns, f, indent=2, ensure_ascii=False)
        
    return new_id

def load_unknowns_raw() -> List[Dict]:
    if not UNKNOWN_FILE.exists():
        return []
    try:
        with open(UNKNOWN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def load_unknowns_df() -> pd.DataFrame:
    raw = load_unknowns_raw()
    if not raw:
        return pd.DataFrame()
    return pd.DataFrame(raw)

def ensure_data_dir():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)
