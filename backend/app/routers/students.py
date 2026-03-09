from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import student as student_model
from ..models import user as user_model
from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..models import subject as subject_model
from ..schemas import student as student_schema
from ..dependencies import get_current_active_user, get_current_user

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=student_schema.StudentOut)
async def read_users_me(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    student = db.query(student_model.Student).filter(student_model.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    # Calculate attendance percentage (Simple logic for now)
    total_days = db.query(attendance_model.Attendance).filter(attendance_model.Attendance.student_id == student.id).count()
    present_days = db.query(attendance_model.Attendance).filter(
        attendance_model.Attendance.student_id == student.id,
        attendance_model.Attendance.status == True
    ).count()
    
    percentage = (present_days / total_days * 100) if total_days > 0 else 0.0
    
    # Create response object and attach calculated field
    # We use valid pydantic model creation
    response = student_schema.StudentOut.model_validate(student)
    response.name = student.user.username # fallback if name is empty in student table
    response.attendance_percentage = round(percentage, 2)
    
    return response

@router.get("/{student_id}/attendance", response_model=List[student_schema.AttendanceOut])
async def read_student_attendance(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Authorization checks (Self, Mentor, or Admin) can be added here
    # For now, allow if user is authenticated
    
    attendance_records = db.query(attendance_model.Attendance).options(
        joinedload(attendance_model.Attendance.subject)
    ).filter(attendance_model.Attendance.student_id == student_id).all()
    
    results = []
    for record in attendance_records:
         # Build response manually to include subject name if joined
         res = student_schema.AttendanceOut.model_validate(record)
         if record.subject:
             res.subject_name = record.subject.name
         results.append(res)
         
    return results

@router.get("/{student_id}/marks", response_model=List[student_schema.MarkOut])
async def read_student_marks(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    marks_records = db.query(marks_model.Marks).options(
        joinedload(marks_model.Marks.subject)
    ).filter(marks_model.Marks.student_id == student_id).all()
    
    results = []
    for record in marks_records:
         res = student_schema.MarkOut.model_validate(record)
         if record.subject:
             res.subject_name = record.subject.name
         results.append(res)
         
    return results
