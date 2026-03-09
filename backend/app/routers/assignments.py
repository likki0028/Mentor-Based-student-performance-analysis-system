
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import assignment as assignment_model
from ..models import submission as submission_model
from ..models import student as student_model
from ..models import user as user_model
from ..schemas import assignment as assignment_schema
from ..dependencies import get_current_active_user

router = APIRouter()

# --- Extra Schemas ---
class SubmissionCreate(BaseModel):
    assignment_id: int
    file_url: str = ""

class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    submission_date: date
    file_url: Optional[str] = None
    grade: Optional[int] = None

    class Config:
        from_attributes = True

# --- Routes ---
@router.get("/", response_model=List[assignment_schema.Assignment])
async def get_assignments(
    subject_id: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all assignments, optionally filter by subject."""
    query = db.query(assignment_model.Assignment)
    if subject_id:
        query = query.filter(assignment_model.Assignment.subject_id == subject_id)
    return query.order_by(assignment_model.Assignment.due_date.desc()).all()

@router.post("/", response_model=assignment_schema.Assignment, status_code=201)
async def create_assignment(
    data: assignment_schema.AssignmentCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new assignment (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_assignment = assignment_model.Assignment(
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        subject_id=data.subject_id
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return new_assignment

@router.post("/submit", response_model=SubmissionOut, status_code=201)
async def submit_assignment(
    data: SubmissionCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Student submits an assignment."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit assignments")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Check assignment exists
    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == data.assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check for duplicate submission
    existing = db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id == data.assignment_id,
        submission_model.Submission.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already submitted")

    submission = submission_model.Submission(
        assignment_id=data.assignment_id,
        student_id=student.id,
        submission_date=date.today(),
        file_url=data.file_url
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

@router.get("/pending")
async def get_pending_assignments(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get assignments not yet submitted by the current student."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view pending assignments")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        return []

    all_assignments = db.query(assignment_model.Assignment).all()
    submitted_ids = {s.assignment_id for s in db.query(submission_model.Submission).filter(
        submission_model.Submission.student_id == student.id
    ).all()}

    pending = []
    for a in all_assignments:
        if a.id not in submitted_ids:
            pending.append({
                "id": a.id, "title": a.title,
                "description": a.description,
                "due_date": str(a.due_date),
                "subject_id": a.subject_id,
                "is_overdue": a.due_date < date.today() if a.due_date else False
            })
    return pending

@router.get("/{assignment_id}/submissions", response_model=List[SubmissionOut])
async def get_submissions(
    assignment_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all submissions for an assignment (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    submissions = db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id == assignment_id
    ).all()
    return submissions
