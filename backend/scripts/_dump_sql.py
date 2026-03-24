import sqlite3

conn = sqlite3.connect(r"h:\mini project\vibe\backend\sql_app.db")
c = conn.cursor()

# Get User ID
c.execute("SELECT id FROM users WHERE username='23241a6701';")
user_row = c.fetchone()
if not user_row:
    print("User not found.")
else:
    user_id = user_row[0]
    # Get Student ID
    c.execute("SELECT id FROM students WHERE user_id=?;", (user_id,))
    student_row = c.fetchone()
    if not student_row:
        print("Student not found.")
    else:
        student_id = student_row[0]
        print(f"User ID: {user_id}, Student ID: {student_id}")

        # Get Subject ID for "Automata and Compiler Design"
        c.execute("SELECT id FROM subjects WHERE name='Automata and Compiler Design';")
        subject_row = c.fetchone()
        subject_id = subject_row[0] if subject_row else None
        print(f"Subject ID for Automata: {subject_id}")

        # Get Attendance
        if subject_id:
            c.execute("SELECT id, date, status, period FROM attendance WHERE student_id=? AND subject_id=? ORDER BY date DESC, period ASC;", (student_id, subject_id))
            rows = c.fetchall()
            print("Attendance Records:")
            for r in rows:
                print(r)

conn.close()
