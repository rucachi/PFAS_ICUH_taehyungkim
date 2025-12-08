"""
DIMSpec Streamlit Application
Main application file with multi-page interface for PFAS mass spectrometry data exploration.
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Import utilities
from utils.database import (
    connect_db, get_tables, get_table_data, get_table_count,
    search_table, get_compound_by_name, get_compound_details,
    get_spectrum_data, get_view_data
)
from utils.visualizations import (
    plot_spectrum, plot_comparison_butterfly, plot_correlation_scatter,
    plot_compound_distribution, format_compound_info
)
from utils.data_processing import (
    normalize_spectrum, calculate_correlation, filter_spectrum_by_intensity,
    format_for_export, calculate_statistics
)

# Page configuration
st.set_page_config(
    page_title="DIMSpec Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        margin-top: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Database path
DB_PATH = Path(__file__).parent / "data" / "dimspec_nist_pfas.sqlite"

# Alternative paths to try
ALTERNATIVE_PATHS = [
    Path(__file__).parent.parent / "dimspec_nist_pfas.sqlite",
    Path(__file__).parent.parent / "pfas_dimspec.db",
    Path("dimspec_nist_pfas.sqlite"),
    Path("pfas_dimspec.db")
]

# Find database
db_found = False
if DB_PATH.exists():
    db_found = True
else:
    for alt_path in ALTERNATIVE_PATHS:
        if alt_path.exists():
            DB_PATH = alt_path
            db_found = True
            break

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Sidebar navigation
st.sidebar.markdown("# 🔬 DIMSpec Explorer")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Table Explorer", "Compound Search", "Spectrum Viewer", "About"],
    index=["Home", "Table Explorer", "Compound Search", "Spectrum Viewer", "About"].index(st.session_state.current_page)
)
st.session_state.current_page = page

st.sidebar.markdown("---")
st.sidebar.markdown("### Database Info")

if db_found:
    st.sidebar.success(f"✅ Connected")
    st.sidebar.caption(f"📁 {DB_PATH.name}")
else:
    st.sidebar.error("❌ Database not found")
    st.sidebar.caption("Please add database to data/ folder")

# ============================================================================
# HOME PAGE
# ============================================================================
if page == "Home":
    st.markdown('<h1 class="main-header">🔬 DIMSpec Explorer</h1>', unsafe_allow_html=True)
    st.markdown("### Database Infrastructure for Mass Spectrometry - Python Edition")
    
    st.markdown("""
    Welcome to **DIMSpec Explorer**, a Python/Streamlit application for exploring PFAS 
    (Per- and Polyfluoroalkyl Substances) mass spectrometry data.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-box">
        <h3>📊 Table Explorer</h3>
        <p>Browse database tables and views with search and filter capabilities.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
        <h3>🔍 Compound Search</h3>
        <p>Search for PFAS compounds by name or ID and view detailed information.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="info-box">
        <h3>📈 Spectrum Viewer</h3>
        <p>Visualize mass spectra with interactive plots.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    1. Select a page from the sidebar
    2. Explore the PFAS database
    3. View and export data
    
    **Features:**
    - ✅ Interactive data tables
    - ✅ Searchable compound database
    - ✅ Mass spectrum visualization
    - ✅ Export to CSV/Excel
    """)
    
    if db_found:
        st.success("✅ Database loaded successfully! Use the sidebar to navigate.")
    else:
        st.error("""
        ❌ Database not found! 
        
        Please copy `dimspec_nist_pfas.sqlite` or `pfas_dimspec.db` to the `data/` folder.
        """)

# ============================================================================
# TABLE EXPLORER PAGE
# ============================================================================
elif page == "Table Explorer":
    st.markdown('<h1 class="main-header">📊 Table Explorer</h1>', unsafe_allow_html=True)
    
    if not db_found:
        st.error("Database not found. Please check the database path.")
        st.stop()
    
    # Connect to database
    conn = connect_db(str(DB_PATH))
    
    if conn is None:
        st.error("Failed to connect to database.")
        st.stop()
    
    # Get table list
    tables = get_tables(conn)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Select Table")
        selected_table = st.selectbox(
            "Choose a table or view:",
            tables,
            index=0 if tables else None
        )
        
        if selected_table:
            total_rows = get_table_count(conn, selected_table)
            st.info(f"**Total rows:** {total_rows:,}")
    
    with col2:
        if selected_table:
            st.markdown(f"### {selected_table}")
            
            # Search functionality
            search_term = st.text_input("🔍 Search table", placeholder="Enter search term...")
            
            # Pagination
            rows_per_page = st.select_slider(
                "Rows per page",
                options=[10, 25, 50, 100, 500],
                value=25
            )
            
            if search_term:
                df = search_table(conn, selected_table, search_term, limit=rows_per_page)
                st.caption(f"Showing search results for: **{search_term}**")
            else:
                page_num = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=max(1, (total_rows // rows_per_page) + 1),
                    value=1
                )
                offset = (page_num - 1) * rows_per_page
                df = get_table_data(conn, selected_table, limit=rows_per_page, offset=offset)
            
            # Display data
            st.dataframe(df, use_container_width=True, height=500)
            
            # Export functionality
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                csv = format_for_export(df).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"{selected_table}.csv",
                    mime="text/csv"
                )
            
            with col_exp2:
                # Excel export requires openpyxl
                try:
                    from io import BytesIO
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        format_for_export(df).to_excel(writer, index=False, sheet_name=selected_table)
                    
                    st.download_button(
                        label="📥 Download as Excel",
                        data=buffer.getvalue(),
                        file_name=f"{selected_table}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except ImportError:
                    st.caption("Install openpyxl for Excel export")

# ============================================================================
# COMPOUND SEARCH PAGE
# ============================================================================
elif page == "Compound Search":
    st.markdown('<h1 class="main-header">🔍 Compound Search</h1>', unsafe_allow_html=True)
    
    if not db_found:
        st.error("Database not found. Please check the database path.")
        st.stop()
    
    conn = connect_db(str(DB_PATH))
    
    if conn is None:
        st.error("Failed to connect to database.")
        st.stop()
    
    # Search input
    search_query = st.text_input(
        "Enter compound name or partial name:",
        placeholder="e.g., PFOA, PFOS, perfluoro..."
    )
    
    if search_query:
        with st.spinner("Searching..."):
            results = get_compound_by_name(conn, search_query)
        
        if not results.empty:
            st.success(f"Found {len(results)} compound(s)")
            
            # Display results table
            st.dataframe(results, use_container_width=True)
            
            # Select compound for details
            if 'id' in results.columns and 'name' in results.columns:
                compound_options = {
                    f"{row['name']} (ID: {row['id']})": row['id'] 
                    for _, row in results.iterrows()
                }
                
                selected = st.selectbox(
                    "Select a compound to view details:",
                    options=list(compound_options.keys())
                )
                
                if selected:
                    compound_id = compound_options[selected]
                    details = get_compound_details(conn, compound_id)
                    
                    if details:
                        st.markdown("### Compound Details")
                        st.markdown(format_compound_info(details), unsafe_allow_html=True)
        else:
            st.warning("No compounds found matching your search.")
    else:
        st.info("👆 Enter a compound name to search")

# ============================================================================
# SPECTRUM VIEWER PAGE
# ============================================================================
elif page == "Spectrum Viewer":
    st.markdown('<h1 class="main-header">📈 Spectrum Viewer</h1>', unsafe_allow_html=True)
    
    if not db_found:
        st.error("Database not found. Please check the database path.")
        st.stop()
    
    conn = connect_db(str(DB_PATH))
    
    if conn is None:
        st.error("Failed to connect to database.")
        st.stop()
    
    # Get available peaks
    try:
        peaks_df = get_view_data(conn, "peaks", limit=1000)
        
        if not peaks_df.empty and 'id' in peaks_df.columns:
            peak_id = st.selectbox(
                "Select a peak ID:",
                options=peaks_df['id'].tolist(),
                index=0
            )
            
            if peak_id:
                spectrum_data = get_spectrum_data(conn, peak_id)
                
                if spectrum_data:
                    mz, intensity = spectrum_data
                    
                    # Normalize spectrum
                    norm_method = st.radio(
                        "Normalization method:",
                        ["max", "sum", "mean"],
                        horizontal=True
                    )
                    
                    mz_norm, intensity_norm = normalize_spectrum(mz, intensity, method=norm_method)
                    
                    # Plot spectrum
                    fig = plot_spectrum(mz_norm, intensity_norm, title=f"Mass Spectrum (Peak ID: {peak_id})")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Statistics
                    st.markdown("### Spectrum Statistics")
                    stats = calculate_statistics(intensity_norm)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Number of Peaks", stats['count'])
                    col2.metric("Mean Intensity", f"{stats['mean']:.2f}")
                    col3.metric("Max Intensity", f"{stats['max']:.2f}")
                    col4.metric("Std Dev", f"{stats['std']:.2f}")
                    
                else:
                    st.warning("No spectrum data available for this peak.")
        else:
            st.info("No peak data available in the database.")
    except Exception as e:
        st.error(f"Error loading spectrum data: {e}")
        st.info("This feature requires the 'peaks' and 'ms_data' tables in the database.")

# ============================================================================
# ABOUT PAGE
# ============================================================================
elif page == "About":
    st.markdown('<h1 class="main-header">ℹ️ About DIMSpec Explorer</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Database Infrastructure for Mass Spectrometry
    
    **DIMSpec Explorer** is a Python/Streamlit application for exploring PFAS mass spectrometry data.
    This is a prototype implementation of core features from the original R Shiny DIMSpec application.
    
    This application was produced by **(재)국제도시물정보과학연구원** (International Urban Water Information Science Research Institute).
    
    ### Original DIMSpec Project
    
    The original DIMSpec project was developed by the National Institute of Standards and Technology (NIST)
    Chemical Sciences Division to provide a comprehensive portable database toolkit supporting 
    non-targeted analysis of high resolution mass spectrometry experiments.
    
    - **GitHub**: [https://github.com/usnistgov/dimspec](https://github.com/usnistgov/dimspec)
    - **Documentation**: [https://pages.nist.gov/dimspec/docs/](https://pages.nist.gov/dimspec/docs/)
    
    ### Features in This Prototype
    
    - ✅ **Table Explorer**: Browse all database tables and views
    - ✅ **Compound Search**: Search PFAS compounds by name
    - ✅ **Spectrum Viewer**: Visualize mass spectra
    - ✅ **Data Export**: Download data as CSV or Excel
    
    ### Technology Stack
    
    - **Framework**: Streamlit
    - **Database**: SQLite
    - **Visualization**: Plotly
    - **Data Processing**: Pandas, NumPy, SciPy
    
    ### Disclaimer
    
    This is a prototype application focusing on core read-only features. 
    Advanced features such as data upload, quality control workflows, and complex 
    statistical analyses are not included in this version.
    
    ---
    
    **Version**: 1.0.0 (Prototype)  
    **Last Updated**: 2025-11-29
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**DIMSpec Explorer** v1.0.0")
st.sidebar.caption("Python/Streamlit Prototype")
st.sidebar.caption("By (재)국제도시물정보과학연구원")
