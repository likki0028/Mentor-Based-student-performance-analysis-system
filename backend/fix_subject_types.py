import sqlite3

conn = sqlite3.connect(r"h:\mini project\vibe\backend\sql_app.db")
c = conn.cursor()

# Fix Joy of Computing using Python as NPTEL
c.execute("UPDATE subjects SET subject_type = 'NPTEL' WHERE semester = 6 AND code = 'NPTEL'")
print(f"Updated {c.rowcount} NPTEL subjects")

conn.commit()

c.execute("SELECT name, code, subject_type, credits FROM subjects WHERE semester = 6")
for r in c.fetchall():
    print(r)

conn.close()
