"""
Database utilities for DIMSpec Streamlit application.
Handles all SQLite database operations with caching and standardized queries.
"""

import sqlite3
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any, Union
import streamlit as st

# ============================================================================
# Core Database Connection
# ============================================================================

@st.cache_resource
def connect_db(db_path: str) -> sqlite3.Connection:
    """
    Create a cached database connection.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        SQLite connection object
    """
    try:
        # check_same_thread=False is needed for Streamlit caching
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        # Cache Invalidated Phase 2
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

# ============================================================================
# Table Operations
# ============================================================================

def get_tables(conn: sqlite3.Connection) -> List[str]:
    """
    Get list of all tables and views in the database.
    """
    query = """
    SELECT name FROM sqlite_master 
    WHERE type IN ('table', 'view') 
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def get_table_data(
    conn: sqlite3.Connection, 
    table_name: str, 
    limit: int = 100, 
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Get paginated data from a table with optional exact match filters.
    
    Args:
        conn: SQLite connection
        table_name: Name of table
        limit: Max rows
        offset: Offset rows
        filters: Dict of col=val for WHERE clause (exact match)
    """
    query = f"SELECT * FROM {table_name}"
    params = []
    
    if filters:
        conditions = []
        for col, val in filters.items():
            conditions.append(f"{col} = ?")
            params.append(val)
        query += " WHERE " + " AND ".join(conditions)
        
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return pd.read_sql_query(query, conn, params=params)


def get_table_count(conn: sqlite3.Connection, table_name: str) -> int:
    """Get total row count for a table."""
    query = f"SELECT COUNT(*) as count FROM {table_name}"
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()[0]


def search_table(
    conn: sqlite3.Connection,
    table_name: str,
    search_term: str,
    limit: int = 100
) -> pd.DataFrame:
    """Search for rows containing search term in any text column."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    where_clauses = [f"CAST({col} AS TEXT) LIKE ?" for col in columns]
    where_sql = " OR ".join(where_clauses)
    
    query = f"SELECT * FROM {table_name} WHERE {where_sql} LIMIT ?"
    params = [f"%{search_term}%"] * len(columns) + [limit]
    
    return pd.read_sql_query(query, conn, params=params)

# ============================================================================
# PFAS & Compound Queries
# ============================================================================

def search_pfas(
    conn: sqlite3.Connection, 
    name: Optional[str] = None,
    mz_range: Optional[Tuple[float, float]] = None,
    rt_range: Optional[Tuple[float, float]] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    Multi-criteria search for PFAS compounds.
    
    Args:
        conn: Database connection
        name: Partial name match
        mz_range: (min_mz, max_mz) for precursor m/z
        rt_range: (min_rt, max_rt) for retention time
        limit: Max results
    """
    # Prefer pfas_summary view if available, otherwise compounds
    # Checks if pfas_summary exists
    tables = get_tables(conn)
    target_table = "pfas_summary" if "pfas_summary" in tables else "compounds"
    
    query = f"SELECT * FROM {target_table}"
    conditions = []
    params = []
    
    if name:
        conditions.append("name LIKE ?")
        params.append(f"%{name}%")
        
    if mz_range and "precursor_mz" in get_column_names(conn, target_table):
        conditions.append("precursor_mz BETWEEN ? AND ?")
        params.extend([mz_range[0], mz_range[1]])
        
    if rt_range and "rt" in get_column_names(conn, target_table):
        conditions.append("rt BETWEEN ? AND ?")
        params.extend([rt_range[0], rt_range[1]])
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " LIMIT ?"
    params.append(limit)
    
    return pd.read_sql_query(query, conn, params=params)

def get_compound_by_name(conn: sqlite3.Connection, name: str) -> pd.DataFrame:
    """Legacy wrapper for simple name search."""
    return search_pfas(conn, name=name)

def get_compound_details(conn: sqlite3.Connection, compound_id: int) -> Dict[str, Any]:
    """Get single compound row as dict."""
    query = "SELECT * FROM compounds WHERE id = ?"
    cursor = conn.cursor()
    cursor.execute(query, (int(compound_id),))
    row = cursor.fetchone()
    return dict(row) if row else None

# ============================================================================
# Spectrum & Peak Queries
# ============================================================================

def get_ms1_by_peak(conn: sqlite3.Connection, peak_id: int) -> Optional[Dict[str, Any]]:
    """
    Get parsed MS1 spectrum data for a specific peak.
    Returns: Dict with mz, intensity lists and metadata.
    """
    query = "SELECT * FROM ms_data WHERE peak_id = ?"
    cursor = conn.cursor()
    cursor.execute(query, (peak_id,))
    row = cursor.fetchone()
    
    if row:
        data = dict(row)
        # Parse packed arrays if they exist
        if 'measured_mz' in data and data['measured_mz']:
            try:
                data['mz'] = [float(x) for x in str(data['measured_mz']).split()]
                data['intensity'] = [float(x) for x in str(data['measured_intensity']).split()]
                del data['measured_mz']
                del data['measured_intensity']
                return data
            except ValueError:
                return None
    return None

def get_ms1_by_pfas(conn: sqlite3.Connection, pfas_id: int) -> pd.DataFrame:
    """
    Get all MS1 peaks associated with a PFAS compound ID.
    Expects a link table or foreign key relatinship.
    For this prototype, assumes there's a view or join possible.
    """
    # Check if we have a way to link pfas to peaks. 
    # Usually compounds.id -> peaks.compound_id (if exists)
    cols = get_column_names(conn, "peaks")
    if "compound_id" in cols:
        query = """
        SELECT p.*, m.measured_mz, m.measured_intensity 
        FROM peaks p
        LEFT JOIN ms_data m ON p.id = m.peak_id
        WHERE p.compound_id = ?
        """
        return pd.read_sql_query(query, conn, params=(pfas_id,))
    else:
        # Fallback: return empty if structure doesn't support it directly yet
        st.warning("Linking structure (compounds->peaks) not found.")
        return pd.DataFrame()

def get_spectrum_data(conn: sqlite3.Connection, peak_id: int) -> Optional[Tuple[List[float], List[float]]]:
    """Legacy wrapper for backward compatibility."""
    data = get_ms1_by_peak(conn, peak_id)
    if data:
        return data['mz'], data['intensity']
    return None

# ============================================================================
# Helpers
# ============================================================================

def get_column_names(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Helper to check column existence."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    except:
        return []

def get_view_data(conn: sqlite3.Connection, view_name: str, limit: int = 100) -> pd.DataFrame:
    return get_table_data(conn, view_name, limit=limit)
