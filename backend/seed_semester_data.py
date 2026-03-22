"""
Seed data for corrected Sem 4, Sem 5 (completed) and Sem 6 (incomplete).
- Sem 4/5: Generate realistic marks and attendance (completed semesters).
- Sem 6: Only Mid-1 marks for theory/PE subjects, 2/5 assignments for theory subjects.
  Labs: No internal exam yet. NPTEL: No mid marks.
"""
import sqlite3
import os
import random
from datetime import date, timedelta

random.seed(42)
db_path = os.path.join(os.path.dirname(__file__), "sql_app.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all students
c.execute("SELECT id FROM students")
student_ids = [row[0] for row in c.fetchall()]
print(f"Found {len(student_ids)} students")

# Get subjects by semester
def get_subjects(semester):
    c.execute("SELECT id, name, subject_type, credits FROM subjects WHERE semester = ?", (semester,))
    return c.fetchall()

def seed_completed_semester(semester):
    """Seed marks and attendance for a completed semester."""
    subjects = get_subjects(semester)
    print(f"\nSeeding Sem {semester} ({len(subjects)} subjects)...")
    
    for sub_id, sub_name, sub_type, credits in subjects:
        if credits == 0:  # MC subjects - just pass/fail
            continue
            
        for sid in student_ids:
            # Attendance: 30-45 classes per subject
            total_classes = random.randint(30, 45)
            for day_offset in range(total_classes):
                d = date(2025, 1 if semester % 2 == 1 else 7, 1) + timedelta(days=day_offset)
                present = random.random() < random.uniform(0.65, 0.95)  # 65-95% attendance
                c.execute(
                    "INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?)",
                    (sid, sub_id, d.isoformat(), present)
                )
            
            if sub_type == 'theory':
                # Mid 1 + Mid 2 + End Term
                mid1 = random.randint(15, 38)
                mid2 = random.randint(15, 38)
                end_term = random.randint(25, 55)
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'mid_1', ?, 40, 'Mid 1')", (sid, sub_id, mid1))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'mid_2', ?, 40, 'Mid 2')", (sid, sub_id, mid2))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'end_term', ?, 60, 'End Term')", (sid, sub_id, end_term))
                # 5 assignments
                for a in range(1, 6):
                    ascore = random.randint(5, 10)
                    c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'assignment', ?, 10, ?)", (sid, sub_id, ascore, f'Assignment {a}'))
            
            elif sub_type == 'lab':
                # Lab internal (40) + Lab external (60)
                lab_int = random.randint(20, 38)
                lab_ext = random.randint(30, 55)
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'lab_internal', ?, 40, 'Lab Internal')", (sid, sub_id, lab_int))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'lab_external', ?, 60, 'Lab External')", (sid, sub_id, lab_ext))
            
            elif sub_type == 'nptel':
                # NPTEL end term only
                nptel_score = random.randint(40, 90)
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'end_term', ?, 100, 'NPTEL Score')", (sid, sub_id, nptel_score))
    
    conn.commit()
    print(f"  Seeded Sem {semester} complete!")

def seed_incomplete_semester_6():
    """Seed Sem 6 with only Mid-1 and 2/5 assignments for theory/PE."""
    subjects = get_subjects(6)
    print(f"\nSeeding Sem 6 (Incomplete - {len(subjects)} subjects)...")
    
    # Create assignments for theory subjects (5 per subject, only 2 with past due dates)
    theory_subjects = [(s[0], s[1]) for s in subjects if s[2] == 'theory' and s[3] > 0]
    
    for sub_id, sub_name in theory_subjects:
        for a_num in range(1, 6):
            if a_num <= 2:
                due = date(2026, 1, 15) + timedelta(days=a_num * 14)  # Past due dates
            else:
                due = date(2026, 4, 1) + timedelta(days=a_num * 10)  # Future due dates
            c.execute(
                "INSERT INTO assignments (title, description, due_date, subject_id) VALUES (?, ?, ?, ?)",
                (f"Assignment {a_num} - {sub_name}", f"Assignment {a_num} for {sub_name}", due.isoformat(), sub_id)
            )
            assign_id = c.lastrowid
            
            # For assignments 1 & 2: Most students submit, some don't
            if a_num <= 2:
                for sid in student_ids:
                    if random.random() < 0.85:  # 85% submit
                        sub_date = due - timedelta(days=random.randint(0, 3))
                        c.execute(
                            "INSERT INTO submissions (assignment_id, student_id, submission_date, grade) VALUES (?, ?, ?, ?)",
                            (assign_id, sid, sub_date.isoformat(), random.randint(5, 10))
                        )
                    # else: no submission = Missing
    
    for sub_id, sub_name, sub_type, credits in subjects:
        if credits == 0:
            continue
        
        for sid in student_ids:
            # Attendance: ~15-20 classes so far (half semester)
            total_classes = random.randint(15, 20)
            for day_offset in range(total_classes):
                d = date(2026, 1, 6) + timedelta(days=day_offset)
                present = random.random() < random.uniform(0.65, 0.95)
                c.execute(
                    "INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?)",
                    (sid, sub_id, d.isoformat(), present)
                )
            
            if sub_type == 'theory':
                # Only Mid 1 completed
                mid1 = random.randint(12, 38)
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'mid_1', ?, 40, 'Mid 1')", (sid, sub_id, mid1))
            
            elif sub_type == 'lab':
                pass  # Lab internal not yet conducted
            
            elif sub_type == 'nptel':
                pass  # NPTEL exam not yet taken
    
    conn.commit()
    print("  Seeded Sem 6 (incomplete) complete!")

# Only seed for semesters that have no data yet
c.execute("SELECT DISTINCT s.semester FROM marks m JOIN subjects s ON m.subject_id = s.id WHERE s.semester IN (4,5,6)")
seeded_sems = set(row[0] for row in c.fetchall())
print(f"Already seeded semesters: {seeded_sems}")

if 4 not in seeded_sems:
    seed_completed_semester(4)
else:
    print("Sem 4 already has data, skipping")

if 5 not in seeded_sems:
    seed_completed_semester(5)
else:
    print("Sem 5 already has data, skipping")

if 6 not in seeded_sems:
    seed_incomplete_semester_6()
else:
    print("Sem 6 already has data, skipping")

# Final summary
print("\n=== DATA SUMMARY ===")
for sem in range(1, 7):
    c.execute("SELECT COUNT(*) FROM marks m JOIN subjects s ON m.subject_id = s.id WHERE s.semester = ?", (sem,))
    marks_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM attendance a JOIN subjects s ON a.subject_id = s.id WHERE s.semester = ?", (sem,))
    att_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM assignments a JOIN subjects s ON a.subject_id = s.id WHERE s.semester = ?", (sem,))
    assign_count = c.fetchone()[0]
    print(f"  Sem {sem}: {marks_count} marks, {att_count} attendance, {assign_count} assignments")

conn.close()
print("\nData seeding complete!")
