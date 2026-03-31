"""Add database indexes to speed up queries on Neon + check row counts."""
import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_5BixMZNfKFO6@ep-muddy-base-a15u2npb-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    # Check row counts
    print("=== ROW COUNTS ===")
    for t in ['users', 'students', 'faculty', 'subjects', 'sections', 'attendance', 'marks', 'alerts', 'assignments', 'materials', 'submissions']:
        try:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            print(f"  {t}: {count:,} rows")
        except:
            print(f"  {t}: table not found")
    
    # Add indexes
    print("\n=== ADDING INDEXES ===")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_subject ON attendance(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_student_subject ON attendance(student_id, subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_marks_subject ON marks(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_marks_student_subject ON marks(student_id, subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_students_user ON students(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_students_mentor ON students(mentor_id)",
        "CREATE INDEX IF NOT EXISTS idx_students_section ON students(section_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_student ON alerts(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_assignments_faculty ON assignments(faculty_id)",
        "CREATE INDEX IF NOT EXISTS idx_assignments_subject ON assignments(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id)",
    ]
    for idx_sql in indexes:
        try:
            conn.execute(text(idx_sql))
            print(f"  OK: {idx_sql.split('idx_')[1].split(' ON')[0]}")
        except Exception as e:
            print(f"  SKIP: {e}")
    conn.commit()
    print("\nDone! Indexes created.")
