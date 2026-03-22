import sqlite3

conn = sqlite3.connect('backend/sql_app.db')
cursor = conn.cursor()

# Show current values
print("BEFORE:", cursor.execute("SELECT DISTINCT assessment_type FROM marks").fetchall())

# Normalize all assessment_type values to lowercase
cursor.execute("UPDATE marks SET assessment_type = LOWER(assessment_type)")
conn.commit()

print(f"Rows updated: {cursor.rowcount}")
print("AFTER:", cursor.execute("SELECT DISTINCT assessment_type FROM marks").fetchall())

conn.close()
print("Done!")
