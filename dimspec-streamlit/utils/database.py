"""
Database utilities for DIMSpec Streamlit application.
Handles all SQLite database operations.
"""

import sqlite3
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
import streamlit as st


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
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None


def get_tables(conn: sqlite3.Connection) -> List[str]:
    """
    Get list of all tables and views in the database.
    
    Args:
        conn: SQLite connection
        
    Returns:
        List of table names
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
    offset: int = 0
) -> pd.DataFrame:
    """
    Get paginated data from a table.
    
    Args:
        conn: SQLite connection
        table_name: Name of table to query
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        
    Returns:
        DataFrame with table data
    """
    query = f"SELECT * FROM {table_name} LIMIT ? OFFSET ?"
    return pd.read_sql_query(query, conn, params=(limit, offset))


def get_table_count(conn: sqlite3.Connection, table_name: str) -> int:
    """
    Get total row count for a table.
    
    Args:
        conn: SQLite connection
        table_name: Name of table
        
    Returns:
        Total number of rows
    """
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
    """
    Search for rows containing search term in any column.
    
    Args:
        conn: SQLite connection
        table_name: Name of table to search
        search_term: Text to search for
        limit: Maximum results to return
        
    Returns:
        DataFrame with matching rows
    """
    # Get column names
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build WHERE clause for searching all text columns
    where_clauses = [f"{col} LIKE ?" for col in columns]
    where_sql = " OR ".join(where_clauses)
    
    query = f"SELECT * FROM {table_name} WHERE {where_sql} LIMIT ?"
    params = [f"%{search_term}%"] * len(columns) + [limit]
    
    return pd.read_sql_query(query, conn, params=params)


def get_compound_by_name(
    conn: sqlite3.Connection, 
    compound_name: str
) -> Optional[pd.DataFrame]:
    """
    Search for compounds by name.
    
    Args:
        conn: SQLite connection
        compound_name: Compound name or partial name
        
    Returns:
        DataFrame with matching compounds
    """
    query = """
    SELECT * FROM compounds 
    WHERE name LIKE ? 
    ORDER BY name
    LIMIT 50
    """
    return pd.read_sql_query(query, conn, params=(f"%{compound_name}%",))


def get_compound_details(
    conn: sqlite3.Connection, 
    compound_id: int
) -> Dict[str, Any]:
    """
    Get detailed information for a specific compound.
    
    Args:
        conn: SQLite connection
        compound_id: Compound ID
        
    Returns:
        Dictionary with compound details
    """
    query = "SELECT * FROM compounds WHERE id = ?"
    cursor = conn.cursor()
    cursor.execute(query, (compound_id,))
    row = cursor.fetchone()
    
    if row:
        return dict(row)
    return None


def get_spectrum_data(
    conn: sqlite3.Connection, 
    peak_id: int
) -> Optional[Tuple[List[float], List[float]]]:
    """
    Get mass spectrum data (m/z and intensity) for a peak.
    
    Args:
        conn: SQLite connection
        peak_id: Peak ID
        
    Returns:
        Tuple of (mz_values, intensity_values) or None
    """
    try:
        # Try to get data from peak_data view or ms_data table
        query = """
        SELECT measured_mz, measured_intensity 
        FROM ms_data 
        WHERE peak_id = ?
        LIMIT 1
        """
        cursor = conn.cursor()
        cursor.execute(query, (peak_id,))
        row = cursor.fetchone()
        
        if row and row[0] and row[1]:
            # Parse the packed spectrum data
            mz_str = row[0]
            intensity_str = row[1]
            
            # Convert string representation to lists
            mz_values = [float(x) for x in mz_str.split()]
            intensity_values = [float(x) for x in intensity_str.split()]
            
            return mz_values, intensity_values
    except Exception as e:
        st.warning(f"Could not retrieve spectrum data: {e}")
    
    return None


def get_view_data(
    conn: sqlite3.Connection,
    view_name: str,
    limit: int = 100
) -> pd.DataFrame:
    """
    Get data from a database view.
    
    Args:
        conn: SQLite connection
        view_name: Name of the view
        limit: Maximum rows to return
        
    Returns:
        DataFrame with view data
    """
    query = f"SELECT * FROM {view_name} LIMIT ?"
    return pd.read_sql_query(query, conn, params=(limit,))


def execute_custom_query(
    conn: sqlite3.Connection,
    query: str,
    params: Optional[Tuple] = None
) -> pd.DataFrame:
    """
    Execute a custom SQL query safely.
    
    Args:
        conn: SQLite connection
        query: SQL query string
        params: Optional query parameters
        
    Returns:
        DataFrame with query results
    """
    try:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        else:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        return pd.DataFrame()
