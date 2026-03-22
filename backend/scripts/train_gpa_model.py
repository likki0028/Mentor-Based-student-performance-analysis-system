"""
Train an XGBoost Regressor to predict semester GPA.

Features:
  1. attendance_pct       — overall attendance (0-100)
  2. mid1_avg             — avg Mid-1 score ratio (0-1)
  3. assignment_rate       — assignment submission rate (0-1)
  4. prev_sgpa            — previous semester SGPA (0-10)
  5. credits              — total semester credits
  6. theory_count         — number of theory subjects
  7. lab_count            — number of lab subjects

Target:
  sgpa (0-10)

Usage:
  python scripts/train_gpa_model.py
"""

import os, sys, pickle
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

np.random.seed(42)

# -------------------------------------------------------------------
# 1. GENERATE SYNTHETIC TRAINING DATA (~5000 students * 5 semesters)
# -------------------------------------------------------------------
NUM_STUDENTS = 1000
SEMESTERS = 5
records = []

for _ in range(NUM_STUDENTS):
    # Base student ability (0.3 = weak, 0.95 = strong)
    ability = np.clip(np.random.beta(5, 2), 0.25, 0.98)

    prev_sgpa = 0.0  # No previous semester for sem 1
    for sem in range(1, SEMESTERS + 1):
        # Attendance correlates with ability
        attendance_pct = np.clip(ability * 100 + np.random.normal(0, 8), 40, 100)

        # Mid-1 average (score ratio 0-1)
        mid1_avg = np.clip(ability + np.random.normal(0, 0.08), 0.15, 1.0)

        # Assignment submission rate
        assignment_rate = np.clip(ability * 0.95 + np.random.normal(0, 0.1), 0.0, 1.0)

        # Credits (realistic: 18-24 per sem)
        credits = np.random.choice([18, 19, 20, 21, 22, 23, 24])

        # Subject mix
        theory_count = np.random.randint(4, 7)
        lab_count = np.random.randint(1, 4)

        # ---- Compute target SGPA ----
        # Weighted combination of features with noise
        raw_gpa = (
            0.30 * mid1_avg * 10 +          # Mid marks are strongest predictor
            0.20 * (attendance_pct / 100) * 10 +  # Attendance matters
            0.15 * assignment_rate * 10 +     # Assignments
            0.20 * (prev_sgpa if prev_sgpa > 0 else ability * 10) +  # Past performance
            0.05 * (theory_count / 6) * 10 +  # Subject mix effect
            np.random.normal(0.3, 0.4)        # Random noise
        )
        sgpa = round(np.clip(raw_gpa, 2.0, 10.0), 2)

        records.append({
            "attendance_pct": round(attendance_pct, 2),
            "mid1_avg": round(mid1_avg, 4),
            "assignment_rate": round(assignment_rate, 4),
            "prev_sgpa": round(prev_sgpa, 2),
            "credits": credits,
            "theory_count": theory_count,
            "lab_count": lab_count,
            "sgpa": sgpa,
        })

        prev_sgpa = sgpa  # Carry forward for next semester

df = pd.DataFrame(records)
print(f"Generated {len(df)} training records")
print(f"\nData statistics:")
print(df.describe().round(3))

# -------------------------------------------------------------------
# 2. TRAIN XGBOOST REGRESSOR
# -------------------------------------------------------------------
FEATURE_COLS = [
    "attendance_pct", "mid1_avg", "assignment_rate",
    "prev_sgpa", "credits", "theory_count", "lab_count"
]

X = df[FEATURE_COLS]
y = df["sgpa"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=0
)

model.fit(X_train, y_train)

# -------------------------------------------------------------------
# 3. EVALUATE
# -------------------------------------------------------------------
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

print(f"\n{'='*50}")
print(f"MODEL EVALUATION")
print(f"{'='*50}")
print(f"Train MAE: {mean_absolute_error(y_train, y_pred_train):.4f}")
print(f"Test  MAE: {mean_absolute_error(y_test, y_pred_test):.4f}")
print(f"Train R²:  {r2_score(y_train, y_pred_train):.4f}")
print(f"Test  R²:  {r2_score(y_test, y_pred_test):.4f}")

# Feature importance
print(f"\nFeature Importances:")
for feat, imp in sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {feat:20s} {imp:.4f}")

# -------------------------------------------------------------------
# 4. SAVE MODEL
# -------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "ml_models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

model_path = os.path.join(OUTPUT_DIR, "xgb_gpa_predictor.pkl")
cols_path = os.path.join(OUTPUT_DIR, "gpa_feature_columns.pkl")

with open(model_path, "wb") as f:
    pickle.dump(model, f)
with open(cols_path, "wb") as f:
    pickle.dump(FEATURE_COLS, f)

print(f"\nModel saved to: {model_path}")
print(f"Feature columns saved to: {cols_path}")
print("DONE ✅")
