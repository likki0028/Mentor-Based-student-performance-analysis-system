
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import quiz as quiz_model
from ..models import quiz_attempt as attempt_model
from ..models import student as student_model
from ..models import user as user_model
from ..schemas import quiz as quiz_schema
from ..dependencies import get_current_active_user

router = APIRouter()

# --- Extra Schemas ---
class QuizAttemptCreate(BaseModel):
    quiz_id: int
    marks_obtained: int

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    marks_obtained: int

    class Config:
        from_attributes = True

# --- Routes ---
@router.get("/", response_model=List[quiz_schema.Quiz])
async def get_quizzes(
    subject_id: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all quizzes, optionally filter by subject."""
    query = db.query(quiz_model.Quiz)
    if subject_id:
        query = query.filter(quiz_model.Quiz.subject_id == subject_id)
    return query.all()

@router.post("/", response_model=quiz_schema.Quiz, status_code=201)
async def create_quiz(
    data: quiz_schema.QuizCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new quiz (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_quiz = quiz_model.Quiz(
        title=data.title,
        subject_id=data.subject_id,
        total_marks=data.total_marks
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    return new_quiz

@router.post("/attempt", response_model=QuizAttemptOut, status_code=201)
async def attempt_quiz(
    data: QuizAttemptCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Student attempts a quiz."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can attempt quizzes")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    quiz = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.id == data.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Check for duplicate attempt
    existing = db.query(attempt_model.QuizAttempt).filter(
        attempt_model.QuizAttempt.quiz_id == data.quiz_id,
        attempt_model.QuizAttempt.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already attempted this quiz")

    if data.marks_obtained > quiz.total_marks:
        raise HTTPException(status_code=400, detail="Marks cannot exceed total marks")

    attempt = attempt_model.QuizAttempt(
        quiz_id=data.quiz_id,
        student_id=student.id,
        marks_obtained=data.marks_obtained
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

@router.get("/{quiz_id}/results", response_model=List[QuizAttemptOut])
async def get_quiz_results(
    quiz_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all attempts for a quiz (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    attempts = db.query(attempt_model.QuizAttempt).filter(
        attempt_model.QuizAttempt.quiz_id == quiz_id
    ).all()
    return attempts
