import sqlite3

conn = sqlite3.connect(r"h:\mini project\vibe\backend\sql_app.db")
c = conn.cursor()

# Delete future attendance
c.execute("DELETE FROM attendance WHERE date > '2026-03-24';")
deleted = c.rowcount
print(f"Deleted {deleted} future attendance records.")

conn.commit()
conn.close()
