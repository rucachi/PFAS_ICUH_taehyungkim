"""
Visualization utilities for DIMSpec Streamlit application.
Creates interactive and static plots for mass spectrometry data.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union

def plot_spectrum(
    mz: Optional[List[float]] = None, 
    intensity: Optional[List[float]] = None,
    title: str = "Mass Spectrum",
    color: str = "blue",
    traces: Optional[List[Dict[str, Any]]] = None
) -> go.Figure:
    """
    Create an interactive mass spectrum plot.
    Supports single spectrum (mz, intensity args) or multiple traces.
    
    Args:
        mz: List of m/z values (primary trace)
        intensity: List of intensity values (primary trace)
        title: Plot title
        color: Primary trace color
        traces: List of dicts {'mz': [], 'intensity': [], 'name': '...', 'color': '...'}
    """
    fig = go.Figure()
    
    # Add primary trace if provided
    if mz is not None and intensity is not None:
        fig.add_trace(go.Bar(
            x=mz,
            y=intensity,
            marker_color=color,
            name="Primary Spectrum",
            hovertemplate='<b>m/z</b>: %{x:.4f}<br><b>Intensity</b>: %{y:.2f}<extra></extra>'
        ))
        
    # Add additional traces (overlays)
    if traces:
        for t in traces:
            trace_color = t.get('color', None) # Let Plotly decide if None, or user specified
            name = t.get('name', 'Overlay')
            
            # Use Scatter/Line for overlays to distinguish from Bar, or Bar with opacity
            # Usually "stick" style is Bar. If we overlay, maybe stems? 
            # Let's use Bar for consistency but control opacity/width if needed.
            # Or use Scatter with vertical lines (Lollipop) for clearer overlay.
            # For now, sticking to Bar with opacity.
            fig.add_trace(go.Bar(
                x=t['mz'],
                y=t['intensity'],
                marker_color=trace_color,
                name=name,
                opacity=0.6 if (mz is not None) else 1.0, # Transparent if overlaying
                hovertemplate=f'<b>{name}</b><br>m/z: %{{x:.4f}}<br>Intensity: %{{y:.2f}}<extra></extra>'
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title="m/z",
        yaxis_title="Intensity",
        hovermode='closest',
        template="plotly_white",
        height=500,
        showlegend=True if traces else False,
        barmode='overlay' # Important for overlaps
    )
    
    return fig

def plot_rt_profile(
    rt_values: List[float],
    intensities: List[float],
    title: str = "Retention Time Profile"
) -> go.Figure:
    """Plot RT vs Intensity (Chromatogram)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rt_values,
        y=intensities,
        mode='lines',
        fill='tozeroy',
        line=dict(color='#2ca02c')
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Retention Time (min)",
        yaxis_title="Intensity",
        template="plotly_white",
        height=400
    )
    return fig

def plot_comparison_butterfly(
    mz1: List[float],
    intensity1: List[float],
    mz2: List[float],
    intensity2: List[float],
    label1: str = "Measured",
    label2: str = "Reference"
) -> go.Figure:
    """Create a butterfly plot comparing two spectra."""
    fig = go.Figure()
    
    # Top spectrum
    fig.add_trace(go.Bar(
        x=mz1,
        y=intensity1,
        marker_color='black',
        name=label1,
        hovertemplate=f'<b>{label1}</b><br>m/z: %{{x:.4f}}<br>Intensity: %{{y:.2f}}<extra></extra>'
    ))
    
    # Bottom spectrum (inverted)
    fig.add_trace(go.Bar(
        x=mz2,
        y=[-i for i in intensity2],
        marker_color='red',
        name=label2,
        hovertemplate=f'<b>{label2}</b><br>m/z: %{{x:.4f}}<br>Intensity: %{{y:.2f}}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{label1} vs {label2}",
        xaxis_title="m/z",
        yaxis_title="Relative Intensity",
        hovermode='closest',
        template="plotly_white",
        height=600,
        barmode='overlay',
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
    )
    return fig

def plot_correlation_scatter(
    x: List[float],
    y: List[float],
    correlation: float,
    xlabel: str = "Measured Intensity",
    ylabel: str = "Reference Intensity"
) -> go.Figure:
    """Scatter plot with trendline."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers',
        marker=dict(size=8, color='blue', opacity=0.6),
        name='Data points'
    ))
    
    if len(x) > 1:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=x, y=p(x), mode='lines',
            line=dict(color='red', dash='dash'),
            name=f'Trend (ρ={correlation:.3f})'
        ))
    
    fig.update_layout(
        title=f"Correlation Plot (ρ = {correlation:.3f})",
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        template="plotly_white",
        height=500
    )
    return fig

def plot_compound_distribution(
    df: pd.DataFrame,
    column: str,
    title: str = "Distribution"
) -> go.Figure:
    """Basic histogram."""
    fig = px.histogram(
        df, x=column, title=title,
        template="plotly_white",
        color_discrete_sequence=['#636EFA']
    )
    fig.update_layout(height=400)
    return fig

def format_compound_info(compound_data: dict) -> str:
    """Format dict to HTML table-like view."""
    html = "<div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px;'>"
    for key, value in compound_data.items():
        if value is not None:
            formatted_key = key.replace('_', ' ').title()
            html += f"<p><b>{formatted_key}:</b> {value}</p>"
    html += "</div>"
    return html
