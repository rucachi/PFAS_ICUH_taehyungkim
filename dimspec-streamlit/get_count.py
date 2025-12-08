import sqlite3
from pathlib import Path

DB_PATH = Path("c:/dimspec-main/dimspec-streamlit/data/dimspec_nist_pfas.sqlite")
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM compounds")
print(f"COUNT:{cursor.fetchone()[0]}")
conn.close()
