import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from ctgan import CTGAN
import os

# 1. Load data
target_dir = r"h:\mini project\vibe\ppt purpose"
df = pd.read_csv(os.path.join(target_dir, "college_student_management_data.csv"))

# print original length
print(f"Original Kaggle dataset rows: {len(df)}")

# 2. Map Features
np.random.seed(42)

attendance_pct = df['attendance_rate'] * 100
mid1_avg = np.clip(df['avg_course_grade'] / 100 + np.random.normal(0, 0.05, len(df)), 0, 1)
mid2_avg = np.clip(df['avg_course_grade'] / 100 + np.random.normal(0, 0.05, len(df)), 0, 1)
assignment_rate = df['assignment_submission_rate']
prev_sgpa = np.clip(df['GPA'] * 2.5, 0, 10)

classes_missed_streak = np.clip(np.round((1 - df['attendance_rate']) * np.random.randint(5, 20, len(df))), 0, 15).astype(int)
low_att_subjects = np.clip(np.round(df['course_load'] * (1 - df['attendance_rate']) * 1.5), 0, df['course_load']).astype(int)
failing_subjects = np.clip(np.round(df['course_load'] * (1 - df['avg_course_grade']/100)), 0, df['course_load']).astype(int)

credits = df['course_load'] * 3
theory_count = np.round(df['course_load'] * 0.6).astype(int)
lab_count = df['course_load'] - theory_count

risk_map = {'Low': 'Safe', 'Medium': 'Warning', 'High': 'At-Risk'}
Risk_Status = df['risk_level'].map(risk_map)

# Make sure Safe, Warning, At-Risk exist, fallback to Warning if nan
Risk_Status = Risk_Status.fillna("Warning")

sgpa = np.clip(prev_sgpa + (np.random.normal(0, 0.5, len(df))), 0, 10)

mapped_df = pd.DataFrame({
    'attendance_pct': attendance_pct,
    'mid1_avg': mid1_avg,
    'mid2_avg': mid2_avg,
    'assignment_rate': assignment_rate,
    'prev_sgpa': prev_sgpa,
    'classes_missed_streak': classes_missed_streak,
    'low_att_subjects': low_att_subjects,
    'failing_subjects': failing_subjects,
    'credits': credits,
    'theory_count': theory_count,
    'lab_count': lab_count,
    'sgpa': sgpa,
    'Risk_Status': Risk_Status
})

base_file = os.path.join(target_dir, "mapped_base_dataset.csv")
mapped_df.to_csv(base_file, index=False)
print(f"Saved base mapped dataset. Total rows: {len(mapped_df)}")

# 3. SMOTE Generation
risk_encode = {'Safe': 0, 'Warning': 1, 'At-Risk': 2}
mapped_df['Risk_Encoded'] = mapped_df['Risk_Status'].map(risk_encode)

X = mapped_df.drop(['Risk_Status', 'Risk_Encoded'], axis=1)
y = mapped_df['Risk_Encoded']

# Check if any class has very few samples
smote = SMOTE(random_state=42)
try:
    X_res, y_res = smote.fit_resample(X, y)
    smote_df = pd.DataFrame(X_res, columns=X.columns)
    risk_decode = {0: 'Safe', 1: 'Warning', 2: 'At-Risk'}
    smote_df['Risk_Status'] = y_res.map(risk_decode)
    
    # Fix types post SMOTE
    integer_cols = ['classes_missed_streak', 'low_att_subjects', 'failing_subjects', 'credits', 'theory_count', 'lab_count']
    for col in integer_cols:
        smote_df[col] = np.round(smote_df[col]).astype(int)

    smote_file = os.path.join(target_dir, "dataset_smote_balanced.csv")
    smote_df.to_csv(smote_file, index=False)
    print(f"Saved SMOTE generated dataset separately! Total rows: {len(smote_df)}")
except Exception as e:
    print(f"SMOTE generation failed: {e}")

# 4. CTGAN Generation
print("Training CTGAN model... (Doing 15 epochs for reasonable time. This may take 1-2 minutes)")
discrete_columns = ['classes_missed_streak', 'low_att_subjects', 'failing_subjects', 'credits', 'theory_count', 'lab_count', 'Risk_Status']

try:
    ctgan = CTGAN(epochs=15, batch_size=500, verbose=False)
    ctgan.fit(mapped_df.drop(columns=['Risk_Encoded']), discrete_columns)

    print("Generating synthetic data with CGAN/CTGAN...")
    cgan_df = ctgan.sample(5000)

    cgan_file = os.path.join(target_dir, "dataset_cgan_generated.csv")
    cgan_df.to_csv(cgan_file, index=False)
    print(f"Saved CGAN generated dataset separately! Total rows: {len(cgan_df)}")
except Exception as e:
    print(f"CGAN generation failed: {e}")

print("All tasks completed inside ppt purpose folder. Project code untouched.")
