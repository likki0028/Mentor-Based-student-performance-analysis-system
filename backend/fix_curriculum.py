"""
Fix Semester 4 & 5 subjects to match curriculum images.
Add Semester 6 subjects.
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "sql_app.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# =============================================
# FIX SEMESTER 4 (II-II) - Replace incorrect subjects
# =============================================
# Current DB has: Probability/Statistics, OS, Computer Networks, Software Eng, Machine Learning
# Correct from curriculum: Computer Organization, Operating Systems, Data Science with R,
#   Full Stack Web Dev, Applied Statistics, FSWD Lab, OS Lab, DS with R Lab,
#   Environmental Science, Effective Technical Comm, Real-time Research Project

sem4_correct = [
    ("Computer Organization", "GR22A2073", 4, "theory", 3),
    ("Operating Systems", "GR22A2074", 4, "theory", 3),
    ("Data Science with R Programming", "GR22A2086", 4, "theory", 3),
    ("Full Stack Web Development", "GR22A2076", 4, "theory", 3),
    ("Applied Statistics for Engineers", "GR22A2006", 4, "theory", 3),
    ("Full Stack Web Development Lab", "GR22A2078", 4, "lab", 2),
    ("Operating Systems Lab", "GR22A2079", 4, "lab", 2),
    ("Data Science with R Programming Lab", "GR22A2087", 4, "lab", 2),
    ("Environmental Science", "GR22A2001", 4, "theory", 0),
    ("Effective Technical Communication", "GR22A2108", 4, "theory", 0),
    ("Real-time Research Project", "GR22A2109", 4, "lab", 2),
]

# =============================================
# FIX SEMESTER 5 (III-I) - Replace incorrect subjects
# =============================================
# Current DB has: AI, Data Vis, Web Technologies, Compiler Design, AI Lab, DV Lab, WT Lab, Constitution
# Correct from curriculum: AI, DWM, Data Vis, PE-I, OE-I, DWM Lab, AI Lab Python, DV Lab

sem5_correct = [
    ("Artificial Intelligence", "GR22A3070", 5, "theory", 3),
    ("Data Warehousing and Data Mining", "GR22A3069", 5, "theory", 3),
    ("Data Visualization", "GR22A3076", 5, "theory", 3),
    ("Professional Elective-I", "GR22A3PE1", 5, "theory", 3),
    ("Open Elective-I", "GR22A3OE1", 5, "nptel", 3),
    ("Data Warehousing and Data Mining Lab", "GR22A3073", 5, "lab", 2),
    ("Artificial Intelligence Lab using Python", "GR22A3074", 5, "lab", 2),
    ("Data Visualization Lab", "GR22A3078", 5, "lab", 2),
]

# =============================================
# ADD SEMESTER 6 (III-II) - Current / Incomplete
# =============================================
sem6_new = [
    ("Machine Learning", "GR22A3140", 6, "theory", 3),
    ("Automata and Compiler Design", "GR22A3115", 6, "theory", 3),
    ("Big Data Analytics", "GR22A3143", 6, "theory", 3),
    ("Professional Elective-II", "GR22A3PE2", 6, "theory", 3),
    ("Open Elective-II", "GR22A3OE2", 6, "nptel", 3),
    ("Machine Learning Lab", "GR22A3142", 6, "lab", 2),
    ("Big Data Analytics Lab", "GR22A3148", 6, "lab", 2),
    ("Mini Project with Seminar", "GR22A3089", 6, "lab", 2),
    ("Constitution of India", "GR22A2003", 6, "theory", 0),
]

# --- Execute ---

# Step 1: Delete old Sem 4 & 5 subjects
print("Deleting old Sem 4 subjects...")
c.execute("SELECT id FROM subjects WHERE semester = 4")
old_sem4_ids = [row[0] for row in c.fetchall()]
for sid in old_sem4_ids:
    c.execute("DELETE FROM marks WHERE subject_id = ?", (sid,))
    c.execute("DELETE FROM attendance WHERE subject_id = ?", (sid,))
    c.execute("DELETE FROM assignments WHERE subject_id = ?", (sid,))
c.execute("DELETE FROM subjects WHERE semester = 4")
print(f"  Removed {len(old_sem4_ids)} old Sem 4 subjects and associated data")

print("Deleting old Sem 5 subjects...")
c.execute("SELECT id FROM subjects WHERE semester = 5")
old_sem5_ids = [row[0] for row in c.fetchall()]
for sid in old_sem5_ids:
    c.execute("DELETE FROM marks WHERE subject_id = ?", (sid,))
    c.execute("DELETE FROM attendance WHERE subject_id = ?", (sid,))
    c.execute("DELETE FROM assignments WHERE subject_id = ?", (sid,))
c.execute("DELETE FROM subjects WHERE semester = 5")
print(f"  Removed {len(old_sem5_ids)} old Sem 5 subjects and associated data")

# Step 2: Insert correct Sem 4
print("\nInserting correct Sem 4 subjects...")
for s in sem4_correct:
    c.execute("INSERT INTO subjects (name, code, semester, subject_type, credits) VALUES (?, ?, ?, ?, ?)", s)
    print(f"  Added: [{s[3]}] {s[0]} ({s[1]}) - {s[4]}cr")

# Step 3: Insert correct Sem 5
print("\nInserting correct Sem 5 subjects...")
for s in sem5_correct:
    c.execute("INSERT INTO subjects (name, code, semester, subject_type, credits) VALUES (?, ?, ?, ?, ?)", s)
    print(f"  Added: [{s[3]}] {s[0]} ({s[1]}) - {s[4]}cr")

# Step 4: Delete existing Sem 6 if any, then insert
print("\nInserting Sem 6 subjects...")
c.execute("DELETE FROM subjects WHERE semester = 6")
for s in sem6_new:
    c.execute("INSERT INTO subjects (name, code, semester, subject_type, credits) VALUES (?, ?, ?, ?, ?)", s)
    print(f"  Added: [{s[3]}] {s[0]} ({s[1]}) - {s[4]}cr")

conn.commit()

# Step 5: Update student current_semester to 6
print("\nUpdating all students to current_semester = 6...")
c.execute("UPDATE students SET current_semester = 6")
print(f"  Updated {c.rowcount} students")

conn.commit()

# --- Final Verification ---
print("\n=== FINAL SUBJECT LIST ===")
c.execute("SELECT id, name, code, semester, subject_type, credits FROM subjects ORDER BY semester, id")
for row in c.fetchall():
    print(f"  Sem {row[3]}: [{row[4]:6s}] {row[1]:50s} ({row[2]:12s}) {row[5]} cr")

conn.close()
print("\nCurriculum fix complete!")
