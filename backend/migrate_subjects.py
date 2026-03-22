"""
Migration script: Add subject_type, credits to subjects table, and label to marks table.
Also populates subject_type and credits based on the curriculum.
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "sql_app.db")
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# --- Step 1: Add new columns if they don't exist ---
try:
    cursor.execute("ALTER TABLE subjects ADD COLUMN subject_type VARCHAR DEFAULT 'theory'")
    print("Added subject_type column to subjects")
except Exception as e:
    print(f"subject_type column may already exist: {e}")

try:
    cursor.execute("ALTER TABLE subjects ADD COLUMN credits INTEGER DEFAULT 3")
    print("Added credits column to subjects")
except Exception as e:
    print(f"credits column may already exist: {e}")

try:
    cursor.execute("ALTER TABLE marks ADD COLUMN label VARCHAR")
    print("Added label column to marks")
except Exception as e:
    print(f"label column may already exist: {e}")

# --- Step 2: List current subjects ---
cursor.execute("SELECT id, name, code, semester FROM subjects ORDER BY semester, id")
subjects = cursor.fetchall()
print(f"\nFound {len(subjects)} subjects:")
for s in subjects:
    print(f"  ID={s[0]}, Name='{s[1]}', Code='{s[2]}', Sem={s[3]}")

# --- Step 3: Classify subjects by type and credits ---
# Lab subjects have "Lab" or "Workshop" in name
# NPTEL = Open Elective
lab_keywords = ['lab', 'workshop']

for s in subjects:
    sid, name, code, sem = s
    name_lower = name.lower()
    subject_type = 'theory'
    credits = 3  # default for theory

    # Check if it's a lab
    if any(kw in name_lower for kw in lab_keywords):
        subject_type = 'lab'
        credits = 2
    # Check for Open Elective / NPTEL
    elif 'open elective' in name_lower or 'nptel' in name_lower:
        subject_type = 'nptel'
        credits = 3
    # MC (Mandatory Course) subjects - 0 credits
    elif any(kw in name_lower for kw in [
        'design thinking', 'value ethics', 'gender culture',
        'environmental science', 'constitution of india',
        'effective technical communication'
    ]):
        credits = 0
    # Special subjects
    elif 'real-time research' in name_lower or 'societal related' in name_lower:
        credits = 2
    elif 'mini project' in name_lower or 'seminar' in name_lower:
        credits = 2
    elif 'english' in name_lower:
        credits = 2
    # Theory subjects with specific credit values from curriculum
    elif any(kw in name_lower for kw in ['fundamentals of electrical', 'discrete mathematics']):
        credits = 2
    elif 'graphics for engineers' in name_lower:
        credits = 1
    elif 'engineering workshop' in name_lower:
        subject_type = 'lab'
        credits = 1
    # Professional Elective - treated as theory
    elif 'professional elective' in name_lower:
        credits = 3

    cursor.execute("UPDATE subjects SET subject_type=?, credits=? WHERE id=?", (subject_type, credits, sid))
    print(f"  Updated ID={sid} '{name}' -> type={subject_type}, credits={credits}")

connection.commit()

# --- Step 4: Verify ---
print("\n--- Verification ---")
cursor.execute("SELECT id, name, code, semester, subject_type, credits FROM subjects ORDER BY semester, id")
for row in cursor.fetchall():
    print(f"  Sem {row[3]}: [{row[4]}] {row[1]} ({row[2]}) - {row[5]} credits")

connection.close()
print("\nMigration complete!")
