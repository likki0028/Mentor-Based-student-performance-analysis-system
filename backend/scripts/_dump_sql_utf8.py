import sqlite3

with open("dump_att_utf8.txt", "w", encoding="utf-8") as f:
    conn = sqlite3.connect(r"h:\mini project\vibe\backend\sql_app.db")
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username='23241a6701';")
    user_row = c.fetchone()
    if not user_row:
        f.write("User not found.\n")
    else:
        user_id = user_row[0]
        c.execute("SELECT id FROM students WHERE user_id=?;", (user_id,))
        student_row = c.fetchone()
        if not student_row:
            f.write("Student not found.\n")
        else:
            student_id = student_row[0]
            f.write(f"User ID: {user_id}, Student ID: {student_id}\n")

            c.execute("SELECT id FROM subjects WHERE name='Automata and Compiler Design';")
            subject_row = c.fetchone()
            subject_id = subject_row[0] if subject_row else None
            f.write(f"Subject ID for Automata: {subject_id}\n")

            if subject_id:
                c.execute("SELECT id, date, status, period FROM attendance WHERE student_id=? AND subject_id=? ORDER BY date DESC, period ASC;", (student_id, subject_id))
                rows = c.fetchall()
                f.write("Attendance Records:\n")
                for r in rows:
                    f.write(str(r) + "\n")

    conn.close()
