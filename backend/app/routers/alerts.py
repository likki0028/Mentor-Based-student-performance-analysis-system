
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import alert as alert_model
from ..models import student as student_model
from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import user as user_model
from ..schemas import alert as alert_schema
from ..dependencies import get_current_active_user
from sqlalchemy import func, Integer

router = APIRouter()

@router.get("/", response_model=List[alert_schema.Alert])
async def get_alerts(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get alerts. Students see their own, Faculty/Admin see all."""
    if current_user.role == user_model.UserRole.STUDENT:
        student = db.query(student_model.Student).filter(
            student_model.Student.user_id == current_user.id
        ).first()
        if not student:
            return []
        alerts = db.query(alert_model.Alert).filter(
            alert_model.Alert.student_id == student.id
        ).order_by(alert_model.Alert.created_at.desc()).all()
    else:
        alerts = db.query(alert_model.Alert).order_by(
            alert_model.Alert.created_at.desc()
        ).limit(50).all()
    
    return alerts

@router.post("/read/{alert_id}")
async def mark_alert_as_read(
    alert_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as read."""
    alert = db.query(alert_model.Alert).filter(alert_model.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read"}

@router.post("/generate", status_code=201)
async def generate_alerts(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin/Faculty: Auto-generate alerts for at-risk students.
    Flags students with <75% attendance or average marks <40%.
    """
    if current_user.role not in [user_model.UserRole.ADMIN, user_model.UserRole.MENTOR, user_model.UserRole.LECTURER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
    return {"message": f"{alerts_created} alerts generated"}
