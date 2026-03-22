import sqlite3

db = r'h:\mini project\vibe\backend\sql_app.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# Fix case for assessment_type values in marks table
c.execute("UPDATE marks SET assessment_type = 'MID_TERM' WHERE assessment_type = 'mid_term'")
c.execute("UPDATE marks SET assessment_type = 'END_TERM' WHERE assessment_type = 'end_term'")
c.execute("UPDATE marks SET assessment_type = 'INTERNAL' WHERE assessment_type = 'internal'")

conn.commit()

# Verify
c.execute("SELECT assessment_type, COUNT(*) FROM marks GROUP BY assessment_type")
print(c.fetchall())
conn.close()
print('Done')
