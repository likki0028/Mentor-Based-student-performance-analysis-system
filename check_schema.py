import sqlite3

conn = sqlite3.connect('backend/sql_app.db')

with open('schema_output.txt', 'w') as f:
    for table in ['push_subscriptions', 'notifications']:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        f.write(f"=== {table} ===\n")
        for c in cols:
            f.write(f"  {c}\n")
        f.write(f"Total columns: {len(cols)}\n\n")

conn.close()
print("Written to schema_output.txt")
