
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

router = APIRouter()

# --- Schemas ---
class AttendanceMarkItem(BaseModel):
    student_id: int
    subject_id: int
    date: date
    status: bool  # True=Present, False=Absent

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
    """Bulk mark attendance (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    created = 0
    for record in data.records:
        att = attendance_model.Attendance(
            student_id=record.student_id,
            subject_id=record.subject_id,
            date=record.date,
            status=record.status
        )
        db.add(att)
        created += 1
    
    db.commit()
    return {"message": f"{created} attendance records created"}

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
            "status": r.status
        })
    return results


