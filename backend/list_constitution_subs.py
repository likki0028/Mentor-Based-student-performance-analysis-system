import sqlite3
c = sqlite3.connect('sql_app.db')
res = c.execute("SELECT id, name, code, subject_type, credits, semester FROM subjects WHERE name LIKE '%Constitution%'").fetchall()
print("Subjects matching 'Constitution':")
for r in res:
    print(f"  ID: {r[0]} | Name: {r[1]} | Code: {r[2]} | Type: {r[3]} | Credits: {r[4]} | Sem: {r[5]}")
