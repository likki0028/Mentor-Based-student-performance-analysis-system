"""
COMPLETE DATA PIPELINE
======================
1. Clears all existing students, marks, attendance from local SQLite
2. Generates 65 Section B students with EXACT CGPA distribution
3. Seeds them into the database with marks & attendance
4. Generates ML training data aligned with the same thresholds
5. Trains the XGBoost risk classifier

Run: python complete_data_pipeline.py
"""

import os, sys, json, random, pickle
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# ============================================================================
# STEP 0: Setup paths
# ============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "sql_app.db")
ML_DIR = os.path.join(SCRIPT_DIR, "app", "ml_models")
os.makedirs(ML_DIR, exist_ok=True)

sys.path.insert(0, SCRIPT_DIR)
from scripts.generate_synthetic_data import CURRICULUM, get_indian_name, GENDERS, total_to_grade
from app.core.security import get_password_hash

# ============================================================================
# CONFIG
# ============================================================================
NUM_STUDENTS = 65
SECTION = "B"

# Risk distribution targets (out of 65):
#   At Risk:  ~12 students  (CGPA < 5.5, low attendance)
#   Warning:  ~23 students  (CGPA 5.5-7.5, moderate attendance)  
#   Safe:     ~30 students  (CGPA > 7.5, high attendance)

BUCKETS = {
    "low":  {"count": 15, "min_cgpa": 4.0, "max_cgpa": 5.49, "risk": "At Risk",
             "att_range": (0.45, 0.70), "asgn_range": (0.30, 0.60)},
    "mid_low": {"count": 10, "min_cgpa": 5.5, "max_cgpa": 6.99, "risk": "Warning",
                "att_range": (0.65, 0.80), "asgn_range": (0.50, 0.75)},
    "mid":  {"count": 10, "min_cgpa": 7.0, "max_cgpa": 7.99, "risk": "Warning",
             "att_range": (0.72, 0.85), "asgn_range": (0.60, 0.80)},
    "mid_high": {"count": 15, "min_cgpa": 8.0, "max_cgpa": 8.99, "risk": "Safe",
                 "att_range": (0.80, 0.92), "asgn_range": (0.75, 0.90)},
    "high": {"count": 15, "min_cgpa": 9.0, "max_cgpa": 9.70, "risk": "Safe",
             "att_range": (0.85, 0.98), "asgn_range": (0.85, 0.98)},
}

def clamp(val, mn, mx):
    return max(mn, min(mx, val))

def get_risk_label(cgpa, att_rate):
    """Deterministic risk classification matching ML training data."""
    if cgpa < 5.0 or (cgpa < 5.5 and att_rate < 0.55):
        return "At Risk"
    elif cgpa < 8.5 or (cgpa < 9.0 and att_rate < 0.80):
        return "Warning"
    return "Safe"

# ============================================================================
# STEP 1: Generate 65 students with EXACT bucket counts
# ============================================================================
print("=" * 60)
print("STEP 1: Generating 65 students with perfect CGPA distribution")
print("=" * 60)

generated_students = []
student_idx = 0

for bucket_name, bk in BUCKETS.items():
    filled = 0
    attempts = 0
    while filled < bk["count"]:
        attempts += 1
        if attempts > 5000:
            print(f"  WARNING: Bucket {bucket_name} stuck at {filled}/{bk['count']}")
            break
            
        target_cgpa = round(random.uniform(bk["min_cgpa"], bk["max_cgpa"]), 2)
        target_pct = target_cgpa * 10
        
        # Backlogs only for low CGPA students
        num_backlogs = 0
        if target_cgpa < 5.0:
            num_backlogs = random.randint(3, 8)
        elif target_cgpa < 6.0:
            num_backlogs = random.randint(1, 4)
        elif target_cgpa < 6.5:
            num_backlogs = random.choice([0, 1])
        
        student_idx += 1
        sid = f"23241A67{student_idx:02d}"
        gender = random.choice(GENDERS)
        name = get_indian_name(gender)
        att_rate = round(random.uniform(*bk["att_range"]), 2)
        asgn_rate = round(random.uniform(*bk["asgn_range"]), 2)
        risk = get_risk_label(target_cgpa, att_rate)
        
        student = {
            "student_id": sid, "name": name, "section": SECTION,
            "gender": gender, "risk_profile": risk,
            "semesters": [], "target_cgpa": target_cgpa,
            "backlogs": 0, "overall_attendance_rate": att_rate,
            "overall_assignment_rate": asgn_rate,
        }
        
        # Generate marks for all 6 semesters
        total_credit_pts, total_credits, actual_backlogs = 0, 0, 0
        all_subjects = []
        for s in range(1, 7):
            all_subjects.extend(CURRICULUM[s]["subjects"])
        
        backlog_indices = set()
        if num_backlogs > 0:
            backlog_indices = set(random.sample(range(len(all_subjects)), min(num_backlogs, len(all_subjects))))
        
        subject_global_idx = 0
        
        for sem_num in range(1, 7):
            sem_info = CURRICULUM[sem_num]
            sem_data = {"semester": sem_num, "semester_name": sem_info["name"], "subjects": []}
            sem_credits, sem_grade_pts = 0, 0
            
            for subj in sem_info["subjects"]:
                subj_pct = clamp(target_pct + random.uniform(-8, 8), 0, 100)
                is_backlog = subject_global_idx in backlog_indices
                
                if is_backlog:
                    subj_pct = random.uniform(15, 35)
                else:
                    subj_pct = clamp(subj_pct, 40, 99)
                
                subject_global_idx += 1
                subj_entry = {"name": subj["name"], "code": subj["code"], 
                             "credits": subj["credits"], "type": subj["type"]}
                m = {}
                
                if subj["type"] == "Theory":
                    ext_raw = subj_pct * 0.60
                    int_raw = subj_pct * 0.40
                    if target_cgpa > 9.0 and not is_backlog:
                        ext_raw += 3
                        int_raw += 2
                    m["external"] = int(round(clamp(ext_raw, 0, 59)))
                    m["internal_total"] = int(round(clamp(int_raw, 0, 40)))
                    
                    if is_backlog:
                        m["external"] = random.randint(5, 19)
                        m["internal_total"] = random.randint(5, 15)
                    else:
                        m["external"] = max(21, m["external"])
                        m["internal_total"] = max(14, m["internal_total"])
                    
                    m["total"] = m["external"] + m["internal_total"]
                    
                    # Break down internal
                    avail = m["internal_total"]
                    att_marks = min(5, max(1, int(att_rate * 5)))
                    asgn_marks = min(5, max(1, int(asgn_rate * 5)))
                    m["internal_attendance"] = att_marks
                    m["internal_assignments"] = asgn_marks
                    m["mid_avg"] = max(0, avail - att_marks - asgn_marks)
                    
                    diff = random.randint(-3, 3)
                    m["mid1_total"] = clamp(m["mid_avg"] + diff, 0, 30)
                    m["mid2_total"] = clamp(m["mid_avg"] * 2 - m["mid1_total"], 0, 30)
                    m["mid_avg"] = round((m["mid1_total"] + m["mid2_total"]) / 2)
                    m["mid1_mcq"] = int(round(m["mid1_total"] / 3))
                    m["mid2_mcq"] = int(round(m["mid2_total"] / 3))
                    m["mid1_subjective"] = m["mid1_total"] - m["mid1_mcq"]
                    m["mid2_subjective"] = m["mid2_total"] - m["mid2_mcq"]
                    
                    m["is_pass"] = (m["internal_total"] >= 14 and m["external"] >= 21 and m["total"] >= 40)
                    
                elif subj["type"] == "Lab":
                    ext_raw = subj_pct * 0.60
                    int_raw = subj_pct * 0.40
                    m["external"] = int(round(clamp(ext_raw, 0, 59)))
                    m["internal_total"] = int(round(clamp(int_raw, 0, 40)))
                    
                    if is_backlog:
                        m["external"] = random.randint(5, 19)
                    else:
                        m["external"] = max(21, m["external"])
                        m["internal_total"] = max(14, m["internal_total"])
                    
                    m["total"] = m["external"] + m["internal_total"]
                    m["is_pass"] = (m["internal_total"] >= 14 and m["external"] >= 21 and m["total"] >= 40)
                    
                else:  # Non-Credit
                    avg_raw = subj_pct * 0.40
                    m["mid1"] = int(round(clamp(avg_raw + random.randint(-4, 4), 0, 40)))
                    m["mid2"] = int(round(clamp(avg_raw * 2 - m["mid1"], 0, 40)))
                    m["average"] = round((m["mid1"] + m["mid2"]) / 2)
                    if is_backlog:
                        m["average"] = random.randint(5, 14)
                        m["mid1"] = m["mid2"] = m["average"]
                    else:
                        m["average"] = max(16, m["average"])
                    m["is_pass"] = m["average"] >= 16
                    m["total"] = m["average"]
                
                # Grade point calculation
                if m["is_pass"]:
                    if subj["type"] != "Non-Credit":
                        gp, grade = total_to_grade(m["total"])
                    else:
                        gp, grade = 0, "P"
                else:
                    gp, grade = 0, "F"
                    actual_backlogs += 1
                
                m["grade_point"] = gp
                m["grade"] = grade
                subj_entry["marks"] = m
                sem_data["subjects"].append(subj_entry)
                
                if subj["credits"] > 0 and subj["type"] != "Non-Credit":
                    sem_credits += subj["credits"]
                    sem_grade_pts += gp * subj["credits"]
                    total_credits += subj["credits"]
                    total_credit_pts += gp * subj["credits"]
            
            sem_data["sgpa"] = round(sem_grade_pts / sem_credits, 2) if sem_credits > 0 else 0
            sem_data["total_credits"] = sem_credits
            student["semesters"].append(sem_data)
        
        actual_cgpa = round(total_credit_pts / total_credits, 2) if total_credits > 0 else 0
        
        # Validate this student fits the bucket
        if actual_cgpa < bk["min_cgpa"] or actual_cgpa > bk["max_cgpa"]:
            student_idx -= 1  # Reuse the index
            continue
        
        # Enforce backlog rule: no backlogs for CGPA >= 6.5
        if actual_cgpa >= 6.5 and actual_backlogs > 0:
            student_idx -= 1
            continue
        
        student["cgpa"] = actual_cgpa
        student["backlogs"] = actual_backlogs
        student["risk_profile"] = get_risk_label(actual_cgpa, att_rate)
        generated_students.append(student)
        filled += 1
    
    print(f"  Bucket '{bucket_name}': {filled}/{bk['count']} students (CGPA {bk['min_cgpa']}-{bk['max_cgpa']})")

# Verify counts
cgpas = [s["cgpa"] for s in generated_students]
print(f"\n  Total students: {len(generated_students)}")
print(f"  CGPA < 5.5:  {sum(1 for c in cgpas if c < 5.5)}")
print(f"  CGPA >= 9.0: {sum(1 for c in cgpas if c >= 9.0)}")
print(f"  Backlogs for CGPA >= 6.5: {sum(s['backlogs'] for s in generated_students if s['cgpa'] >= 6.5)}")
risks = [s["risk_profile"] for s in generated_students]
print(f"  At Risk: {risks.count('At Risk')}, Warning: {risks.count('Warning')}, Safe: {risks.count('Safe')}")

# Save JSON
json_path = os.path.join(SCRIPT_DIR, "scripts", "synthetic_students.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(generated_students, f, indent=2)
print(f"\n  Saved to {json_path}")

# ============================================================================
# STEP 2: Seed into local SQLite DB
# ============================================================================
print(f"\n{'=' * 60}")
print("STEP 2: Seeding students into local SQLite database")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Find Section B ID
c.execute("SELECT id FROM sections WHERE name = 'Section B'")
row = c.fetchone()
if row:
    section_b_id = row[0]
else:
    c.execute("INSERT INTO sections (name) VALUES ('Section B')")
    section_b_id = c.lastrowid
    conn.commit()
print(f"  Section B ID: {section_b_id}")

# Find a mentor faculty ID
c.execute("SELECT f.id FROM faculty f JOIN users u ON f.user_id = u.id LIMIT 1")
mentor_row = c.fetchone()
mentor_id = mentor_row[0] if mentor_row else None
print(f"  Mentor ID: {mentor_id}")

# Get subject code -> id mapping
c.execute("SELECT id, code FROM subjects")
db_subjects = {row[1]: row[0] for row in c.fetchall()}
print(f"  Subjects in DB: {len(db_subjects)}")

# Delete ALL existing students, their marks and attendance
c.execute("SELECT id FROM students")
existing_student_ids = [row[0] for row in c.fetchall()]
if existing_student_ids:
    placeholders = ",".join("?" * len(existing_student_ids))
    c.execute(f"DELETE FROM marks WHERE student_id IN ({placeholders})", existing_student_ids)
    c.execute(f"DELETE FROM attendance WHERE student_id IN ({placeholders})", existing_student_ids)
    c.execute(f"DELETE FROM alerts WHERE student_id IN ({placeholders})", existing_student_ids)
    c.execute("DELETE FROM students")
    
    # Also delete student user accounts
    c.execute("SELECT user_id FROM students")  # already deleted, get from users
    c.execute("DELETE FROM users WHERE role = 'STUDENT'")
    
conn.commit()
print(f"  Cleared {len(existing_student_ids)} old students and their data")

# Insert new students
marks_count = 0
att_count = 0
sem_start_dates = {
    1: datetime(2023, 8, 1),
    2: datetime(2024, 1, 1),
    3: datetime(2024, 8, 1),
    4: datetime(2025, 1, 1),
    5: datetime(2025, 8, 1),
    6: datetime(2026, 1, 1),
}

for s_data in generated_students:
    username = s_data["student_id"].lower()
    pwd_hash = get_password_hash("student123")
    email = f"{username}@griet.ac.in"
    
    # Insert user
    c.execute(
        "INSERT INTO users (username, email, hashed_password, role, is_active) VALUES (?, ?, ?, 'STUDENT', 1)",
        (username, email, pwd_hash)
    )
    user_id = c.lastrowid
    
    # Insert student
    c.execute(
        "INSERT INTO students (user_id, enrollment_number, current_semester, section_id, mentor_id, backlogs) VALUES (?, ?, 6, ?, ?, ?)",
        (user_id, s_data["student_id"], section_b_id, mentor_id, s_data["backlogs"])
    )
    student_db_id = c.lastrowid
    
    # Insert marks
    for sem_data in s_data["semesters"]:
        sem_num = sem_data["semester"]
        for subj_data in sem_data["subjects"]:
            code = subj_data["code"]
            sub_id = db_subjects.get(code)
            if not sub_id:
                continue
            
            m = subj_data["marks"]
            
            if subj_data["type"] == "Theory":
                # Mid 1
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'mid_term', ?, 30)",
                         (student_db_id, sub_id, m["mid1_total"]))
                # Mid 2
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'mid_term', ?, 30)",
                         (student_db_id, sub_id, m["mid2_total"]))
                # Internal
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'internal', ?, 40)",
                         (student_db_id, sub_id, m["internal_total"]))
                if sem_num < 6:
                    # External
                    c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'end_term', ?, 60)",
                             (student_db_id, sub_id, m["external"]))
                    marks_count += 1
                marks_count += 3
                
            elif subj_data["type"] == "Lab":
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'internal', ?, 40)",
                         (student_db_id, sub_id, m["internal_total"]))
                if sem_num < 6:
                    c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'end_term', ?, 60)",
                             (student_db_id, sub_id, m["external"]))
                    marks_count += 1
                marks_count += 1
                
            else:  # Non-Credit
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'mid_term', ?, 40)",
                         (student_db_id, sub_id, m["mid1"]))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total) VALUES (?, ?, 'mid_term', ?, 40)",
                         (student_db_id, sub_id, m["mid2"]))
                marks_count += 2
    
    # Insert attendance (15 records per subject in latest semester)
    att_rate = s_data["overall_attendance_rate"]
    latest_sem = s_data["semesters"][-1]
    sem_start = sem_start_dates.get(latest_sem["semester"], datetime(2026, 1, 1))
    
    for subj_data in latest_sem["subjects"]:
        code = subj_data["code"]
        sub_id = db_subjects.get(code)
        if not sub_id:
            continue
        for day in range(15):
            att_date = sem_start + timedelta(days=day * 7 + random.randint(0, 2))
            present = 1 if random.random() < att_rate else 0
            c.execute("INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?)",
                     (student_db_id, sub_id, att_date.strftime("%Y-%m-%d"), present))
            att_count += 1

conn.commit()
print(f"  Inserted {len(generated_students)} students")
print(f"  Created {marks_count} marks records")
print(f"  Created {att_count} attendance records")

# ============================================================================
# STEP 3: Generate ML training data (6000 synthetic records)
# ============================================================================
print(f"\n{'=' * 60}")
print("STEP 3: Generating ML training data (6000 records)")
print("=" * 60)

np.random.seed(42)
NUM_TRAIN = 6000
records = []

for _ in range(NUM_TRAIN):
    ability = np.clip(np.random.beta(4, 2.5), 0.15, 0.98)
    
    attendance_pct = np.clip(ability * 100 + np.random.normal(0, 10), 30, 100)
    mid1_avg = np.clip(ability + np.random.normal(0, 0.12), 0.1, 1.0)
    
    if np.random.random() < 0.3:
        mid2_avg = 0.0
    else:
        mid2_avg = np.clip(ability + np.random.normal(0, 0.13), 0.1, 1.0)
    
    assignment_rate = np.clip(ability * 0.9 + np.random.normal(0, 0.12), 0.0, 1.0)
    prev_sgpa = np.clip(ability * 10 + np.random.normal(0, 0.8), 2.0, 10.0)
    
    classes_missed_streak = int(np.clip(
        np.random.exponential(2) * (1.2 - ability), 0, 20
    ))
    
    num_subjects = np.random.randint(6, 9)
    low_att_subjects = sum(
        1 for _ in range(num_subjects)
        if np.clip(ability * 100 + np.random.normal(0, 12), 30, 100) < 75
    )
    failing_subjects = sum(
        1 for _ in range(num_subjects)
        if np.clip(ability + np.random.normal(0, 0.15), 0, 1) < 0.40
    )
    
    # RISK LABEL — aligned with get_risk_label() above
    # prev_sgpa is effectively the student's "CGPA" in training data
    # attendance_pct / 100 is the attendance rate
    att_ratio = attendance_pct / 100.0
    
    if prev_sgpa < 5.0 or (prev_sgpa < 5.5 and att_ratio < 0.55):
        risk_label = "At Risk"
    elif prev_sgpa < 8.5 or (prev_sgpa < 9.0 and att_ratio < 0.80):
        risk_label = "Warning"
    else:
        risk_label = "Safe"
    
    # Small noise (2%) to prevent trivial overfitting
    if np.random.random() < 0.02:
        risk_label = np.random.choice(["At Risk", "Warning", "Safe"])
    
    records.append({
        "attendance_pct": round(float(attendance_pct), 2),
        "mid1_avg": round(float(mid1_avg), 4),
        "mid2_avg": round(float(mid2_avg), 4),
        "assignment_rate": round(float(assignment_rate), 4),
        "prev_sgpa": round(float(prev_sgpa), 2),
        "classes_missed_streak": int(classes_missed_streak),
        "low_att_subjects": int(low_att_subjects),
        "failing_subjects": int(failing_subjects),
        "risk_label": risk_label,
    })

df = pd.DataFrame(records)
print(f"  Generated {len(df)} training records")
print(f"  Distribution:")
print(f"    {df['risk_label'].value_counts().to_string()}")

# ============================================================================
# STEP 4: Train XGBoost Risk Classifier
# ============================================================================
print(f"\n{'=' * 60}")
print("STEP 4: Training XGBoost Risk Classifier")
print("=" * 60)

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

FEATURE_COLS = [
    "attendance_pct", "mid1_avg", "mid2_avg", "assignment_rate",
    "prev_sgpa", "classes_missed_streak", "low_att_subjects", "failing_subjects"
]

le = LabelEncoder()
le.fit(["At Risk", "Safe", "Warning"])

X = df[FEATURE_COLS]
y = le.transform(df["risk_label"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = XGBClassifier(
    n_estimators=250, max_depth=5, learning_rate=0.1,
    subsample=0.85, colsample_bytree=0.85, num_class=3,
    objective="multi:softprob", eval_metric="mlogloss",
    random_state=42, verbosity=0
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"  Test Accuracy: {acc * 100:.1f}%")
print(f"\n  Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_, digits=3))

# Save model
with open(os.path.join(ML_DIR, "xgb_risk_model.pkl"), "wb") as f:
    pickle.dump(model, f)
with open(os.path.join(ML_DIR, "label_encoder.pkl"), "wb") as f:
    pickle.dump(le, f)
with open(os.path.join(ML_DIR, "feature_columns.pkl"), "wb") as f:
    pickle.dump(FEATURE_COLS, f)
print(f"  Model saved to {ML_DIR}")

# ============================================================================
# STEP 5: Verify risk predictions on actual students
# ============================================================================
print(f"\n{'=' * 60}")
print("STEP 5: Verifying risk predictions on actual DB students")
print("=" * 60)

# For each student, compute the features and predict risk
c.execute("""
    SELECT s.id, s.enrollment_number, s.backlogs
    FROM students s
""")
students_in_db = c.fetchall()

risk_counts = {"At Risk": 0, "Warning": 0, "Safe": 0}
for sid, enroll, backlogs in students_in_db:
    # Get attendance
    c.execute("SELECT COUNT(*), SUM(status) FROM attendance WHERE student_id = ?", (sid,))
    att_row = c.fetchone()
    att_total = att_row[0] or 0
    att_present = att_row[1] or 0
    att_pct = (att_present / att_total * 100) if att_total > 0 else 75.0
    
    # Get marks for mid-term scores
    c.execute("SELECT score, total, assessment_type FROM marks WHERE student_id = ?", (sid,))
    all_marks = c.fetchall()
    
    mid1_scores = [(r[0] / r[1]) for r in all_marks if r[2] == 'mid_term' and r[1] > 0]
    mid1_avg = float(np.mean(mid1_scores)) if mid1_scores else 0.65
    mid2_avg = 0.0  # We store both mid1 and mid2 as 'mid_term', so use 0
    
    # Assignment rate (default since we don't have assignment submissions)
    assignment_rate = 0.75
    
    # Compute prev_sgpa from marks (continuous, not banded)
    total_scored = sum(r[0] for r in all_marks if r[1] > 0)
    total_max = sum(r[1] for r in all_marks if r[1] > 0)
    if total_max > 0:
        pct = (total_scored / total_max) * 100
        prev_sgpa = round(min(10.0, pct / 10.0), 2)
    else:
        prev_sgpa = 7.0
    
    # Count low attendance subjects  
    c.execute("""
        SELECT subject_id, COUNT(*), SUM(status)
        FROM attendance WHERE student_id = ?
        GROUP BY subject_id
    """, (sid,))
    sub_att = c.fetchall()
    low_att = sum(1 for _, total, pres in sub_att if total > 0 and (pres or 0) / total * 100 < 75)
    
    # Failing subjects
    failing = 0
    c.execute("SELECT DISTINCT subject_id FROM marks WHERE student_id = ?", (sid,))
    subj_ids = [r[0] for r in c.fetchall()]
    for sub_id in subj_ids:
        c.execute("SELECT SUM(score), SUM(total) FROM marks WHERE student_id = ? AND subject_id = ?", (sid, sub_id))
        row = c.fetchone()
        if row[1] and row[1] > 0 and (row[0] / row[1] * 100) < 40:
            failing += 1
    
    features_dict = {
        "attendance_pct": round(att_pct, 2),
        "mid1_avg": round(mid1_avg, 4),
        "mid2_avg": mid2_avg,
        "assignment_rate": assignment_rate,
        "prev_sgpa": round(prev_sgpa, 2),
        "classes_missed_streak": 0,
        "low_att_subjects": low_att,
        "failing_subjects": failing,
    }
    
    feat_df = pd.DataFrame([features_dict])[FEATURE_COLS]
    pred_idx = model.predict(feat_df)[0]
    pred_label = le.inverse_transform([pred_idx])[0]
    risk_counts[pred_label] += 1

print(f"  At Risk:  {risk_counts['At Risk']} students")
print(f"  Warning:  {risk_counts['Warning']} students")
print(f"  Safe:     {risk_counts['Safe']} students")

conn.close()

print(f"\n{'=' * 60}")
print("ALL DONE! Data pipeline complete.")
print("=" * 60)
print("Restart the backend server to pick up the new ML model.")
