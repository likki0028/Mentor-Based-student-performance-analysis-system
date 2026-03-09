
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import faculty as faculty_model
from ..models import student as student_model
from ..models import user as user_model
from ..models import remark as remark_model
from ..schemas import faculty as faculty_schema
from ..dependencies import get_current_active_user

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

@router.get("/dashboard", response_model=faculty_schema.FacultyDashboard)
async def get_dashboard_stats(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_students = db.query(student_model.Student).count()
    at_risk = max(1, total_students // 10)  # Simple heuristic: ~10% at risk
    
    return {
        "total_students": total_students,
        "at_risk_count": at_risk,
        "pending_tasks": 2,
        "recent_alerts": ["Student X has low attendance", "Student Y failed Mid-Term"]
    }

@router.get("/my-students", response_model=List[faculty_schema.StudentSummary])
async def get_my_students(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    students = db.query(student_model.Student).limit(10).all()
    
    results = []
    for stu in students:
        risk = "Safe"
        if int(stu.id) % 5 == 0:
            risk = "At Risk"
            
        summary = faculty_schema.StudentSummary(
            id=stu.id,
            name=stu.user.username if stu.user else "Unknown",
            enrollment_number=stu.enrollment_number,
            current_semester=getattr(stu, 'current_semester', 1) or 1,
            attendance_percentage=75.5,
            risk_status=risk
        )
        results.append(summary)
        
    return results

@router.post("/remarks", response_model=faculty_schema.RemarkOut, status_code=201)
async def add_remark(
    remark_data: faculty_schema.RemarkCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a remark/note to a student's profile."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.LECTURER, user_model.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify student exists
    student = db.query(student_model.Student).filter(student_model.Student.id == remark_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get faculty profile
    fac = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.user_id == current_user.id).first()
    faculty_id = fac.id if fac else 0

    new_remark = remark_model.Remark(
        student_id=remark_data.student_id,
        faculty_id=faculty_id,
        message=remark_data.message
    )
    db.add(new_remark)
    db.commit()
    db.refresh(new_remark)
    return new_remark

@router.get("/remarks/{student_id}", response_model=List[faculty_schema.RemarkOut])
async def get_remarks(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all remarks for a student."""
    remarks = db.query(remark_model.Remark).filter(
        remark_model.Remark.student_id == student_id
    ).order_by(remark_model.Remark.created_at.desc()).all()
    return remarks
