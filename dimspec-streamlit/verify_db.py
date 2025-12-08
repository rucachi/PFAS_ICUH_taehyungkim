import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Define paths
base_path = Path(__file__).parent
db_paths = [
    base_path / "data" / "dimspec_nist_pfas.sqlite",
]

# Find database
db_path = None
for path in db_paths:
    if path.exists():
        db_path = path
        break

# Redirect output to file with UTF-8 encoding
with open("db_log.txt", "w", encoding="utf-8") as f:
    def log(msg):
        f.write(str(msg) + "\n")
        print(msg) # Still print to console for immediate feedback if possible

    if not db_path:
        log("❌ No database found in data/ folder.")
        sys.exit(1)

    log(f"✅ Found database: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        log(f"\\n📊 Tables found ({len(tables)}):")
        for t in tables:
            log(f"  - {t}")

        # Check 'compounds' table
        if 'compounds' in tables:
            log("\\n🔍 Checking 'compounds' table:")
            cursor.execute("PRAGMA table_info(compounds)")
            cols = [row[1] for row in cursor.fetchall()]
            log(f"  Columns: {cols}")
            
            cursor.execute("SELECT * FROM compounds LIMIT 1")
            row = cursor.fetchone()
            if row:
                log(f"  Sample row: {dict(row)}")
        else:
            log("\\n❌ 'compounds' table NOT found!")

        # Check 'ms_data' table
        if 'ms_data' in tables:
            log("\\n🔍 Checking 'ms_data' table:")
            cursor.execute("PRAGMA table_info(ms_data)")
            cols = [row[1] for row in cursor.fetchall()]
            log(f"  Columns: {cols}")
            
            cursor.execute("SELECT * FROM ms_data LIMIT 1")
            row = cursor.fetchone()
            if row:
                # Truncate long strings for display
                row_dict = dict(row)
                for k, v in row_dict.items():
                    if isinstance(v, str) and len(v) > 50:
                        row_dict[k] = v[:50] + "..."
                log(f"  Sample row: {row_dict}")
        else:
            log("\\n❌ 'ms_data' table NOT found!")

        # Check 'peaks' view/table
        if 'peaks' in tables:
            log("\\n🔍 Checking 'peaks' table/view:")
            cursor.execute("PRAGMA table_info(peaks)")
            cols = [row[1] for row in cursor.fetchall()]
            log(f"  Columns: {cols}")
        else:
            log("\\n⚠️ 'peaks' table/view NOT found (might be okay if not strictly required or named differently)")

    except Exception as e:
        log(f"\\n❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
