
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import student as student_model
from ..models import subject as subject_model
from ..models import alert as alert_model


class AnalyticsService:
    @staticmethod
    def get_student_analytics(db: Session, student_id: int):
        """Get comprehensive analytics for a student."""
        student = db.query(student_model.Student).filter(
            student_model.Student.id == student_id
        ).first()
        if not student:
            return None

        # Attendance stats
        total_classes = db.query(func.count(attendance_model.Attendance.id)).filter(
            attendance_model.Attendance.student_id == student_id
        ).scalar() or 0

        present_count = db.query(func.sum(
            func.cast(attendance_model.Attendance.status, Integer)
        )).filter(
            attendance_model.Attendance.student_id == student_id
        ).scalar() or 0

        attendance_pct = (present_count / total_classes * 100) if total_classes > 0 else 0

        # Marks stats
        marks_records = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == student_id
        ).all()

        avg_marks = 0
        if marks_records:
            avg_marks = sum(m.score for m in marks_records) / len(marks_records)

        # Subject-wise breakdown
        subject_stats = []
        subjects = db.query(subject_model.Subject).all()
        for sub in subjects:
            sub_marks = [m for m in marks_records if m.subject_id == sub.id]
            sub_att_total = db.query(func.count(attendance_model.Attendance.id)).filter(
                attendance_model.Attendance.student_id == student_id,
                attendance_model.Attendance.subject_id == sub.id
            ).scalar() or 0
            sub_att_present = db.query(func.sum(
                func.cast(attendance_model.Attendance.status, Integer)
            )).filter(
                attendance_model.Attendance.student_id == student_id,
                attendance_model.Attendance.subject_id == sub.id
            ).scalar() or 0

            sub_att_pct = (sub_att_present / sub_att_total * 100) if sub_att_total > 0 else 0
            sub_avg = sum(m.score for m in sub_marks) / len(sub_marks) if sub_marks else 0

            if sub_att_total > 0 or sub_marks:
                subject_stats.append({
                    "subject_id": sub.id,
                    "subject_name": sub.name,
                    "subject_code": sub.code,
                    "attendance_percentage": round(sub_att_pct, 2),
                    "total_classes": sub_att_total,
                    "classes_attended": sub_att_present,
                    "average_marks": round(sub_avg, 2),
                    "marks_count": len(sub_marks)
                })

        # Risk classification
        risk_status = AnalyticsService.classify_risk(attendance_pct, avg_marks)

        # Recent alerts
        alerts = db.query(alert_model.Alert).filter(
            alert_model.Alert.student_id == student_id
        ).order_by(alert_model.Alert.created_at.desc()).limit(5).all()

        return {
            "student_id": student_id,
            "name": student.user.username if student.user else "Unknown",
            "enrollment_number": student.enrollment_number,
            "current_semester": student.current_semester,
            "attendance_percentage": round(attendance_pct, 2),
            "total_classes": total_classes,
            "classes_attended": present_count,
            "average_marks": round(avg_marks, 2),
            "total_assessments": len(marks_records),
            "risk_status": risk_status,
            "subject_stats": subject_stats,
            "recent_alerts": [
                {"id": a.id, "message": a.message, "type": a.type, "is_read": a.is_read, "created_at": str(a.created_at)}
                for a in alerts
            ]
        }

    @staticmethod
    def classify_risk(attendance_pct: float, avg_marks: float) -> str:
        """Rule-based risk classification."""
        if attendance_pct < 75 or avg_marks < 40:
            return "At Risk"
        elif attendance_pct < 85 or avg_marks < 60:
            return "Warning"
        return "Safe"

    @staticmethod
    def calculate_gpa(db: Session, student_id: int) -> float:
        """Calculate GPA from marks (simplified: marks % mapped to 10-point scale)."""
        marks_records = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == student_id
        ).all()

        if not marks_records:
            return 0.0

        total_percentage = sum((m.score / m.total * 100) if m.total > 0 else 0 for m in marks_records)
        avg_pct = total_percentage / len(marks_records)

        # Convert to 10-point GPA
        gpa = min(10.0, avg_pct / 10)
        return round(gpa, 2)
