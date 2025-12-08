"""
Data processing utilities for DIMSpec Streamlit application.
Handles data transformation and analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
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
        method: Normalization method ('max', 'sum', or 'mean')
        
    Returns:
        Tuple of (mz, normalized_intensity)
    """
    intensity_array = np.array(intensity)
    
    if method == "max":
        normalized = (intensity_array / np.max(intensity_array)) * 100
    elif method == "sum":
        normalized = (intensity_array / np.sum(intensity_array)) * 100
    elif method == "mean":
        normalized = (intensity_array / np.mean(intensity_array)) * 100
    else:
        normalized = intensity_array
    
    return mz, normalized.tolist()


def calculate_correlation(
    intensity1: List[float],
    intensity2: List[float],
    method: str = "pearson"
) -> float:
    """
    Calculate correlation between two spectra.
    
    Args:
        intensity1: First intensity array
        intensity2: Second intensity array
        method: Correlation method ('pearson', 'spearman', 'kendall')
        
    Returns:
        Correlation coefficient
    """
    arr1 = np.array(intensity1)
    arr2 = np.array(intensity2)
    
    # Align arrays to same length
    min_len = min(len(arr1), len(arr2))
    arr1 = arr1[:min_len]
    arr2 = arr2[:min_len]
    
    if method == "pearson":
        corr, _ = stats.pearsonr(arr1, arr2)
    elif method == "spearman":
        corr, _ = stats.spearmanr(arr1, arr2)
    elif method == "kendall":
        corr, _ = stats.kendalltau(arr1, arr2)
    else:
        corr = 0.0
    
    return corr


def filter_spectrum_by_intensity(
    mz: List[float],
    intensity: List[float],
    threshold: float = 1.0
) -> Tuple[List[float], List[float]]:
    """
    Filter spectrum by minimum intensity threshold.
    
    Args:
        mz: m/z values
        intensity: Intensity values
        threshold: Minimum relative intensity (%)
        
    Returns:
        Filtered (mz, intensity) tuple
    """
    filtered_pairs = [(m, i) for m, i in zip(mz, intensity) if i >= threshold]
    
    if filtered_pairs:
        filtered_mz, filtered_intensity = zip(*filtered_pairs)
        return list(filtered_mz), list(filtered_intensity)
    else:
        return [], []


def bin_spectrum(
    mz: List[float],
    intensity: List[float],
    bin_size: float = 0.1
) -> Tuple[List[float], List[float]]:
    """
    Bin spectrum data by m/z.
    
    Args:
        mz: m/z values
        intensity: Intensity values
        bin_size: Size of m/z bins
        
    Returns:
        Binned (mz, intensity) tuple
    """
    df = pd.DataFrame({'mz': mz, 'intensity': intensity})
    df['bin'] = (df['mz'] / bin_size).astype(int) * bin_size
    
    binned = df.groupby('bin').agg({
        'mz': 'mean',
        'intensity': 'max'  # Take max intensity in bin
    }).reset_index(drop=True)
    
    return binned['mz'].tolist(), binned['intensity'].tolist()


def calculate_mass_accuracy(
    measured_mz: float,
    theoretical_mz: float,
    unit: str = "ppm"
) -> float:
    """
    Calculate mass accuracy.
    
    Args:
        measured_mz: Measured m/z value
        theoretical_mz: Theoretical m/z value
        unit: Unit of measurement ('ppm' or 'Da')
        
    Returns:
        Mass accuracy value
    """
    if unit == "ppm":
        return ((measured_mz - theoretical_mz) / theoretical_mz) * 1e6
    else:  # Da
        return measured_mz - theoretical_mz


def find_peak_matches(
    mz_query: List[float],
    mz_reference: List[float],
    tolerance_ppm: float = 10.0
) -> List[Tuple[int, int, float]]:
    """
    Find matching peaks between two spectra.
    
    Args:
        mz_query: Query m/z values
        mz_reference: Reference m/z values
        tolerance_ppm: Mass tolerance in ppm
        
    Returns:
        List of (query_idx, ref_idx, error_ppm) tuples
    """
    matches = []
    
    for i, mz_q in enumerate(mz_query):
        for j, mz_r in enumerate(mz_reference):
            error_ppm = abs(calculate_mass_accuracy(mz_q, mz_r, "ppm"))
            
            if error_ppm <= tolerance_ppm:
                matches.append((i, j, error_ppm))
    
    return matches


def format_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format DataFrame for export (CSV/Excel).
    
    Args:
        df: Input DataFrame
        
    Returns:
        Formatted DataFrame
    """
    df_export = df.copy()
    
    # Round float columns
    for col in df_export.select_dtypes(include=['float64']).columns:
        df_export[col] = df_export[col].round(6)
    
    # Convert datetime columns to string
    for col in df_export.select_dtypes(include=['datetime64']).columns:
        df_export[col] = df_export[col].astype(str)
    
    return df_export


def calculate_statistics(values: List[float]) -> dict:
    """
    Calculate basic statistics for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with statistics
    """
    arr = np.array(values)
    
    return {
        'count': len(arr),
        'mean': np.mean(arr),
        'median': np.median(arr),
        'std': np.std(arr),
        'min': np.min(arr),
        'max': np.max(arr),
        'q25': np.percentile(arr, 25),
        'q75': np.percentile(arr, 75)
    }
