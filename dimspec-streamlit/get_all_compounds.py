import sqlite3
import pandas as pd
from pathlib import Path

# Database path
DB_PATH = Path("c:/dimspec-main/dimspec-streamlit/data/dimspec_nist_pfas.sqlite")

if DB_PATH.exists():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        # Get total count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM compounds")
        count = cursor.fetchone()[0]
        print(f"Total compounds: {count}")
        
        # Get all names if count is reasonable, otherwise get top 100
        limit = 100
        query = f"SELECT name FROM compounds ORDER BY name LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        
        print(f"\nFirst {limit} Compound Names:")
        for name in df['name']:
            print(f"- {name}")
            
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
else:
    print("Database file not found.")
