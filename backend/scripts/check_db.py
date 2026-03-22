"""Check DB record counts."""
import sqlite3, os
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql_app.db")
if not os.path.exists(db_path):
    print(f"DB not found at: {db_path}")
    exit(1)
conn = sqlite3.connect(db_path)
c = conn.cursor()
tables = ["users","students","attendance","marks","assignments","submissions","quizzes","quiz_attempts","doubts","alerts","remarks","materials","syllabus_topics","faculty","sections","subjects","faculty_assignments"]
for t in tables:
    try:
        n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n}")
    except Exception as e:
        print(f"{t}: ERR")
conn.close()
