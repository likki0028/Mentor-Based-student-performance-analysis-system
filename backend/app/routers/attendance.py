
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from pydantic import BaseModel

from ..database import get_db
from ..models import attendance as attendance_model
from ..models import student as student_model
from ..models import subject as subject_model
from ..models import user as user_model
from ..dependencies import get_current_active_user
from ..timetable_config import get_periods_for_subject, get_day_from_date, CODE_TO_SHORT
from ..services import notification_service
from ..models.notification import NotificationPriority, NotificationType

router = APIRouter()

# --- Schemas ---
class AttendanceMarkItem(BaseModel):
    student_id: int
    subject_id: int
    date: date
    status: bool  # True=Present, False=Absent
    period: int = 1  # Period number 1-7

class AttendanceBulkMark(BaseModel):
    records: List[AttendanceMarkItem]

class AttendanceReport(BaseModel):
    student_id: int
    student_name: str
    subject_name: str
    total_classes: int
    present: int
    percentage: float

# --- Routes ---
@router.post("/mark", status_code=201)
async def mark_attendance(
    data: AttendanceBulkMark,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk mark attendance (Faculty/Admin only). Rejects if attendance already exists for that date+subject+period."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if data.records:
        first = data.records[0]
        record_date = first.date
        
        # Block future dates
        if record_date > date.today():
            raise HTTPException(status_code=400, detail="Cannot mark attendance for future dates.")
        
        # Block Sundays
        if record_date.weekday() == 6:  # 6 = Sunday
            raise HTTPException(status_code=400, detail="Cannot mark attendance on Sunday.")
        
        # Block Fridays (Training day)
        if record_date.weekday() == 4:  # 4 = Friday
            raise HTTPException(status_code=400, detail="Cannot mark attendance on Friday (Training Day).")
        
        # Block festival holidays
        festival_holidays = [
            "2026-01-01", "2026-01-26", "2026-03-14", "2026-03-30",
            "2026-04-14", "2026-08-15", "2026-08-19", "2026-09-18",
            "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-12", "2026-12-25"
        ]
        if str(record_date) in festival_holidays:
            raise HTTPException(status_code=400, detail="Cannot mark attendance on a festival holiday.")
        
        # Check duplicate: now per (subject_id, date, period)
        existing = db.query(attendance_model.Attendance).filter(
            attendance_model.Attendance.subject_id == first.subject_id,
            attendance_model.Attendance.date == first.date,
            attendance_model.Attendance.period == first.period
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Attendance already taken for this subject on {first.date} (Period {first.period}). It cannot be changed."
            )
    
    created = 0
    absent_notifications = []  # Collect absent info for background notification
    for record in data.records:
        att = attendance_model.Attendance(
            student_id=record.student_id,
            subject_id=record.subject_id,
            date=record.date,
            status=record.status,
            period=record.period
        )
        db.add(att)
        created += 1

        # Collect absent students for background notification
        if not record.status:
            try:
                student = db.query(student_model.Student).filter(student_model.Student.id == record.student_id).first()
                subject = db.query(subject_model.Subject).filter(subject_model.Subject.id == record.subject_id).first()
                if student and student.user_id:
                    absent_notifications.append({
                        "user_id": student.user_id,
                        "subject": subject.name if subject else "Subject",
                        "date": str(record.date),
                        "period": record.period
                    })
            except Exception as e:
                print(f"Failed to collect absent info: {e}")
    
    db.commit()

    # --- Send absent notifications in background ---
    if absent_notifications:
        import threading
        from ..database import SessionLocal
        _notifs = list(absent_notifications)

        def _send_absent_alerts():
            bg_db = SessionLocal()
            try:
                for info in _notifs:
                    notification_service.create_notification(
                        db=bg_db,
                        user_id=info["user_id"],
                        title="Attendance Alert",
                        message=f"You were marked ABSENT for {info['subject']} on {info['date']} (Period {info['period']})",
                        notif_type=NotificationType.SYSTEM,
                        priority=NotificationPriority.LOW,  # Bell only — fast
                        link="/student/attendance"
                    )
            except Exception as e:
                print(f"BG absent notification error: {e}")
            finally:
                bg_db.close()

        threading.Thread(target=_send_absent_alerts, daemon=True).start()

    return {"message": f"{created} attendance records created"}

@router.get("/check")
async def check_attendance(
    subject_id: int,
    date: str,
    period: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if attendance has already been taken for a subject on a given date (optionally per period)."""
    query = db.query(attendance_model.Attendance).filter(
        attendance_model.Attendance.subject_id == subject_id,
        attendance_model.Attendance.date == date
    )
    if period is not None:
        query = query.filter(attendance_model.Attendance.period == period)
    
    records = query.all()
    
    if not records:
        return {"taken": False, "records": []}
    
    # Group by period to show which periods are already taken
    taken_periods = list(set(r.period for r in records if r.period))
    
    return {
        "taken": True,
        "taken_periods": taken_periods,
        "records": [
            {"student_id": r.student_id, "status": r.status, "period": r.period}
            for r in records
        ]
    }

@router.get("/timetable-periods")
async def get_timetable_periods(
    subject_id: int,
    date: str,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get which period numbers a subject occupies on a given date.
    Returns the list of periods and which ones already have attendance marked.
    """
    from datetime import datetime as dt

    subject = db.query(subject_model.Subject).filter(subject_model.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    parsed_date = dt.strptime(date, "%Y-%m-%d").date()
    day_name = get_day_from_date(parsed_date)

    if not day_name:
        return {"periods": [], "message": "Sunday — no classes", "is_training_day": False}

    if day_name == "FRI":
        return {"periods": [], "message": "Training Day — no attendance", "is_training_day": True}

    subject_code = subject.code
    periods = get_periods_for_subject(subject_code, day_name)

    # Check which periods already have attendance
    existing = db.query(attendance_model.Attendance.period).filter(
        attendance_model.Attendance.subject_id == subject_id,
        attendance_model.Attendance.date == date
    ).distinct().all()
    taken_periods = [r[0] for r in existing if r[0]]

    return {
        "periods": periods,
        "taken_periods": taken_periods,
        "day": day_name,
        "subject_code": subject_code,
        "is_training_day": False,
        "message": f"{len(periods)} period(s) on {day_name}" if periods else f"No class for this subject on {day_name}"
    }

@router.get("/report", response_model=List[AttendanceReport])
async def get_attendance_report(
    subject_id: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get attendance report for all students, optionally filtered by subject."""
    query = db.query(
        attendance_model.Attendance.student_id,
        attendance_model.Attendance.subject_id,
        func.count(attendance_model.Attendance.id).label("total"),
        func.sum(
            func.cast(attendance_model.Attendance.status, Integer)
        ).label("present")
    ).group_by(
        attendance_model.Attendance.student_id,
        attendance_model.Attendance.subject_id
    )

    if subject_id:
        query = query.filter(attendance_model.Attendance.subject_id == subject_id)
    
    results = query.all()
    
    report = []
    for row in results:
        student = db.query(student_model.Student).filter(student_model.Student.id == row.student_id).first()
        subject = db.query(subject_model.Subject).filter(subject_model.Subject.id == row.subject_id).first()
        
        total = row.total or 0
        present = row.present or 0
        pct = (present / total * 100) if total > 0 else 0
        
        report.append(AttendanceReport(
            student_id=row.student_id,
            student_name=student.user.username if student and student.user else "Unknown",
            subject_name=subject.name if subject else "Unknown",
            total_classes=total,
            present=present,
            percentage=round(pct, 2)
        ))
    
    return report

@router.get("/{student_id}")
async def get_student_attendance(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get attendance records for a specific student."""
    records = db.query(attendance_model.Attendance).filter(
        attendance_model.Attendance.student_id == student_id
    ).all()
    
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "student_id": r.student_id,
            "subject_id": r.subject_id,
            "date": str(r.date),
            "status": r.status,
            "period": r.period
        })
    return results


