"""
Train an XGBoost Classifier for student risk prediction.

3-class classification: Safe, Warning, At Risk

Features:
  1. attendance_pct       — overall attendance (0-100)
  2. mid1_avg             — avg Mid-1 score ratio (0-1)
  3. mid2_avg             — avg Mid-2 score ratio (0-1), 0 if not conducted
  4. assignment_rate      — assignment submission rate (0-1)
  5. prev_sgpa            — previous semester SGPA (0-10)
  6. classes_missed_streak — max consecutive classes missed (0-20)
  7. low_att_subjects     — count of subjects with attendance < 75%
  8. failing_subjects     — count of subjects with marks < 40%

Target: risk_label  (0=Safe, 1=Warning, 2=At Risk)

Usage:
  python scripts/train_risk_model.py
"""

import os, pickle, sys
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.preprocessing import LabelEncoder

np.random.seed(42)

# -------------------------------------------------------------------
# 1. GENERATE SYNTHETIC TRAINING DATA (~6000 students)
# -------------------------------------------------------------------
NUM_STUDENTS = 6000
records = []

for _ in range(NUM_STUDENTS):
    # Base ability (0.2 = very weak, 0.95 = very strong)
    ability = np.clip(np.random.beta(4, 2.5), 0.15, 0.98)

    # Attendance (strongly correlated with ability)
    attendance_pct = np.clip(ability * 100 + np.random.normal(0, 10), 30, 100)

    # Mid-1 average score ratio
    mid1_avg = np.clip(ability + np.random.normal(0, 0.12), 0.1, 1.0)

    # Mid-2 average (slightly different from mid1, 30% chance not conducted yet)
    if np.random.random() < 0.3:
        mid2_avg = 0.0  # Not yet conducted
    else:
        mid2_avg = np.clip(ability + np.random.normal(0, 0.13), 0.1, 1.0)

    # Assignment submission rate
    assignment_rate = np.clip(ability * 0.9 + np.random.normal(0, 0.12), 0.0, 1.0)

    # Previous SGPA
    prev_sgpa = np.clip(ability * 10 + np.random.normal(0, 0.8), 2.0, 10.0)

    # Classes missed streak (weak students miss more consecutively)
    classes_missed_streak = int(np.clip(
        np.random.exponential(2) * (1.2 - ability), 0, 20
    ))

    # Number of subjects with low attendance (out of ~7 subjects)
    num_subjects = np.random.randint(6, 9)
    low_att_subjects = sum(
        1 for _ in range(num_subjects)
        if np.clip(ability * 100 + np.random.normal(0, 12), 30, 100) < 75
    )

    # Number of failing subjects (marks < 40%)
    failing_subjects = sum(
        1 for _ in range(num_subjects)
        if np.clip(ability + np.random.normal(0, 0.15), 0, 1) < 0.40
    )

    # ---- Determine risk label ----
    # Score-based approach (higher score = higher risk)
    risk_score = 0

    # Attendance factor (strongest indicator)
    if attendance_pct < 60:
        risk_score += 4
    elif attendance_pct < 75:
        risk_score += 2
    elif attendance_pct < 85:
        risk_score += 1

    # Marks factor
    marks_avg = mid1_avg if mid2_avg == 0 else (mid1_avg + mid2_avg) / 2
    if marks_avg < 0.35:
        risk_score += 3
    elif marks_avg < 0.50:
        risk_score += 2
    elif marks_avg < 0.60:
        risk_score += 1

    # Assignment factor
    if assignment_rate < 0.40:
        risk_score += 2
    elif assignment_rate < 0.60:
        risk_score += 1

    # Previous performance
    if prev_sgpa < 4.0:
        risk_score += 2
    elif prev_sgpa < 6.0:
        risk_score += 1

    # Streak / failing subjects
    if classes_missed_streak >= 5:
        risk_score += 1
    if low_att_subjects >= 3:
        risk_score += 1
    if failing_subjects >= 2:
        risk_score += 1

    # Add noise to avoid perfect separation
    risk_score += np.random.normal(0, 0.8)

    # Classify
    if risk_score >= 5:
        risk_label = "At Risk"
    elif risk_score >= 2.5:
        risk_label = "Warning"
    else:
        risk_label = "Safe"

    records.append({
        "attendance_pct": round(attendance_pct, 2),
        "mid1_avg": round(mid1_avg, 4),
        "mid2_avg": round(mid2_avg, 4),
        "assignment_rate": round(assignment_rate, 4),
        "prev_sgpa": round(prev_sgpa, 2),
        "classes_missed_streak": classes_missed_streak,
        "low_att_subjects": low_att_subjects,
        "failing_subjects": failing_subjects,
        "risk_label": risk_label
    })

df = pd.DataFrame(records)
print(f"Generated {len(df)} training records")
print(f"\nClass distribution:")
print(df['risk_label'].value_counts().to_string())

# -------------------------------------------------------------------
# 2. ENCODE & SPLIT
# -------------------------------------------------------------------
FEATURE_COLS = [
    "attendance_pct", "mid1_avg", "mid2_avg", "assignment_rate",
    "prev_sgpa", "classes_missed_streak", "low_att_subjects", "failing_subjects"
]

le = LabelEncoder()
le.fit(["At Risk", "Safe", "Warning"])  # Alphabetical order

X = df[FEATURE_COLS]
y = le.transform(df["risk_label"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -------------------------------------------------------------------
# 3. TRAIN XGBOOST CLASSIFIER
# -------------------------------------------------------------------
model = XGBClassifier(
    n_estimators=250,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.85,
    colsample_bytree=0.85,
    num_class=3,
    objective="multi:softprob",
    eval_metric="mlogloss",
    random_state=42,
    verbosity=0
)

model.fit(X_train, y_train)

# -------------------------------------------------------------------
# 4. EVALUATE
# -------------------------------------------------------------------
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

print(f"\n{'='*55}")
print(f"  XGBoost Risk Classifier — Model Evaluation")
print(f"{'='*55}")
print(f"  Training samples: {len(X_train)}")
print(f"  Testing samples:  {len(X_test)}")
print(f"-"*55)
print(f"  Train Accuracy: {accuracy_score(y_train, y_pred_train)*100:.2f}%")
print(f"  Test  Accuracy: {accuracy_score(y_test, y_pred_test)*100:.2f}%")
print(f"  Test  F1 (weighted): {f1_score(y_test, y_pred_test, average='weighted')*100:.2f}%")
print(f"-"*55)

# Detailed classification report
target_names = le.classes_  # ['At Risk', 'Safe', 'Warning']
print("\n  Classification Report (Test Set):")
print(classification_report(y_test, y_pred_test, target_names=target_names, digits=3))

print("  Confusion Matrix (Test Set):")
cm = confusion_matrix(y_test, y_pred_test)
print(f"  {'':15s} Pred:At Risk  Pred:Safe  Pred:Warning")
for i, label in enumerate(target_names):
    print(f"  True:{label:10s} {cm[i][0]:>10d}  {cm[i][1]:>9d}  {cm[i][2]:>11d}")

# Feature importance
print(f"\n  Feature Importances:")
for feat, imp in sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1]):
    bar = "█" * int(imp * 40)
    print(f"    {feat:25s} {imp*100:5.1f}%  {bar}")
print(f"{'='*55}")

# -------------------------------------------------------------------
# 5. SAVE MODEL
# -------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "ml_models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(os.path.join(OUTPUT_DIR, "xgb_risk_model.pkl"), "wb") as f:
    pickle.dump(model, f)
with open(os.path.join(OUTPUT_DIR, "label_encoder.pkl"), "wb") as f:
    pickle.dump(le, f)
with open(os.path.join(OUTPUT_DIR, "feature_columns.pkl"), "wb") as f:
    pickle.dump(FEATURE_COLS, f)

print(f"\nModel saved to: {OUTPUT_DIR}")
print("DONE ✅")
