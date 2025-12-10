import streamlit as st
import pandas as pd
import sqlite3
import sys
from pathlib import Path

# Move to root to ensure relative imports work standardly
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import init_page, get_db_path, get_available_table_categories
from utils import database as db
from utils import data_processing as dp

# Page Init
init_page("Table Explorer")

st.markdown('<h1 class="main-header">📊 Table Explorer</h1>', unsafe_allow_html=True)

# Get available tables/views based on current database
TABLE_CATEGORIES = get_available_table_categories()

# Function to get tables for a category
def get_tables_in_category(category_key):
    return TABLE_CATEGORIES.get(category_key, [])

# --- Data Selection Wizard ---
st.markdown("### 🧭 Data Selection Wizard")
st.info("Follow the steps below to systematically explore the DIMSpec database structure.")

# Check if we have any categories available
if not TABLE_CATEGORIES:
    st.error("No tables or views found in the database. Please check your database configuration.")
    st.stop()

# Step 1: Core Selection (Always visible/required)
st.markdown("#### **Step 1: Core Data Analysis (Start Here)**")

# Default to first available table if not set
if "selected_table" not in st.session_state:
    # Get first table from first category
    first_category = list(TABLE_CATEGORIES.keys())[0]
    first_table = TABLE_CATEGORIES[first_category][0]
    st.session_state.selected_table = first_table

# We use columns to create a wizard-like feel
col1, col2 = st.columns([1, 2])

with col1:
    # High level category selection
    selected_category = st.radio(
        "Select Data Level:",
        list(TABLE_CATEGORIES.keys()),
        index=0,
        help="Step 1: Core (Analysis Root) -> Step 2: Reference (Metadata) -> Step 3: Normalization -> Step 4: Relations -> Step 5: Views"
    )

with col2:
    # Specific table selection based on category
    available_tables = get_tables_in_category(selected_category)
    
    # Try to keep selection if valid, else reset
    current_index = 0
    if st.session_state.selected_table in available_tables:
        current_index = available_tables.index(st.session_state.selected_table)
    
    selected_table = st.selectbox(
        f"Select Table from {selected_category.split('.')[1]}:",
        available_tables,
        index=current_index
    )
    st.session_state.selected_table = selected_table

    st.caption(f"Viewing: **{selected_table}**")

st.markdown("---")

# --- Main Data View ---

if 'selected_table' in st.session_state:
    table_name = st.session_state.selected_table
    conn = db.connect_db(get_db_path())
    
    # 1. Get total count
    try:
        total_rows = db.get_table_count(conn, table_name)
    except Exception as e:
        st.error(f"Error loading table: {e}")
        total_rows = 0
        
    # 2. Search & Filter
    col_search, col_limit = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("🔍 Search within table:", placeholder="Type to filter...")
    with col_limit:
        limit = st.selectbox("Rows per page:", [50, 100, 500, 1000], index=0)
        
    # 3. Load Data
    try:
        # Simple data loading with limit
        if search_term:
             # Load a larger chunk for client-side filtering (prototype approach)
             df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 2000", conn)
             # String filter
             mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
             df = df[mask]
             st.caption(f"Showing matches in first 2000 rows.")
        else:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)

        st.dataframe(df, use_container_width=True)
        st.caption(f"Total Rows in DB: {total_rows:,}")
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download CSV",
            csv,
            f"{table_name}.csv",
            "text/csv",
            key='download-csv'
        )
        
    except Exception as e:
        st.error(f"Error querying data: {e}")
        
    # Do not close cached connection
    # conn.close()

else:
    st.info("Please select a table to view.")
