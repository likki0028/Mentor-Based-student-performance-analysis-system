
import os
import pickle
import logging

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import student as student_model
from ..models import subject as subject_model
from ..models import submission as submission_model
from ..models import assignment as assignment_model

logger = logging.getLogger(__name__)

# ============================================================================
# LOAD MODELS AT MODULE LEVEL (once on startup)
# ============================================================================
_ML_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml_models")

def _load_pickle(filename):
    """Safely load a pickle file from the ml_models directory."""
    path = os.path.join(_ML_MODELS_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    logger.warning(f"ML model file not found: {path}")
    return None

# Risk Classifier
_risk_model = _load_pickle("xgb_risk_model.pkl")
_risk_encoder = _load_pickle("label_encoder.pkl")
_risk_features = _load_pickle("feature_columns.pkl")

# GPA Predictor
_gpa_model = _load_pickle("xgb_gpa_predictor.pkl")
_gpa_features = _load_pickle("gpa_feature_columns.pkl")


# ============================================================================
# HELPER: Extract GPA prediction features from DB
# ============================================================================
def _get_gpa_features(db: Session, student_id: int) -> dict:
    """
    Extract the 7 ML features from the database for GPA prediction.
    Features: attendance_pct, mid1_avg, assignment_rate, prev_sgpa,
              credits, theory_count, lab_count
    """
    student = db.query(student_model.Student).filter(
        student_model.Student.id == student_id
    ).first()
    if not student:
        return None

    current_sem = student.current_semester or 6

    current_subjects = db.query(subject_model.Subject).filter(
        subject_model.Subject.semester == current_sem
    ).all()
    prev_subjects = db.query(subject_model.Subject).filter(
        subject_model.Subject.semester < current_sem
    ).all()

    current_sub_ids = [s.id for s in current_subjects]

    # 1. Attendance percentage
    if current_sub_ids:
        att_total = db.query(func.count(attendance_model.Attendance.id)).filter(
            attendance_model.Attendance.student_id == student_id,
            attendance_model.Attendance.subject_id.in_(current_sub_ids)
        ).scalar() or 0
        att_present = db.query(func.sum(
            func.cast(attendance_model.Attendance.status, Integer)
        )).filter(
            attendance_model.Attendance.student_id == student_id,
            attendance_model.Attendance.subject_id.in_(current_sub_ids)
        ).scalar() or 0
        attendance_pct = (att_present / att_total * 100) if att_total > 0 else 75.0
    else:
        attendance_pct = 75.0

    # 2. Mid-1 average
    marks_records = db.query(marks_model.Marks).filter(
        marks_model.Marks.student_id == student_id,
        marks_model.Marks.subject_id.in_(current_sub_ids)
    ).all() if current_sub_ids else []

    mid1_scores = []
    for m in marks_records:
        atype = m.assessment_type.value.lower() if hasattr(m.assessment_type, 'value') else str(m.assessment_type).lower()
        if atype in ('mid_1', 'mid_term') and m.total > 0:
            mid1_scores.append(m.score / m.total)

    mid1_avg = np.mean(mid1_scores) if mid1_scores else 0.65

    # 3. Assignment submission rate
    assignments = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.subject_id.in_(current_sub_ids)
    ).all() if current_sub_ids else []
    if assignments:
        submitted = db.query(func.count(submission_model.Submission.id)).filter(
            submission_model.Submission.student_id == student_id,
            submission_model.Submission.assignment_id.in_([a.id for a in assignments])
        ).scalar() or 0
        assignment_rate = submitted / len(assignments)
    else:
        assignment_rate = 0.75

    # 4. Previous semester SGPA
    prev_sub_ids = [s.id for s in prev_subjects]
    prev_sgpa = 5.0
    if prev_sub_ids:
        prev_marks = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == student_id,
            marks_model.Marks.subject_id.in_(prev_sub_ids)
        ).all()
        if prev_marks:
            total_credits, total_points = 0, 0
            for sub in prev_subjects:
                sub_marks = [m for m in prev_marks if m.subject_id == sub.id]
                if sub_marks and sub.credits > 0:
                    ts = sum(m.score for m in sub_marks)
                    tm = sum(m.total for m in sub_marks)
                    if tm > 0:
                        pct = (ts / tm) * 100
                        gp = int(round(min(10.0, pct / 10)))
                        total_credits += sub.credits
                        total_points += gp * sub.credits
            if total_credits > 0:
                prev_sgpa = round(total_points / total_credits, 2)

    # 5/6/7. Credits and subject counts
    credits = sum(s.credits for s in current_subjects)
    theory_count = sum(1 for s in current_subjects if s.subject_type and s.subject_type.upper() in ('THEORY', 'NON_CREDIT'))
    lab_count = sum(1 for s in current_subjects if s.subject_type and s.subject_type.upper() == 'LAB')

    return {
        "attendance_pct": round(attendance_pct, 2),
        "mid1_avg": round(float(mid1_avg), 4),
        "assignment_rate": round(float(assignment_rate), 4),
        "prev_sgpa": round(float(prev_sgpa), 2),
        "credits": int(credits),
        "theory_count": int(theory_count),
        "lab_count": int(lab_count),
    }


# ============================================================================
# HELPER: Extract risk classification features from DB
# ============================================================================
def _get_risk_features(db: Session, student_id: int) -> dict:
    """
    Extract 8 features for risk classification.
    Features: attendance_pct, mid1_avg, mid2_avg, assignment_rate,
              prev_sgpa, classes_missed_streak, low_att_subjects, failing_subjects
    """
    student = db.query(student_model.Student).filter(
        student_model.Student.id == student_id
    ).first()
    if not student:
        return None

    current_sem = student.current_semester or 6
    current_subjects = db.query(subject_model.Subject).filter(
        subject_model.Subject.semester == current_sem
    ).all()
    prev_subjects = db.query(subject_model.Subject).filter(
        subject_model.Subject.semester < current_sem
    ).all()
    current_sub_ids = [s.id for s in current_subjects]

    # 1. Overall attendance
    if current_sub_ids:
        att_total = db.query(func.count(attendance_model.Attendance.id)).filter(
            attendance_model.Attendance.student_id == student_id,
            attendance_model.Attendance.subject_id.in_(current_sub_ids)
        ).scalar() or 0
        att_present = db.query(func.sum(
            func.cast(attendance_model.Attendance.status, Integer)
        )).filter(
            attendance_model.Attendance.student_id == student_id,
            attendance_model.Attendance.subject_id.in_(current_sub_ids)
        ).scalar() or 0
        attendance_pct = (att_present / att_total * 100) if att_total > 0 else 75.0
    else:
        attendance_pct = 75.0

    # 2 & 3. Mid marks
    marks_records = db.query(marks_model.Marks).filter(
        marks_model.Marks.student_id == student_id,
        marks_model.Marks.subject_id.in_(current_sub_ids)
    ).all() if current_sub_ids else []

    mid1_scores, mid2_scores = [], []
    for m in marks_records:
        atype = m.assessment_type.value.lower() if hasattr(m.assessment_type, 'value') else str(m.assessment_type).lower()
        if m.total > 0:
            if atype in ('mid_1', 'mid_term'):
                mid1_scores.append(m.score / m.total)
            elif atype == 'mid_2':
                mid2_scores.append(m.score / m.total)

    mid1_avg = float(np.mean(mid1_scores)) if mid1_scores else 0.65
    mid2_avg = float(np.mean(mid2_scores)) if mid2_scores else 0.0

    # 4. Assignment rate
    assignments = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.subject_id.in_(current_sub_ids)
    ).all() if current_sub_ids else []
    if assignments:
        submitted = db.query(func.count(submission_model.Submission.id)).filter(
            submission_model.Submission.student_id == student_id,
            submission_model.Submission.assignment_id.in_([a.id for a in assignments])
        ).scalar() or 0
        assignment_rate = submitted / len(assignments)
    else:
        assignment_rate = 0.75

    # 5. Previous SGPA
    prev_sub_ids = [s.id for s in prev_subjects]
    prev_sgpa = 7.0
    if prev_sub_ids:
        prev_marks = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == student_id,
            marks_model.Marks.subject_id.in_(prev_sub_ids)
        ).all()
        if prev_marks:
            total_credits, total_points = 0, 0
            for sub in prev_subjects:
                sub_marks = [m for m in prev_marks if m.subject_id == sub.id]
                if sub_marks and sub.credits > 0:
                    ts = sum(m.score for m in sub_marks)
                    tm = sum(m.total for m in sub_marks)
                    if tm > 0:
                        gp = int(round(min(10.0, (ts / tm) * 10)))
                        total_credits += sub.credits
                        total_points += gp * sub.credits
            if total_credits > 0:
                prev_sgpa = round(total_points / total_credits, 2)

    # 6. Classes missed streak
    att_records = db.query(attendance_model.Attendance).filter(
        attendance_model.Attendance.student_id == student_id,
        attendance_model.Attendance.subject_id.in_(current_sub_ids)
    ).order_by(attendance_model.Attendance.date.desc()).limit(50).all() if current_sub_ids else []
    max_streak, current_streak = 0, 0
    for a in att_records:
        if not a.status:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # 7. Subjects with attendance < 75%
    per_sub_att = db.query(
        attendance_model.Attendance.subject_id,
        func.count(attendance_model.Attendance.id),
        func.sum(func.cast(attendance_model.Attendance.status, Integer))
    ).filter(
        attendance_model.Attendance.student_id == student_id,
        attendance_model.Attendance.subject_id.in_(current_sub_ids)
    ).group_by(attendance_model.Attendance.subject_id).all() if current_sub_ids else []

    low_att_subjects = sum(1 for _, total, present in per_sub_att
                           if total > 0 and (int(present or 0) / total * 100) < 75)

    # 8. Subjects with marks < 40%
    failing_subjects = 0
    for sub in current_subjects:
        sub_marks = [m for m in marks_records if m.subject_id == sub.id]
        if sub_marks:
            ts = sum(m.score for m in sub_marks)
            tm = sum(m.total for m in sub_marks)
            if tm > 0 and (ts / tm * 100) < 40:
                failing_subjects += 1

    return {
        "attendance_pct": round(attendance_pct, 2),
        "mid1_avg": round(mid1_avg, 4),
        "mid2_avg": round(mid2_avg, 4),
        "assignment_rate": round(assignment_rate, 4),
        "prev_sgpa": round(float(prev_sgpa), 2),
        "classes_missed_streak": int(max_streak),
        "low_att_subjects": int(low_att_subjects),
        "failing_subjects": int(failing_subjects),
    }


# ============================================================================
# ML SERVICE CLASS
# ============================================================================
class MLService:
    """ML Service providing XGBoost-based predictions."""

    @staticmethod
    def predict_risk(db: Session, student_id: int) -> dict:
        """Predict student risk using trained XGBoost classifier."""
        from .analytics_service import AnalyticsService

        student = db.query(student_model.Student).filter(
            student_model.Student.id == student_id
        ).first()
        student_name = student.user.username if student and student.user else f"Student {student_id}"

        # Extract features
        features = _get_risk_features(db, student_id)
        att_pct = features["attendance_pct"] if features else 75.0
        avg_marks = AnalyticsService.calculate_average_marks(db, student_id)

        # Default: rule-based fallback
        risk_status = AnalyticsService.classify_risk(att_pct, avg_marks)
        confidence = 0.75
        model_type = "Rule-Based"

        # Use ML model if available
        if _risk_model and _risk_features and _risk_encoder and features:
            try:
                df = pd.DataFrame([features])
                df = df[_risk_features]
                pred_idx = _risk_model.predict(df)[0]
                risk_status = _risk_encoder.inverse_transform([pred_idx])[0]
                proba = _risk_model.predict_proba(df)[0]
                confidence = round(float(max(proba)), 3)
                model_type = "XGBoost Classifier"
            except Exception as e:
                logger.error(f"Risk model prediction failed: {e}")

        # Dynamic risk factors
        risk_factors = []
        if att_pct < 75:
            risk_factors.append(f"Low attendance ({att_pct:.1f}%)")
        if avg_marks < 40:
            risk_factors.append(f"Low marks ({avg_marks:.1f}%)")
        if features and features["low_att_subjects"] > 0:
            risk_factors.append(f"{features['low_att_subjects']} subjects below 75% attendance")
        if features and features["failing_subjects"] > 0:
            risk_factors.append(f"{features['failing_subjects']} subjects below 40% marks")
        if features and features["classes_missed_streak"] >= 3:
            risk_factors.append(f"Missed {features['classes_missed_streak']} classes in a row")
        if not risk_factors:
            risk_factors.append("No significant risk factors detected")

        # Dynamic recommendation
        if risk_status == "At Risk":
            recommendation = "Immediate intervention needed. Schedule 1-on-1 counselling and notify parents."
        elif risk_status == "Warning":
            recommendation = "Monitor closely. Encourage regular attendance and provide academic support."
        else:
            recommendation = "Student is performing well. Keep up the good work."

        return {
            "student_id": student_id,
            "student_name": student_name,
            "risk_status": risk_status,
            "confidence": confidence,
            "attendance_percentage": round(att_pct, 1),
            "average_marks": round(avg_marks, 1),
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "model_type": model_type,
            "features_used": features,
        }

    @staticmethod
    def predict_gpa(db: Session, student_id: int) -> dict:
        """Predict semester GPA using trained XGBoost model."""
        student = db.query(student_model.Student).filter(
            student_model.Student.id == student_id
        ).first()
        if not student:
            return {"error": "Student not found"}

        current_sem = student.current_semester or 6

        features = _get_gpa_features(db, student_id)
        if not features:
            return {"error": "Could not extract features"}

        predicted_sgpa = 7.0
        model_type = "fallback"

        if _gpa_model and _gpa_features:
            try:
                df = pd.DataFrame([features])
                df = df[_gpa_features]
                raw_pred = _gpa_model.predict(df)[0]
                predicted_sgpa = round(float(np.clip(raw_pred, 2.0, 10.0)), 2)
                model_type = "XGBoost Regressor"
            except Exception as e:
                logger.error(f"GPA model prediction failed: {e}")
                predicted_sgpa = round(float(np.clip(
                    0.30 * features["mid1_avg"] * 10 +
                    0.20 * (features["attendance_pct"] / 100) * 10 +
                    0.15 * features["assignment_rate"] * 10 +
                    0.20 * features["prev_sgpa"] + 0.5,
                    2.0, 10.0
                )), 2)
                model_type = "Weighted Formula (fallback)"

        from .analytics_service import AnalyticsService
        analytics = AnalyticsService.get_student_analytics(db, student_id)
        current_cgpa = analytics.get("cgpa", 0) if analytics else 0

        return {
            "student_id": student_id,
            "student_name": student.user.username if student.user else "Unknown",
            "current_semester": current_sem,
            "predicted_semester": current_sem,
            "current_cgpa": current_cgpa,
            "predicted_sgpa": predicted_sgpa,
            "model_type": model_type,
            "features_used": features,
        }

    @staticmethod
    def batch_predict(db: Session) -> list:
        students = db.query(student_model.Student).all()
        return [MLService.predict_risk(db, s.id) for s in students]

    @staticmethod
    def batch_predict_gpa(db: Session) -> list:
        students = db.query(student_model.Student).all()
        return [MLService.predict_gpa(db, s.id) for s in students]
