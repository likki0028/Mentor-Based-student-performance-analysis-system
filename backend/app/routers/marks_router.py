
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import marks as marks_model
from ..models import user as user_model
from ..models import student as student_model
from ..dependencies import get_current_active_user

router = APIRouter()

# --- Schemas ---
class MarkCreate(BaseModel):
    student_id: int
    subject_id: int
    assessment_type: str  # "mid_term", "end_term", "internal"
    score: int
    total: int

class BulkMarkCreate(BaseModel):
    marks: List[MarkCreate]

# --- Routes ---
@router.post("/", status_code=201)
async def add_marks(
    data: BulkMarkCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add marks for students (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    created = 0
    for m in data.marks:
        # Validate student exists
        student = db.query(student_model.Student).filter(
            student_model.Student.id == m.student_id
        ).first()
        if not student:
            continue

        # Map assessment type
        try:
            assessment = marks_model.AssessmentType(m.assessment_type)
        except ValueError:
            assessment = marks_model.AssessmentType.INTERNAL

        mark = marks_model.Marks(
            student_id=m.student_id,
            subject_id=m.subject_id,
            assessment_type=assessment,
            score=min(m.score, m.total),
            total=m.total
        )
        db.add(mark)
        created += 1

    db.commit()
    return {"message": f"{created} marks records added"}

@router.get("/{student_id}")
async def get_student_marks(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all marks for a student."""
    records = db.query(marks_model.Marks).filter(
        marks_model.Marks.student_id == student_id
    ).all()

    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "subject_id": r.subject_id,
            "assessment_type": r.assessment_type,
            "score": r.score,
            "total": r.total
        }
        for r in records
    ]
