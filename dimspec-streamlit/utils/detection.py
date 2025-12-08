
"""
PFAS Detection Core Logic
Handles candidate filtering, similarity calculation, and family prediction.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from utils import data_processing as dp

# --- Constants ---
DEFAULT_MZ_TOLERANCE_PPM = 5.0  # PPM
DEFAULT_RT_MARGIN = 0.5         # Minutes
COSINE_SIMILARITY_THRESHOLD = 0.8  # Threshold for "Unknown" tagging

def calculate_similarity(
    input_fp: np.ndarray,
    target_fp: np.ndarray
) -> float:
    """
    Calculate Cosine Similarity between two fingerprint vectors.
    """
    if len(input_fp) == 0 or len(target_fp) == 0:
        return 0.0
    
    # Ensure they are same length (should be if binned same way)
    if len(input_fp) != len(target_fp):
        # Fallback: truncate to shorter
        min_len = min(len(input_fp), len(target_fp))
        input_fp = input_fp[:min_len]
        target_fp = target_fp[:min_len]
        
    dot_product = np.dot(input_fp, target_fp)
    norm_a = np.linalg.norm(input_fp)
    norm_b = np.linalg.norm(target_fp)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)

def generate_fingerprint_vector(
    mz_list: List[float], 
    intensity_list: List[float],
    mz_min: float = 50.0,
    mz_max: float = 1200.0,
    bin_size: float = 1.0
) -> np.ndarray:
    """
    Wrapper around data_processing binning to return pure numpy array for fast calc.
    """
    # Use existing binning logic
    df_fp = dp.bin_spectrum_fingerprint(
        mz_list, intensity_list, mz_min, mz_max, bin_size
    )
    # Normalize (L2 or Max) - User mentioned Max=1 or Total=1. 
    # Let's use simple Max=1 scaling for now as it's robust for varying concentrations.
    intensities = df_fp['intensity'].values
    max_val = np.max(intensities) if len(intensities) > 0 else 0
    if max_val > 0:
        return intensities / max_val
    return intensities

def filter_candidates_fast(
    library_df: pd.DataFrame,
    input_mz: float,
    input_rt: float = None,
    mz_tolerance_ppm: float = DEFAULT_MZ_TOLERANCE_PPM,
    rt_margin: float = DEFAULT_RT_MARGIN
) -> pd.DataFrame:
    """
    Fast filtering of library based on m/z and RT.
    library_df must have 'precursor_mz' and optionally 'rt_mean'.
    """
    if library_df.empty:
        return library_df
        
    # 1. m/z Filter (PPM)
    # abs(measured - theoretical) / theoretical * 1e6 <= ppm
    # => abs(measured - theoretical) <= theoretical * ppm * 1e-6
    # Note: input_mz is measured. 
    ppm_factor = mz_tolerance_ppm * 1e-6
    
    # Vectorized filtering
    # Pre-calculate bounds
    # Lower bound: theoretical >= input / (1 + ppm) roughly
    # Let's just do direct comparison on the column
    mask_mz = np.abs(library_df['precursor_mz'] - input_mz) <= (library_df['precursor_mz'] * ppm_factor)
    
    filtered = library_df[mask_mz].copy()
    
    # 2. RT Filter (if provided and available in DB)
    if input_rt is not None and 'rt_mean' in filtered.columns and not filtered.empty:
        # Check for null RTs in DB - keep them or drop? usually keep candidates if RT unknown
        # But if rule is strict, we drop. Let's correspond to "physically impossible" -> drop
        # Handle nan: if rt_mean is nan, we might include it (conservative) or exclude.
        # Let's include if nan, filter if value exists.
        rt_vals = filtered['rt_mean']
        mask_rt = (rt_vals.isna()) | (
            (rt_vals >= input_rt - rt_margin) & 
            (rt_vals <= input_rt + rt_margin)
        )
        filtered = filtered[mask_rt]
        
    return filtered

def predict_family_rule_based(
    candidates: pd.DataFrame
) -> Tuple[str, float]:
    """
    Simple heuristic: Vote based on candidates' families.
    Returns (PredictedFamily, Confidence).
    """
    if candidates.empty:
        return "Unknown", 0.0

    # If we have similarity scores, weight by similarity
    # Otherwise just simple count
    if 'similarity' in candidates.columns:
        # Weighted vote
        # Sum similarity per family
        stats = candidates.groupby('Family')['similarity'].sum()
        total_sim = stats.sum()
        if total_sim > 0:
            best_fam = stats.idxmax()
            conf = stats[best_fam] / total_sim
            return best_fam, conf
    else:
        # Simple count
        counts = candidates['Family'].value_counts()
        best_fam = counts.idxmax()
        conf = counts[best_fam] / len(candidates)
        return best_fam, conf
        
    return "Unknown", 0.0

def analyze_peak(
    library_df: pd.DataFrame,
    input_mz: float,
    input_rt: float = None,
    spectrum_mz: List[float] = None,
    spectrum_int: List[float] = None,
    mz_tolerance: float = DEFAULT_MZ_TOLERANCE_PPM,
    rt_margin: float = DEFAULT_RT_MARGIN
) -> Dict[str, Any]:
    """
    Main Pipeline: Filter -> Rank -> Classify -> Tag Unknown
    """
    # 1. Filter Candidates
    candidates = filter_candidates_fast(
        library_df, input_mz, input_rt, mz_tolerance, rt_margin
    )
    
    # 2. Rank by Similarity (if spectrum provided)
    # If no spectrum, rank by mass error
    candidates['similarity'] = 0.0
    candidates['mz_error_ppm'] = np.abs(candidates['precursor_mz'] - input_mz) / candidates['precursor_mz'] * 1e6
    
    if spectrum_mz and spectrum_int and len(spectrum_mz) > 0:
        # Generate input fingerprint
        input_fp = generate_fingerprint_vector(spectrum_mz, spectrum_int)
        
        # Calculate similarity for each candidate
        def calc_sim_row(row):
            if row['fingerprint'] is not None:
                return calculate_similarity(input_fp, row['fingerprint'])
            return 0.0
            
        candidates['similarity'] = candidates.apply(calc_sim_row, axis=1)
        # Sort by similarity desc, then mass error asc
        candidates = candidates.sort_values(by=['similarity', 'mz_error_ppm'], ascending=[False, True])
    else:
        # Sort by mass error only
        candidates = candidates.sort_values(by=['mz_error_ppm'], ascending=True)
        
    # Limit Top-N for downstream classification
    top_n = candidates.head(10) # take top 10 for prediction context
    
    # 3. Classify (Rule Based)
    predicted_class, class_conf = predict_family_rule_based(top_n)
    
    # 4. Unknown Tagging
    # Logic: if best candidate has similarity < threshold (0.8), tag as Unknown.
    # Note: If no spectrum input, similarity is 0.0, so this logic needs care.
    # If no spectrum input, we rely on mass/RT match. If mass match is good (< 5ppm), 
    # we might say "Putative ID" but not "Confirmed".
    
    is_unknown = False
    status_label = "Confirmed Match"
    
    if spectrum_mz:
        # Spectrum mode
        best_sim = top_n.iloc[0]['similarity'] if not top_n.empty else 0.0
        if best_sim < COSINE_SIMILARITY_THRESHOLD:
            is_unknown = True
            status_label = "Unknown Structure"
            predicted_class = "Unknown" if best_sim < 0.5 else predicted_class # Downgrade class prediction if sim is very low
    else:
        # Single peak mode
        if top_n.empty:
            is_unknown = True
            status_label = "No Mass Match"
        else:
            status_label = "Putative Mass Match"
            
    return {
        "predicted_class": predicted_class,
        "class_confidence": class_conf,
        "candidates": top_n, # Return DataFrame
        "is_unknown": is_unknown,
        "status_label": status_label
    }
