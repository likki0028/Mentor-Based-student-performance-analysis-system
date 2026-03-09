
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import student as student_model


class MLService:
    """Rule-based risk classification service.
    
    Uses attendance percentage and average marks to classify students:
    - At Risk: attendance < 75% OR avg marks < 40
    - Warning: attendance < 85% OR avg marks < 60
    - Safe: otherwise
    """

    @staticmethod
    def predict_risk(db: Session, student_id: int) -> dict:
        """Predict risk status for a single student."""
        student = db.query(student_model.Student).filter(
            student_model.Student.id == student_id
        ).first()
        if not student:
            return {"error": "Student not found"}

        # Calculate attendance
        total = db.query(func.count(attendance_model.Attendance.id)).filter(
            attendance_model.Attendance.student_id == student_id
        ).scalar() or 0

        present = db.query(func.sum(
            func.cast(attendance_model.Attendance.status, Integer)
        )).filter(
            attendance_model.Attendance.student_id == student_id
        ).scalar() or 0

        att_pct = (present / total * 100) if total > 0 else 100

        # Calculate average marks
        avg_marks = db.query(func.avg(marks_model.Marks.score)).filter(
            marks_model.Marks.student_id == student_id
        ).scalar() or 0

        # Risk factors
        factors = []
        if att_pct < 75:
            factors.append(f"Low attendance: {att_pct:.1f}%")
        if avg_marks < 40:
            factors.append(f"Low average marks: {avg_marks:.1f}")

        # Classification
        if att_pct < 75 or avg_marks < 40:
            risk = "At Risk"
            confidence = 0.9
        elif att_pct < 85 or avg_marks < 60:
            risk = "Warning"
            confidence = 0.7
            if att_pct < 85:
                factors.append(f"Attendance below 85%: {att_pct:.1f}%")
            if avg_marks < 60:
                factors.append(f"Average marks below 60: {avg_marks:.1f}")
        else:
            risk = "Safe"
            confidence = 0.85
            factors.append("All metrics within acceptable range")

        return {
            "student_id": student_id,
            "student_name": student.user.username if student.user else "Unknown",
            "risk_status": risk,
            "confidence": confidence,
            "attendance_percentage": round(att_pct, 2),
            "average_marks": round(float(avg_marks), 2),
            "risk_factors": factors,
            "recommendation": MLService._get_recommendation(risk)
        }

    @staticmethod
    def _get_recommendation(risk: str) -> str:
        if risk == "At Risk":
            return "Immediate intervention required. Schedule a meeting with the mentor and set up a performance improvement plan."
        elif risk == "Warning":
            return "Monitor closely. Encourage the student to improve attendance and seek help in weak subjects."
        return "Student is performing well. Continue to encourage and support."

    @staticmethod
    def batch_predict(db: Session) -> list:
        """Predict risk for all students."""
        students = db.query(student_model.Student).all()
        results = []
        for stu in students:
            result = MLService.predict_risk(db, stu.id)
            if "error" not in result:
                results.append(result)
        return results
