"""Test the ML risk pipeline exactly as the server does."""
import os, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import sqlite3

# Load model files
ML_DIR = os.path.join(os.path.dirname(__file__), "app", "ml_models")
with open(os.path.join(ML_DIR, "xgb_risk_model.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(ML_DIR, "label_encoder.pkl"), "rb") as f:
    encoder = pickle.load(f)
with open(os.path.join(ML_DIR, "feature_columns.pkl"), "rb") as f:
    feature_cols = pickle.load(f)

print(f"Model loaded: {type(model).__name__}")
print(f"Encoder classes: {encoder.classes_}")
print(f"Feature columns: {feature_cols}")

# Test predictions with known values
test_cases = [
    {"attendance_pct": 50.0, "mid1_avg": 0.3, "mid2_avg": 0.2, "assignment_rate": 0.3,
     "prev_sgpa": 4.0, "classes_missed_streak": 5, "low_att_subjects": 4, "failing_subjects": 3},
    {"attendance_pct": 75.0, "mid1_avg": 0.6, "mid2_avg": 0.55, "assignment_rate": 0.7,
     "prev_sgpa": 7.0, "classes_missed_streak": 1, "low_att_subjects": 1, "failing_subjects": 0},
    {"attendance_pct": 95.0, "mid1_avg": 0.9, "mid2_avg": 0.88, "assignment_rate": 0.95,
     "prev_sgpa": 9.5, "classes_missed_streak": 0, "low_att_subjects": 0, "failing_subjects": 0},
]

print("\n=== Direct Model Predictions ===")
for i, tc in enumerate(test_cases):
    df = pd.DataFrame([tc])[feature_cols]
    pred_idx = model.predict(df)[0]
    pred_label = encoder.inverse_transform([pred_idx])[0]
    proba = model.predict_proba(df)[0]
    print(f"  Test {i+1}: prev_sgpa={tc['prev_sgpa']}, att={tc['attendance_pct']}% -> {pred_label} (proba: {dict(zip(encoder.classes_, [f'{p:.2f}' for p in proba]))})")

# Now test with actual DB data
print("\n=== Actual DB Student Predictions ===")
conn = sqlite3.connect("sql_app.db")
c = conn.cursor()
c.execute("SELECT id, enrollment_number FROM students LIMIT 10")
students = c.fetchall()

for sid, enroll in students:
    c.execute("SELECT COUNT(*), SUM(status) FROM attendance WHERE student_id = ?", (sid,))
    att = c.fetchone()
    att_pct = (att[1] / att[0] * 100) if att[0] > 0 else 75.0
    
    c.execute("SELECT score, total FROM marks WHERE student_id = ?", (sid,))
    all_marks = c.fetchall()
    total_scored = sum(r[0] for r in all_marks if r[1] > 0)
    total_max = sum(r[1] for r in all_marks if r[1] > 0)
    prev_sgpa = round(min(10.0, (total_scored / total_max) * 10), 2) if total_max > 0 else 7.0
    
    mid_scores = [(r[0] / r[1]) for r in all_marks if r[1] > 0]
    mid1_avg = float(np.mean(mid_scores)) if mid_scores else 0.65
    
    features = {
        "attendance_pct": round(att_pct, 2),
        "mid1_avg": round(mid1_avg, 4),
        "mid2_avg": 0.0,
        "assignment_rate": 0.75,
        "prev_sgpa": prev_sgpa,
        "classes_missed_streak": 0,
        "low_att_subjects": 0,
        "failing_subjects": 0,
    }
    
    df = pd.DataFrame([features])[feature_cols]
    pred_idx = model.predict(df)[0]
    pred_label = encoder.inverse_transform([pred_idx])[0]
    print(f"  {enroll}: prev_sgpa={prev_sgpa:.2f}, att={att_pct:.1f}% -> {pred_label}")

conn.close()
