import sqlite3
import pandas as pd
from pathlib import Path

# Database path
DB_PATH = Path("data/dimspec_nist_pfas.sqlite")

if not DB_PATH.exists():
    print(f"Database not found at {DB_PATH}")
    # Try absolute path based on user info
    DB_PATH = Path("c:/dimspec-main/dimspec-streamlit/data/dimspec_nist_pfas.sqlite")

if DB_PATH.exists():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        query = "SELECT name FROM compounds LIMIT 10"
        df = pd.read_sql_query(query, conn)
        print("Example Compound Names:")
        for name in df['name']:
            print(f"- {name}")
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
else:
    print("Database file still not found.")
