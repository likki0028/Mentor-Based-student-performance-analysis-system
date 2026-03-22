import sqlite3

conn = sqlite3.connect(r"h:\mini project\vibe\backend\sql_app.db")
c = conn.cursor()

c.execute("""
    SELECT DISTINCT sec.name, st.current_semester 
    FROM sections sec 
    JOIN students st ON st.section_id = sec.id 
    JOIN faculty f ON st.mentor_id = f.id 
    JOIN users u ON f.user_id = u.id 
    WHERE u.username = 'mentor_b'
""")
for r in c.fetchall():
    print(r)

conn.close()
