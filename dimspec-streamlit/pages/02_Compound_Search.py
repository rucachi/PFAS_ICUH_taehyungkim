import streamlit as st
import pandas as pd
import sqlite3
import sys
from pathlib import Path

# Move to root to ensure relative imports work standardly
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import init_page, get_db_path, PFAS_FAMILIES, FUNCTIONAL_GROUPS
from utils import database as db
from utils import data_processing as dp

# Page Init
init_page("Compound Search")

st.markdown('<h1 class="main-header">🔍 Compound Search</h1>', unsafe_allow_html=True)
st.caption("Search for PFAS compounds using names, chemical properties, or smart classification filters.")

conn = db.connect_db(get_db_path())

# --- Smart Search Sidebar ---
with st.sidebar:
    st.header("🧠 PFAS Smart Search")
    st.info("Use these filters to narrow down 4,000+ compounds without knowing exact names.")
    
    # 1. Family Filter
    selected_family = st.selectbox(
        "PFAS Family (Class)",
        ["All"] + PFAS_FAMILIES,
        index=0,
        help="Filter by structural family (e.g. PFCA, PFSA)"
    )
    
    # 2. Carbon Chain Length
    use_c_chain = st.checkbox("Filter by Carbon Chain Length")
    carbon_len = 8
    if use_c_chain:
        carbon_len = st.slider("Carbon Number (C#)", min_value=1, max_value=20, value=8)
    
    # 3. m/z Search
    use_mz = st.checkbox("Filter by Exact Mass (m/z)")
    target_mz = 0.0
    mz_tolerance = 0.01
    if use_mz:
        col_mz, col_tol = st.columns(2)
        target_mz = col_mz.number_input("Target m/z", value=413.97, format="%.4f")
        mz_tolerance = col_tol.number_input("Tolerance (Da)", value=0.01, format="%.3f")

    # 4. Functional Group (Placeholder for future expansion)
    # selected_func_group = st.selectbox("Functional Group", ["None"] + FUNCTIONAL_GROUPS)

# --- Main Search Area ---

# Load basic compound data (Cached ideally, but small enough for direct load)
@st.cache_data
def load_all_compounds():
    c = db.connect_db(get_db_path())
    df = pd.read_sql_query("SELECT id, name, formula, fixedmass as exact_mass, additional as description FROM compounds", c)
    # Do not close cached resource
    # c.close()
    return df

df_compounds = load_all_compounds()

# Apply Smart Filters
filtered_df = df_compounds.copy()

# Filter by Family
if selected_family != "All":
    # Helper adds column if missing
    filtered_df = dp.filter_dataframe_smart(filtered_df, family=selected_family)

# Filter by Carbon Count
if use_c_chain:
    filtered_df = dp.filter_dataframe_smart(filtered_df, carbon_count=carbon_len)

# Filter by m/z
if use_mz and target_mz > 0:
    # Ensure exact_mass is numeric
    filtered_df['exact_mass'] = pd.to_numeric(filtered_df['exact_mass'], errors='coerce')
    mask = (filtered_df['exact_mass'] >= target_mz - mz_tolerance) & \
           (filtered_df['exact_mass'] <= target_mz + mz_tolerance)
    filtered_df = filtered_df[mask]

# --- Name Search (Refines Smart Search) ---
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    name_query = st.text_input("Name / ID Search (Refines above filters):", placeholder="e.g. PFOA, DTXSID...")
with search_col2:
    st.text("")
    st.text("")
    # Just a visual spacer

if name_query:
    mask = filtered_df.astype(str).apply(lambda x: x.str.contains(name_query, case=False, na=False)).any(axis=1)
    filtered_df = filtered_df[mask]

# --- Display Results ---

st.markdown(f"### Results ({len(filtered_df)} matches)")

if len(filtered_df) > 0:
    # Display table
    st.dataframe(
        filtered_df[['id', 'name', 'formula', 'exact_mass', 'description']], 
        use_container_width=True,
        hide_index=True
    )
    
    # Detail View
    st.markdown("---")
    st.subheader("📝 Compound Details")
    selected_id_name = st.selectbox("Select compound to view details:", filtered_df['name'].tolist())
    
    if selected_id_name:
        row = filtered_df[filtered_df['name'] == selected_id_name].iloc[0]
        
        det_col1, det_col2 = st.columns(2)
        with det_col1:
            st.metric("Formula", row['formula'])
            st.metric("Exact Mass", f"{row['exact_mass']:.5f}")
            if 'Family' in row:
                st.info(f"**Family**: {row['Family']}")
            if 'CarbonCount' in row:
                st.info(f"**Carbon Length**: C{row['CarbonCount']}")
                
        with det_col2:
            st.markdown(f"**Description**:\n{row.get('description', 'No description available.')}")
            st.markdown(f"**ID**: {row['id']}")

else:
    st.warning("No compounds match your criteria. Try loosening the filters.")



# Do not close cached connection
# conn.close()
