
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from ..models import alert as alert_model
from ..models import student as student_model
from ..models import attendance as attendance_model
from ..models import marks as marks_model
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
            students = db.query(student_model.Student).all()
            alerts_created = 0

            for stu in students:
                # Check attendance
                total = db.query(func.count(attendance_model.Attendance.id)).filter(
                    attendance_model.Attendance.student_id == stu.id
                ).scalar() or 0

                present = db.query(func.sum(
                    func.cast(attendance_model.Attendance.status, Integer)
                )).filter(
                    attendance_model.Attendance.student_id == stu.id
                ).scalar() or 0

                att_pct = (present / total * 100) if total > 0 else 100

                if att_pct < 75:
                    existing = db.query(alert_model.Alert).filter(
                        alert_model.Alert.student_id == stu.id,
                        alert_model.Alert.type == "Low Attendance",
                        alert_model.Alert.is_read == False
                    ).first()
                    if not existing:
                        db.add(alert_model.Alert(
                            student_id=stu.id,
                            message=f"Attendance is {att_pct:.1f}% (below 75% threshold)",
                            type="Low Attendance"
                        ))
                        alerts_created += 1

                # Check marks
                avg_score = db.query(func.avg(marks_model.Marks.score)).filter(
                    marks_model.Marks.student_id == stu.id
                ).scalar()

                if avg_score is not None and avg_score < 40:
                    existing = db.query(alert_model.Alert).filter(
                        alert_model.Alert.student_id == stu.id,
                        alert_model.Alert.type == "Low Marks",
                        alert_model.Alert.is_read == False
                    ).first()
                    if not existing:
                        db.add(alert_model.Alert(
                            student_id=stu.id,
                            message=f"Average score is {avg_score:.1f}% (below 40% threshold)",
                            type="Low Marks"
                        ))
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
