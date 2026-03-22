import sqlite3
conn = sqlite3.connect('sql_app.db')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
for t in tables:
    cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
    col_names = [c[1] for c in cols]
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t} ({count} rows): {col_names}")
conn.close()
