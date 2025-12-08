import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("c:/dimspec-main/dimspec-streamlit/data/dimspec_nist_pfas.sqlite")
conn = sqlite3.connect(str(DB_PATH))

# Get all names
df = pd.read_sql_query("SELECT name FROM compounds ORDER BY name", conn)
conn.close()

# Save to file
with open("compound_names.txt", "w", encoding="utf-8") as f:
    for name in df['name']:
        f.write(f"{name}\n")

print(f"Saved {len(df)} names to compound_names.txt")

# Print first 20 for chat
print("\nTop 20 Examples:")
for name in df['name'].head(20):
    print(f"- {name}")
