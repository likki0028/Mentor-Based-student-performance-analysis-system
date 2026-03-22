"""
XGBoost GPA Predictor Trainer
==============================
Trains an XGBoost Regressor to predict a student's next semester SGPA
based on their academic history up to the current semester.

Training data structure:
  Each student with 5 semesters generates 4 training rows:
    - Row 1: Sem 1 features -> predict Sem 2 SGPA
    - Row 2: Sem 1+2 features -> predict Sem 3 SGPA
    - Row 3: Sem 1+2+3 features -> predict Sem 4 SGPA
    - Row 4: Sem 1+2+3+4 features -> predict Sem 5 SGPA

Features per row (variable length, padded with 0 for future semesters):
  - Per completed semester: mid1_avg, mid2_avg, asn_avg, att_avg, sgpa
  - Global: cgpa_so_far, attendance_trend, assignment_trend
  - Meta: completed_semesters (1-4), target_semester (2-5)

Output:
  - ../app/ml_models/xgb_gpa_predictor.pkl
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os
import json


def extract_semester_features(student, up_to_sem):
    """
    Extract features from semesters 1..up_to_sem for a single student.
    Returns a dict with fixed-length feature vector (padded to 5 semesters).
    """
    features = {}
    
    cgpa_points = 0
    cgpa_credits = 0
    all_att = []
    all_asn = []
    
    for sem_num in range(1, 6):  # Always iterate 1-5 for fixed-length features
        prefix = f"sem{sem_num}"
        
        if sem_num <= up_to_sem:
            sem_data = student["semesters"][sem_num - 1]
            
            mid1_scores = []
            mid2_scores = []
            asn_scores = []
            att_scores = []
            
            for subj in sem_data["subjects"]:
                if subj["type"] == "Theory":
                    m = subj["marks"]
                    mid1_scores.append(m["mid1_total"] / 30.0)
                    mid2_scores.append(m["mid2_total"] / 30.0)
                    asn_scores.append(m["internal_assignments"] / 5.0)
                    att_scores.append(m["internal_attendance"] / 5.0)
            
            features[f"{prefix}_mid1_avg"] = round(np.mean(mid1_scores), 3) if mid1_scores else 0
            features[f"{prefix}_mid2_avg"] = round(np.mean(mid2_scores), 3) if mid2_scores else 0
            features[f"{prefix}_asn_avg"] = round(np.mean(asn_scores), 3) if asn_scores else 0
            features[f"{prefix}_att_avg"] = round(np.mean(att_scores), 3) if att_scores else 0
            features[f"{prefix}_sgpa"] = sem_data["sgpa"]
            
            all_att.extend(att_scores)
            all_asn.extend(asn_scores)
            
            # Accumulate CGPA
            cgpa_credits += sem_data["total_credits"]
            cgpa_points += sem_data["sgpa"] * sem_data["total_credits"]
        else:
            # Pad future semesters with 0
            features[f"{prefix}_mid1_avg"] = 0
            features[f"{prefix}_mid2_avg"] = 0
            features[f"{prefix}_asn_avg"] = 0
            features[f"{prefix}_att_avg"] = 0
            features[f"{prefix}_sgpa"] = 0
    
    # Global features
    features["cgpa_so_far"] = round(cgpa_points / cgpa_credits, 2) if cgpa_credits > 0 else 0
    features["avg_attendance"] = round(np.mean(all_att), 3) if all_att else 0
    features["avg_assignment"] = round(np.mean(all_asn), 3) if all_asn else 0
    features["completed_semesters"] = up_to_sem
    
    # Trend features (change from previous semester)
    if up_to_sem >= 2:
        prev_sgpa = student["semesters"][up_to_sem - 2]["sgpa"]
        curr_sgpa = student["semesters"][up_to_sem - 1]["sgpa"]
        features["sgpa_trend"] = round(curr_sgpa - prev_sgpa, 3)
    else:
        features["sgpa_trend"] = 0
    
    return features


def train_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # -----------------------------------------------
    # 1. Load the detailed student JSON (5000 from ML data)
    # -----------------------------------------------
    print("=" * 60)
    print("STEP 1: Generating Training Data from Synthetic Students")
    print("=" * 60)
    
    # We need full semester details, so we'll regenerate from the generation script
    # But to avoid re-running the whole thing, let's use the JSON for the 195 demo 
    # students PLUS generate more on the fly
    
    # Import the generation function
    import sys
    sys.path.insert(0, script_dir)
    from generate_synthetic_data import generate_one_student, SectionTracker, GENDERS
    import random
    
    random.seed(123)  # Different seed for variety
    
    # Reset the tracker
    import generate_synthetic_data
    generate_synthetic_data.tracker = SectionTracker()
    
    # Generate 5000 students with full semester details
    risk_list = ["High"] * 830 + ["Medium"] * 1250 + ["Low"] * 2920
    random.shuffle(risk_list)
    
    training_rows = []
    total_students = 0
    
    for idx, risk in enumerate(risk_list):
        sid = f"GPA{idx+1:05d}"
        student = generate_one_student(sid, f"S{idx+1}", "X", random.choice(GENDERS), risk)
        total_students += 1
        
        # Each student with 5 semesters produces 4 training rows
        # (predict sem 2 from sem 1, sem 3 from sem 1+2, etc.)
        for target_sem in range(2, 6):
            up_to = target_sem - 1
            features = extract_semester_features(student, up_to)
            features["target_semester"] = target_sem
            features["target_sgpa"] = student["semesters"][target_sem - 1]["sgpa"]
            training_rows.append(features)
    
    df = pd.DataFrame(training_rows)
    print(f"  Students generated: {total_students}")
    print(f"  Training rows: {len(df)} (4 rows per student)")
    print(f"  Features: {len(df.columns) - 1} (excluding target_sgpa)")
    print(f"\n  Target SGPA Distribution:")
    print(df['target_sgpa'].describe().round(3).to_string())
    
    # -----------------------------------------------
    # 2. Prepare Features and Target
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 2: Preparing Features & Target")
    print("=" * 60)
    
    feature_cols = [c for c in df.columns if c != 'target_sgpa']
    X = df[feature_cols]
    y = df['target_sgpa']
    
    print(f"  Feature columns ({len(feature_cols)}):")
    sem_feats = [c for c in feature_cols if c.startswith("sem")]
    global_feats = [c for c in feature_cols if not c.startswith("sem")]
    print(f"    Per-semester: {len(sem_feats)} features")
    print(f"    Global: {global_feats}")
    
    # -----------------------------------------------
    # 3. Train/Test Split (80/20)
    # -----------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\n  Training set: {len(X_train)} rows")
    print(f"  Test set:     {len(X_test)} rows")
    
    # -----------------------------------------------
    # 4. Train XGBoost Regressor
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 3: Training XGBoost Regressor")
    print("=" * 60)
    
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        max_depth=5,
        learning_rate=0.08,
        n_estimators=200,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.3,
        reg_lambda=1.5,
        min_child_weight=5,
        seed=42
    )
    
    model.fit(X_train, y_train, verbose=False)
    print("  Training complete!")
    
    # -----------------------------------------------
    # 5. Evaluate on Test Set
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 4: Evaluation Results")
    print("=" * 60)
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n  Mean Absolute Error (MAE):  {mae:.4f} SGPA points")
    print(f"  Root Mean Sq Error (RMSE): {rmse:.4f} SGPA points")
    print(f"  R² Score:                  {r2:.4f} ({r2*100:.2f}%)")
    
    # Custom accuracy: predictions within ±0.5 SGPA of actual
    within_05 = np.mean(np.abs(y_test.values - y_pred) <= 0.5) * 100
    within_1 = np.mean(np.abs(y_test.values - y_pred) <= 1.0) * 100
    within_025 = np.mean(np.abs(y_test.values - y_pred) <= 0.25) * 100
    
    print(f"\n  Prediction Accuracy (tolerance windows):")
    print(f"    Within ±0.25 SGPA: {within_025:.1f}%")
    print(f"    Within ±0.50 SGPA: {within_05:.1f}%")
    print(f"    Within ±1.00 SGPA: {within_1:.1f}%")
    
    # -----------------------------------------------
    # 6. Per-semester prediction quality
    # -----------------------------------------------
    print(f"\n  Per-Semester Prediction Quality:")
    print(f"  {'Target Sem':<12} {'MAE':<10} {'RMSE':<10} {'R²':<10} {'±0.5 Acc':<10}")
    print(f"  {'-'*52}")
    
    for target_sem in range(2, 6):
        mask = X_test['target_semester'] == target_sem
        if mask.sum() > 0:
            sem_y = y_test[mask]
            sem_pred = y_pred[mask]
            sem_mae = mean_absolute_error(sem_y, sem_pred)
            sem_rmse = np.sqrt(mean_squared_error(sem_y, sem_pred))
            sem_r2 = r2_score(sem_y, sem_pred)
            sem_acc = np.mean(np.abs(sem_y.values - sem_pred) <= 0.5) * 100
            print(f"  Sem {target_sem:<7} {sem_mae:<10.4f} {sem_rmse:<10.4f} {sem_r2:<10.4f} {sem_acc:<10.1f}%")
    
    # -----------------------------------------------
    # 7. Cross-Validation (5-fold)
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 5: 5-Fold Cross-Validation")
    print("=" * 60)
    
    cv_r2 = cross_val_score(model, X, y, cv=5, scoring='r2')
    cv_mae = cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')
    print(f"  R² Scores: {[f'{s:.4f}' for s in cv_r2]}")
    print(f"  Mean R²:   {cv_r2.mean():.4f} (+/- {cv_r2.std():.4f})")
    print(f"  Mean MAE:  {-cv_mae.mean():.4f} SGPA points")
    
    # -----------------------------------------------
    # 8. Feature Importance (Top 10)
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 6: Top 10 Feature Importance")
    print("=" * 60)
    
    importances = model.feature_importances_
    feat_imp = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    for name, imp in feat_imp[:10]:
        bar = '#' * int(imp * 80)
        print(f"  {name:<25} {imp:.4f}  {bar}")
    
    # -----------------------------------------------
    # 9. Save Model
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 7: Saving Model Files")
    print("=" * 60)
    
    models_dir = os.path.join(script_dir, "..", "app", "ml_models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "xgb_gpa_predictor.pkl")
    features_path = os.path.join(models_dir, "gpa_feature_columns.pkl")
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(features_path, 'wb') as f:
        pickle.dump(feature_cols, f)
    
    print(f"  Model saved:    {os.path.abspath(model_path)}")
    print(f"  Features saved: {os.path.abspath(features_path)}")
    
    # -----------------------------------------------
    # 10. Sample Predictions
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 8: Sample Predictions")
    print("=" * 60)
    
    # Pick a few test samples from different target semesters
    for target_sem in range(2, 6):
        mask = X_test['target_semester'] == target_sem
        if mask.sum() > 0:
            sample_idx = X_test[mask].index[0]
            sample_x = X_test.loc[[sample_idx]]
            actual = y_test.loc[sample_idx]
            predicted = model.predict(sample_x)[0]
            cgpa = sample_x['cgpa_so_far'].values[0]
            
            print(f"\n  Predicting Sem {target_sem} SGPA (using Sem 1-{target_sem-1} data):")
            print(f"    CGPA so far: {cgpa:.2f}")
            print(f"    Actual SGPA:    {actual:.2f}")
            print(f"    Predicted SGPA: {predicted:.2f}")
            print(f"    Error:          {abs(actual - predicted):.2f} points")
    
    print(f"\n{'=' * 60}")
    print("ALL DONE! GPA Predictor is ready for integration.")
    print("=" * 60)


if __name__ == "__main__":
    train_model()
