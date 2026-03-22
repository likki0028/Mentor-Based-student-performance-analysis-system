
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from ..models import alert as alert_model
from ..models import student as student_model
from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import user as user_model
from .email_service import EmailService
from ..database import SessionLocal


class AlertService:
    @staticmethod
    def generate_alerts(db: Session = None):
        """Check all students and generate alerts for at-risk students.
        
        Flags:
        - Attendance < 75%
        - Average marks < 40
        """
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True

        try:
            # Optimized approach: Get all student IDs to check
            students = db.query(student_model.Student).all()
            if not students: return 0
            
            # 1. Fetch all attendance stats in one query
            att_stats = db.query(
                attendance_model.Attendance.student_id,
                func.count(attendance_model.Attendance.id).label("total"),
                func.sum(func.cast(attendance_model.Attendance.status, Integer)).label("present")
            ).group_by(attendance_model.Attendance.student_id).all()
            att_map = {row.student_id: (row.present / row.total * 100) if row.total > 0 else 100 for row in att_stats}

            # 2. Fetch all average marks in one query
            marks_stats = db.query(
                marks_model.Marks.student_id,
                func.avg(marks_model.Marks.score).label("avg_score")
            ).group_by(marks_model.Marks.student_id).all()
            marks_map = {row.student_id: row.avg_score for row in marks_stats}

            alerts_created = 0
            for stu in students:
                # Check attendance
                att_pct = att_map.get(stu.id, 100)
                if att_pct < 75:
                    existing = db.query(alert_model.Alert).filter(
                        alert_model.Alert.student_id == stu.id,
                        alert_model.Alert.type == "Low Attendance",
                        alert_model.Alert.is_read == False
                    ).first()
                    if not existing:
                        new_alert = alert_model.Alert(
                            student_id=stu.id,
                            message=f"{stu.user.username if stu.user else 'Student'} - Attendance: {att_pct:.1f}%",
                            type="Low Attendance"
                        )
                        db.add(new_alert)
                        if stu.mentor and stu.mentor.user:
                            EmailService.send_alert_email(stu.mentor.user.email, stu.user.username if stu.user else "Student", "Low Attendance", f"Attendance is {att_pct:.1f}%")
                        alerts_created += 1

                # Check marks
                avg_score = marks_map.get(stu.id)
                if avg_score is not None and avg_score < 40:
                    existing = db.query(alert_model.Alert).filter(
                        alert_model.Alert.student_id == stu.id,
                        alert_model.Alert.type == "Low Marks",
                        alert_model.Alert.is_read == False
                    ).first()
                    if not existing:
                        new_alert = alert_model.Alert(
                            student_id=stu.id,
                            message=f"{stu.user.username if stu.user else 'Student'} - Avg Marks: {avg_score:.1f}%",
                            type="Low Marks"
                        )
                        db.add(new_alert)
                        if stu.mentor and stu.mentor.user:
                            EmailService.send_alert_email(stu.mentor.user.email, stu.user.username if stu.user else "Student", "Low Marks", f"Average score is {avg_score:.1f}%")
                        alerts_created += 1

            db.commit()
            return alerts_created
        except Exception as e:
            db.rollback()
            print(f"Error generating alerts: {e}")
            return 0
        finally:
            if own_session:
                db.close()
