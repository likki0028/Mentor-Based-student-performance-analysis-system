"""
XGBoost Risk Prediction Model Trainer (v2)
============================================
Trains an XGBoost Classifier on the synthetic_students_ml.csv (5,000 rows)
to predict student risk level: High, Medium, or Low.

Features (28 total):
  - cgpa, overall_attendance, overall_assignment (3 global features)
  - Per-semester (x5): mid1_avg, mid2_avg, asn_avg, att_avg, sgpa (25 features)

This version includes label noise in the training data to target
realistic 85-90% accuracy instead of unrealistic 99%+.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os


def train_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------------------------
    # 1. Load Data
    # -----------------------------------------------
    csv_path = os.path.join(script_dir, "synthetic_students_ml.csv")
    print("=" * 60)
    print("STEP 1: Loading Data")
    print("=" * 60)
    df = pd.read_csv(csv_path)
    print(f"  Total rows: {len(df)}")
    print(f"  Total columns: {len(df.columns)}")
    print(f"\n  Risk Level Distribution:")
    print(df['risk_level'].value_counts().to_string())

    # -----------------------------------------------
    # 2. Prepare Features and Target
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 2: Preparing Features & Target")
    print("=" * 60)

    # All feature columns (everything except student_id and risk_level)
    feature_cols = [c for c in df.columns if c not in ['student_id', 'risk_level']]
    X = df[feature_cols]
    y = df['risk_level']

    print(f"  Feature columns ({len(feature_cols)}):")
    # Group features for display
    global_feats = [c for c in feature_cols if not c.startswith("sem")]
    print(f"    Global:  {global_feats}")
    for s in range(1, 6):
        sem_feats = [c for c in feature_cols if c.startswith(f"sem{s}_")]
        print(f"    Sem {s}:   {sem_feats}")

    # Encode target labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    print(f"\n  Label mapping: {dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))}")

    # -----------------------------------------------
    # 3. Train/Test Split (80/20)
    # -----------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"  Training set: {len(X_train)} rows")
    print(f"  Test set:     {len(X_test)} rows")

    # -----------------------------------------------
    # 4. Train XGBoost Classifier
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 3: Training XGBoost Classifier")
    print("=" * 60)

    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        max_depth=4,           # Slightly shallower to not overfit noisy labels
        learning_rate=0.08,
        n_estimators=150,
        subsample=0.75,
        colsample_bytree=0.7,
        reg_alpha=0.5,         # More regularization
        reg_lambda=2.0,
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
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n  Overall Accuracy: {accuracy * 100:.2f}%")
    print(f"\n  Classification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_,
        digits=3
    ))

    print(f"  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    cm_labels = label_encoder.classes_
    # Pretty print
    col_width = 14
    header = f"  {'Actual':>{col_width}}"
    for label in cm_labels:
        header += f"  {'Pred ' + label:>{col_width}}"
    print(header)
    for i, label in enumerate(cm_labels):
        row = f"  {label:>{col_width}}"
        for j in range(len(cm_labels)):
            row += f"  {cm[i][j]:>{col_width}}"
        print(row)

    # -----------------------------------------------
    # 6. Cross-Validation (5-fold)
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 5: 5-Fold Cross-Validation")
    print("=" * 60)

    cv_scores = cross_val_score(model, X, y_encoded, cv=5, scoring='accuracy')
    print(f"  Fold Accuracies: {[f'{s*100:.2f}%' for s in cv_scores]}")
    print(f"  Mean CV Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")

    # -----------------------------------------------
    # 7. Feature Importance (Top 10)
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 6: Top 10 Feature Importance")
    print("=" * 60)

    importances = model.feature_importances_
    feat_imp = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    for name, imp in feat_imp[:10]:
        bar = '█' * int(imp * 80)
        print(f"  {name:<25} {imp:.4f}  {bar}")

    # -----------------------------------------------
    # 8. Save Model & Encoder
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 7: Saving Model Files")
    print("=" * 60)

    models_dir = os.path.join(script_dir, "..", "app", "ml_models")
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "xgb_risk_model.pkl")
    encoder_path = os.path.join(models_dir, "label_encoder.pkl")
    # Also save the feature column names so ml_service.py knows the order
    features_path = os.path.join(models_dir, "feature_columns.pkl")

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    with open(encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)

    with open(features_path, 'wb') as f:
        pickle.dump(feature_cols, f)

    print(f"  Model saved:    {os.path.abspath(model_path)}")
    print(f"  Encoder saved:  {os.path.abspath(encoder_path)}")
    print(f"  Features saved: {os.path.abspath(features_path)}")

    # -----------------------------------------------
    # 9. Sample Predictions
    # -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("STEP 8: Sample Predictions")
    print("=" * 60)

    # Use a few actual students from the test set
    test_indices = [0, len(X_test)//3, 2*len(X_test)//3, len(X_test)-1]
    for ti in test_indices:
        row = X_test.iloc[ti:ti+1]
        actual_label = label_encoder.inverse_transform([y_test.iloc[ti] if hasattr(y_test, 'iloc') else y_test[ti]])[0]
        pred = model.predict(row)[0]
        proba = model.predict_proba(row)[0]
        pred_label = label_encoder.inverse_transform([pred])[0]

        cgpa_val = row['cgpa'].values[0]
        att_val = row['overall_attendance'].values[0]
        print(f"\n  CGPA={cgpa_val:.2f}, Attendance={att_val*100:.0f}% | Actual={actual_label} | Predicted={pred_label}")
        conf_str = " | ".join([f"{label_encoder.classes_[i]}={proba[i]*100:.1f}%" for i in range(len(proba))])
        print(f"  Confidence: {conf_str}")

    print(f"\n{'=' * 60}")
    print("ALL DONE! Model is ready for integration.")
    print("=" * 60)


if __name__ == "__main__":
    train_model()
