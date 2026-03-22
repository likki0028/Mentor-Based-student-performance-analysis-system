
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import quiz as quiz_model
from ..models import quiz_question as question_model
from ..models import quiz_attempt as attempt_model
from ..models import quiz_response as response_model
from ..models import student as student_model
from ..models import user as user_model
from ..dependencies import get_current_active_user

router = APIRouter()

# --- Schemas ---
class QuestionInput(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str  # 'a','b','c','d'
    marks: int = 1

class QuizCreateInput(BaseModel):
    title: str
    subject_id: int
    section_id: Optional[int] = None
    start_time: str  # ISO format
    end_time: str     # ISO format
    questions: List[QuestionInput]

class AnswerInput(BaseModel):
    question_id: int
    selected_option: str  # 'a','b','c','d'

class QuizSubmitInput(BaseModel):
    answers: List[AnswerInput]

# --- Routes ---

@router.get("/")
async def list_quizzes(
    subject_id: Optional[int] = None,
    section_id: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List quizzes, optionally filtered by subject/section."""
    query = db.query(quiz_model.Quiz)
    if subject_id:
        query = query.filter(quiz_model.Quiz.subject_id == subject_id)
    if section_id:
        query = query.filter(quiz_model.Quiz.section_id == section_id)
    quizzes = query.order_by(quiz_model.Quiz.id.desc()).all()
    
    now = datetime.now()
    results = []
    for q in quizzes:
        status = "upcoming"
        if q.start_time and q.end_time:
            if now >= q.start_time and now <= q.end_time:
                status = "active"
            elif now > q.end_time:
                status = "ended"
        
        question_count = db.query(question_model.QuizQuestion).filter(
            question_model.QuizQuestion.quiz_id == q.id
        ).count()
        
        results.append({
            "id": q.id,
            "title": q.title,
            "subject_id": q.subject_id,
            "section_id": q.section_id,
            "total_marks": q.total_marks,
            "start_time": q.start_time.isoformat() if q.start_time else None,
            "end_time": q.end_time.isoformat() if q.end_time else None,
            "status": status,
            "question_count": question_count
        })
    return results


@router.post("/", status_code=201)
async def create_quiz(
    data: QuizCreateInput,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a quiz with questions (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if len(data.questions) == 0:
        raise HTTPException(status_code=400, detail="Quiz must have at least one question")
    
    total_marks = sum(q.marks for q in data.questions)
    
    try:
        start_time = datetime.fromisoformat(data.start_time)
        end_time = datetime.fromisoformat(data.end_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
    
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    new_quiz = quiz_model.Quiz(
        title=data.title,
        subject_id=data.subject_id,
        section_id=data.section_id,
        total_marks=total_marks,
        start_time=start_time,
        end_time=end_time,
        created_by=current_user.id
    )
    db.add(new_quiz)
    db.flush()  # Get the ID
    
    for q in data.questions:
        question = question_model.QuizQuestion(
            quiz_id=new_quiz.id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_option=q.correct_option.lower(),
            marks=q.marks
        )
        db.add(question)
    
    db.commit()
    db.refresh(new_quiz)
    
    return {
        "id": new_quiz.id,
        "title": new_quiz.title,
        "total_marks": new_quiz.total_marks,
        "question_count": len(data.questions),
        "start_time": new_quiz.start_time.isoformat(),
        "end_time": new_quiz.end_time.isoformat()
    }

@router.get("/recommendations/daily")
async def get_daily_assessment_recommendations(
    subject_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get recommended daily assessment marks (out of 5) for each student.
    Formula: for each quiz, normalize score to /5, then average all quizzes.
    """
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all quizzes for this subject
    quizzes = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.subject_id == subject_id).all()
    if not quizzes:
        return []
    
    quiz_ids = [q.id for q in quizzes]
    quiz_totals = {q.id: q.total_marks for q in quizzes}
    
    # Get all attempts for these quizzes
    attempts = db.query(attempt_model.QuizAttempt).filter(
        attempt_model.QuizAttempt.quiz_id.in_(quiz_ids)
    ).all()
    
    # Group by student: { student_id: [ (marks_obtained, total_marks), ... ] }
    student_scores = {}
    for a in attempts:
        if a.student_id not in student_scores:
            student_scores[a.student_id] = []
        total = quiz_totals.get(a.quiz_id, 1)
        student_scores[a.student_id].append((a.marks_obtained, total))
    
    # Calculate normalized average
    recommendations = []
    for sid, scores in student_scores.items():
        normalized_scores = [(obtained / total) * 5 for obtained, total in scores if total > 0]
        if normalized_scores:
            avg = sum(normalized_scores) / len(normalized_scores)
            # Round to nearest 0.5
            recommended = round(avg * 2) / 2
        else:
            recommended = 0
        
        student = db.query(student_model.Student).filter(student_model.Student.id == sid).first()
        name = "Unknown"
        if student and student.user:
            name = student.user.username
        
        recommendations.append({
            "student_id": sid,
            "student_name": name,
            "recommended_marks": recommended,
            "quizzes_taken": len(scores),
            "total_quizzes": len(quizzes)
        })
    
    return recommendations


@router.get("/{quiz_id}")
async def get_quiz_detail(
    quiz_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get quiz details with questions. Hides correct answer for students."""
    quiz = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = db.query(question_model.QuizQuestion).filter(
        question_model.QuizQuestion.quiz_id == quiz_id
    ).all()
    
    is_faculty = current_user.role in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]
    
    # Check if student already attempted
    already_attempted = False
    if current_user.role == user_model.UserRole.STUDENT:
        student = db.query(student_model.Student).filter(student_model.Student.user_id == current_user.id).first()
        if student:
            existing = db.query(attempt_model.QuizAttempt).filter(
                attempt_model.QuizAttempt.quiz_id == quiz_id,
                attempt_model.QuizAttempt.student_id == student.id
            ).first()
            if existing:
                already_attempted = True
    
    now = datetime.now()
    status = "upcoming"
    if quiz.start_time and quiz.end_time:
        if now >= quiz.start_time and now <= quiz.end_time:
            status = "active"
        elif now > quiz.end_time:
            status = "ended"
    
    q_list = []
    for q in questions:
        item = {
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "marks": q.marks
        }
        if is_faculty:
            item["correct_option"] = q.correct_option
        q_list.append(item)
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "subject_id": quiz.subject_id,
        "section_id": quiz.section_id,
        "total_marks": quiz.total_marks,
        "start_time": quiz.start_time.isoformat() if quiz.start_time else None,
        "end_time": quiz.end_time.isoformat() if quiz.end_time else None,
        "status": status,
        "already_attempted": already_attempted,
        "questions": q_list
    }


@router.post("/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: int,
    data: QuizSubmitInput,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Student submits quiz answers. Auto-scored."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit quizzes")
    
    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    quiz = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check time window
    now = datetime.now()
    if quiz.start_time and now < quiz.start_time:
        raise HTTPException(status_code=400, detail="Quiz has not started yet")
    if quiz.end_time and now > quiz.end_time:
        raise HTTPException(status_code=400, detail="Quiz has ended")
    
    # Check duplicate
    existing = db.query(attempt_model.QuizAttempt).filter(
        attempt_model.QuizAttempt.quiz_id == quiz_id,
        attempt_model.QuizAttempt.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already attempted this quiz")
    
    # Auto-score
    questions = db.query(question_model.QuizQuestion).filter(
        question_model.QuizQuestion.quiz_id == quiz_id
    ).all()
    question_map = {q.id: q for q in questions}
    
    total_score = 0
    for ans in data.answers:
        q = question_map.get(ans.question_id)
        if q and ans.selected_option.lower() == q.correct_option.lower():
            total_score += q.marks
    
    # Create attempt
    attempt = attempt_model.QuizAttempt(
        quiz_id=quiz_id,
        student_id=student.id,
        marks_obtained=total_score,
        submitted_at=now
    )
    db.add(attempt)
    db.flush()
    
    # Save responses
    for ans in data.answers:
        resp = response_model.QuizResponse(
            attempt_id=attempt.id,
            question_id=ans.question_id,
            selected_option=ans.selected_option.lower()
        )
        db.add(resp)
    
    db.commit()
    
    return {
        "attempt_id": attempt.id,
        "marks_obtained": total_score,
        "total_marks": quiz.total_marks,
        "percentage": round(total_score / quiz.total_marks * 100, 1) if quiz.total_marks > 0 else 0
    }


@router.get("/{quiz_id}/results")
async def get_quiz_results(
    quiz_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all attempts for a quiz with student names (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    quiz = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    attempts = db.query(attempt_model.QuizAttempt).filter(
        attempt_model.QuizAttempt.quiz_id == quiz_id
    ).all()
    
    results = []
    for a in attempts:
        student = db.query(student_model.Student).filter(student_model.Student.id == a.student_id).first()
        name = "Unknown"
        enrollment = ""
        if student:
            enrollment = student.enrollment_number or ""
            if student.user:
                name = student.user.username
        results.append({
            "attempt_id": a.id,
            "student_id": a.student_id,
            "student_name": name,
            "enrollment_number": enrollment,
            "marks_obtained": a.marks_obtained,
            "total_marks": quiz.total_marks,
            "percentage": round(a.marks_obtained / quiz.total_marks * 100, 1) if quiz.total_marks > 0 else 0,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None
        })
    return results


@router.delete("/{quiz_id}", status_code=200)
async def delete_quiz(
    quiz_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a quiz and all related data (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    quiz = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Delete responses for all attempts of this quiz
    attempts = db.query(attempt_model.QuizAttempt).filter(attempt_model.QuizAttempt.quiz_id == quiz_id).all()
    for a in attempts:
        db.query(response_model.QuizResponse).filter(response_model.QuizResponse.attempt_id == a.id).delete()
    
    db.query(attempt_model.QuizAttempt).filter(attempt_model.QuizAttempt.quiz_id == quiz_id).delete()
    db.query(question_model.QuizQuestion).filter(question_model.QuizQuestion.quiz_id == quiz_id).delete()
    db.delete(quiz)
    db.commit()
    
    return {"message": "Quiz deleted successfully"}
