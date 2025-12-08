"""
Data processing utilities for DIMSpec Streamlit application.
Handles data transformation, analysis, and fingerprint generation.
"""

import pandas as pd
import numpy as np
import re
from typing import List, Tuple, Optional, Any
from scipy import stats

def normalize_spectrum(
    mz: List[float],
    intensity: List[float],
    method: str = "max"
) -> Tuple[List[float], List[float]]:
    """
    Normalize spectrum intensity values.
    
    Args:
        mz: m/z values
        intensity: Intensity values
        method: 'max' (scale to 100%), 'sum' (scale to total 1), 'mean' (scale to avg 100)
    """
    if not intensity:
        return mz, intensity
        
    intensity_array = np.array(intensity)
    
    if method.lower() == "max":
        max_val = np.max(intensity_array)
        normalized = (intensity_array / max_val * 100) if max_val > 0 else intensity_array
    elif method.lower() == "sum":
        sum_val = np.sum(intensity_array)
        normalized = (intensity_array / sum_val) if sum_val > 0 else intensity_array
    elif method.lower() == "mean":
        mean_val = np.mean(intensity_array)
        normalized = (intensity_array / mean_val * 100) if mean_val > 0 else intensity_array
    else:
        normalized = intensity_array
    
    return mz, normalized.tolist()

def bin_spectrum_fingerprint(
    mz: List[float],
    intensity: List[float],
    mz_min: float = 50.0,
    mz_max: float = 1200.0,
    bin_size: float = 1.0
) -> pd.DataFrame:
    """
    Convert spectrum to a binned fingerprint vector.
    Useful for similarity searching and ML features.
    """
    # Create bins
    bins = np.arange(mz_min, mz_max + bin_size, bin_size)
    
    # Digitizing
    mz_array = np.array(mz)
    int_array = np.array(intensity)
    
    # Filter out of range
    mask = (mz_array >= mz_min) & (mz_array <= mz_max)
    mz_clean = mz_array[mask]
    int_clean = int_array[mask]
    
    if len(mz_clean) == 0:
        return pd.DataFrame({'bin_mz': bins[:-1], 'intensity': 0.0})
        
    digitized = np.digitize(mz_clean, bins)
    
    # Sum intensities in each bin
    binned_intensities = np.zeros(len(bins) - 1)
    for i, bin_idx in enumerate(digitized):
        # digitize returns index 1..len(bins)-1 usually, we map to 0..len-1
        # indices outside bounds handled by filter above, but digitize bins are 1-based index
        if 0 < bin_idx < len(bins):
            binned_intensities[bin_idx-1] += int_clean[i]
            
    return pd.DataFrame({
        'bin_mz': bins[:-1],
        'intensity': binned_intensities
    })

# ... (Previous functions kept for compatibility) ...

def calculate_correlation(
    intensity1: List[float],
    intensity2: List[float],
    method: str = "pearson"
) -> float:
    """Calculate correlation between two spectra (requires alignment first)."""
    arr1 = np.array(intensity1)
    arr2 = np.array(intensity2)
    
    # Simple length check - in reality, need proper alignment (binning)
    min_len = min(len(arr1), len(arr2))
    if min_len < 2: return 0.0
    
    if method == "pearson":
        corr, _ = stats.pearsonr(arr1[:min_len], arr2[:min_len])
    else:
        corr = 0.0
    return corr

def filter_spectrum_by_intensity(
    mz: List[float],
    intensity: List[float],
    threshold: float = 1.0
) -> Tuple[List[float], List[float]]:
    """Filter noise below absolute or relative threshold."""
    filtered_pairs = [(m, i) for m, i in zip(mz, intensity) if i >= threshold]
    if filtered_pairs:
        filtered_mz, filtered_intensity = zip(*filtered_pairs)
        return list(filtered_mz), list(filtered_intensity)
    return [], []

def format_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare DF for CSV/Excel export."""
    df_export = df.copy()
    for col in df_export.select_dtypes(include=['float64']).columns:
        df_export[col] = df_export[col].round(6)
    for col in df_export.select_dtypes(include=['datetime64']).columns:
        df_export[col] = df_export[col].astype(str)
    return df_export

def calculate_statistics(values: List[float]) -> dict:
    """Basic stats."""
    if not values: return {}
    arr = np.array(values)
    return {
        'count': len(arr),
        'mean': float(np.mean(arr)),
        'sum': float(np.sum(arr)),
        'max': float(np.max(arr)),
        'std': float(np.std(arr))
    }

# --- Smart Search Helpers ---

def get_carbon_count(formula: str) -> Optional[int]:
    """Extract carbon count from formula string (e.g., C8H... -> 8)."""
    if not formula or not isinstance(formula, str):
        return None
    # Match C follow by digits
    match = re.search(r'C(\d+)', formula)
    if match:
        return int(match.group(1))
    return None

def get_compound_family(name: str) -> str:
    """Infer PFAS family from compound name."""
    if not name or not isinstance(name, str):
        return "Other"
    
    n = name.lower()
    # Improved keyword matching
    if 'perfluorocarboxylic' in n or 'pfca' in n: return "PFCA (Carboxylic Acids)"
    # Catch "Perfluoro...oic acid"
    if 'perfluoro' in n and 'oic acid' in n: return "PFCA (Carboxylic Acids)"
    
    if 'perfluorosulfonic' in n or 'pfsa' in n: return "PFSA (Sulfonic Acids)"
    # Catch "Perfluoro...sulfonic acid"
    if 'perfluoro' in n and 'sulfonic acid' in n: return "PFSA (Sulfonic Acids)"
    
    if 'fluorotelomer' in n and 'sulfonate' in n: return "FTS (Fluorotelomer Sulfonates)"
    if 'fts' in n: return "FTS (Fluorotelomer Sulfonates)"
    
    if 'phosphate' in n or 'pap' in n: return "PAPs (Phosphate Esters)"
    if 'sulfonamide' in n or 'fosa' in n: return "FOSA/FOSAA (Sulfonamides)"
    if 'ether' in n: return "PFEther (Ether Acids)"
    
    return "Other"

def filter_dataframe_smart(
    df: pd.DataFrame, 
    family: str = None, 
    carbon_count: int = None,
    functional_group: str = None
) -> pd.DataFrame:
    """Apply specific PFAS Smart Filters."""
    filtered = df.copy()
    
    # 1. Family Filter
    if family and family != "All":
        # We need to compute family column first
        if 'Family' not in filtered.columns:
            filtered['Family'] = filtered['name'].apply(get_compound_family)
        # Handle "PFCA" vs "PFCA (Carboxylic Acids)" mismatch if present
        # Ideally user provides full string from constant
        filtered = filtered[filtered['Family'] == family]
        
    # 2. Carbon Count
    if carbon_count is not None:
        if 'CarbonCount' not in filtered.columns:
            filtered['CarbonCount'] = filtered['formula'].apply(get_carbon_count)
        filtered = filtered[filtered['CarbonCount'] == carbon_count]
        
    # 3. Functional Group (Simple keyword match on desc or name)
    if functional_group and functional_group != "None":
        # Extract the key part, e.g. "-COOH"
        fg_key = functional_group.split(' ')[0]
        # Very rough search in name or formula
        # This is a placeholder for more complex logic if needed
        # Assuming name contains relevant suffix
        pass 
        
    return filtered
