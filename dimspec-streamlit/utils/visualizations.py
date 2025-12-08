"""
Visualization utilities for DIMSpec Streamlit application.
Creates interactive and static plots for mass spectrometry data.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
import streamlit as st


def plot_spectrum(
    mz: List[float], 
    intensity: List[float],
    title: str = "Mass Spectrum",
    color: str = "blue"
) -> go.Figure:
    """
    Create an interactive mass spectrum plot.
    
    Args:
        mz: List of m/z values
        intensity: List of intensity values
        title: Plot title
        color: Bar color
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=mz,
        y=intensity,
        marker_color=color,
        name="Intensity",
        hovertemplate='<b>m/z</b>: %{x:.4f}<br><b>Intensity</b>: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="m/z",
        yaxis_title="Relative Intensity",
        hovermode='closest',
        template="plotly_white",
        height=500,
        showlegend=False
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
    """
    Create a butterfly plot comparing two spectra.
    
    Args:
        mz1: m/z values for first spectrum
        intensity1: Intensity values for first spectrum
        mz2: m/z values for second spectrum
        intensity2: Intensity values for second spectrum (will be inverted)
        label1: Label for first spectrum
        label2: Label for second spectrum
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Top spectrum (measured)
    fig.add_trace(go.Bar(
        x=mz1,
        y=intensity1,
        marker_color='black',
        name=label1,
        hovertemplate=f'<b>{label1}</b><br>m/z: %{{x:.4f}}<br>Intensity: %{{y:.2f}}<extra></extra>'
    ))
    
    # Bottom spectrum (reference, inverted)
    fig.add_trace(go.Bar(
        x=mz2,
        y=[-i for i in intensity2],  # Invert
        marker_color='red',
        name=label2,
        hovertemplate=f'<b>{label2}</b><br>m/z: %{{x:.4f}}<br>Intensity: %{{y:.2f}}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Spectrum Comparison",
        xaxis_title="m/z",
        yaxis_title="Relative Intensity",
        hovermode='closest',
        template="plotly_white",
        height=600,
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_correlation_scatter(
    x: List[float],
    y: List[float],
    correlation: float,
    xlabel: str = "Measured Intensity",
    ylabel: str = "Reference Intensity"
) -> go.Figure:
    """
    Create a scatter plot showing correlation between two spectra.
    
    Args:
        x: X-axis values
        y: Y-axis values
        correlation: Correlation coefficient
        xlabel: X-axis label
        ylabel: Y-axis label
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=8,
            color='blue',
            opacity=0.6
        ),
        name='Data points',
        hovertemplate='<b>m/z</b>: %{x:.4f}<br><b>Intensity</b>: %{y:.2f}<extra></extra>'
    ))
    
    # Add trendline
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    fig.add_trace(go.Scatter(
        x=x,
        y=p(x),
        mode='lines',
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
    """
    Create a histogram showing distribution of values.
    
    Args:
        df: DataFrame with data
        column: Column name to plot
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    fig = px.histogram(
        df,
        x=column,
        title=title,
        template="plotly_white",
        color_discrete_sequence=['#636EFA']
    )
    
    fig.update_layout(
        xaxis_title=column,
        yaxis_title="Count",
        height=400
    )
    
    return fig


def create_dataframe_display(
    df: pd.DataFrame,
    max_rows: int = 10
) -> pd.DataFrame:
    """
    Prepare DataFrame for display with formatting.
    
    Args:
        df: Input DataFrame
        max_rows: Maximum rows to show initially
        
    Returns:
        Formatted DataFrame
    """
    # Limit decimal places for float columns
    df_display = df.copy()
    
    for col in df_display.select_dtypes(include=['float64']).columns:
        df_display[col] = df_display[col].round(4)
    
    return df_display.head(max_rows)


def format_compound_info(compound_data: dict) -> str:
    """
    Format compound information as HTML.
    
    Args:
        compound_data: Dictionary with compound details
        
    Returns:
        HTML string
    """
    html = "<div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px;'>"
    
    for key, value in compound_data.items():
        if value is not None:
            html += f"<p><b>{key.replace('_', ' ').title()}:</b> {value}</p>"
    
    html += "</div>"
    return html


def create_summary_metrics(
    df: pd.DataFrame,
    metrics: List[str]
) -> dict:
    """
    Calculate summary metrics for display.
    
    Args:
        df: DataFrame
        metrics: List of column names to summarize
        
    Returns:
        Dictionary of metric values
    """
    summary = {}
    
    for metric in metrics:
        if metric in df.columns:
            if df[metric].dtype in ['int64', 'float64']:
                summary[metric] = {
                    'mean': df[metric].mean(),
                    'std': df[metric].std(),
                    'min': df[metric].min(),
                    'max': df[metric].max()
                }
            else:
                summary[metric] = {
                    'unique': df[metric].nunique(),
                    'most_common': df[metric].mode()[0] if not df[metric].mode().empty else None
                }
    
    return summary
