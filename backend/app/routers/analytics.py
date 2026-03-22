
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import user as user_model
from ..dependencies import get_current_active_user
from ..services.analytics_service import AnalyticsService
from ..services.ml_service import MLService

router = APIRouter()

@router.get("/student/{student_id}")
async def get_student_analytics(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for a student."""
    try:
        print("DEBUG: Calling AnalyticsService...")
        result = AnalyticsService.get_student_analytics(db, student_id)
        if not result:
            raise HTTPException(status_code=404, detail="Student not found")
        print("DEBUG: Service call successful! Type of result:", type(result))
        return result
    except Exception as e:
        import traceback
        print("DEBUG: EXCEPTION CAUGHT IN ROUTE:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/{student_id}")
async def predict_student_risk(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Predict risk status for a student using ML service."""
    result = MLService.predict_risk(db, student_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/batch-predict")
async def batch_predict_risk(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Predict risk for all students (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.ADMIN, user_model.UserRole.MENTOR, user_model.UserRole.LECTURER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return MLService.batch_predict(db)

@router.get("/gpa/{student_id}")
async def get_student_gpa(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get GPA for a student."""
    gpa = AnalyticsService.calculate_gpa(db, student_id)
    return {"student_id": student_id, "gpa": gpa}

@router.get("/predict-gpa/{student_id}")
async def predict_student_gpa(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Predict next semester SGPA for a student using ML model."""
    result = MLService.predict_gpa(db, student_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/batch-predict-gpa")
async def batch_predict_gpa(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Predict next semester GPA for all students (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.ADMIN, user_model.UserRole.MENTOR, user_model.UserRole.LECTURER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return MLService.batch_predict_gpa(db)


@router.get("/classroom/{subject_id}/{section_id}")
async def get_classroom_analytics(
    subject_id: int,
    section_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get classroom-level analytics for a subject/section."""
    from ..models import student as student_model
    from ..models import attendance as att_model
    from ..models import marks as marks_model
    from ..models import quiz as quiz_model
    from ..models import quiz_attempt as attempt_model

    students = db.query(student_model.Student).filter(
        student_model.Student.section_id == section_id
    ).all()
    student_ids = [s.id for s in students]
    if not student_ids:
        return {"attendance": [], "quiz_performance": [], "at_risk": [], "student_count": 0}

    # --- Attendance stats per student ---
    all_att = db.query(att_model.Attendance).filter(
        att_model.Attendance.student_id.in_(student_ids),
        att_model.Attendance.subject_id == subject_id
    ).all()

    att_by_student = {}
    for a in all_att:
        if a.student_id not in att_by_student:
            att_by_student[a.student_id] = {"present": 0, "total": 0}
        att_by_student[a.student_id]["total"] += 1
        if a.status:
            att_by_student[a.student_id]["present"] += 1

    # Attendance distribution for chart
    att_ranges = {"90-100%": 0, "75-89%": 0, "60-74%": 0, "<60%": 0}
    for sid in student_ids:
        data = att_by_student.get(sid, {"present": 0, "total": 0})
        pct = (data["present"] / data["total"] * 100) if data["total"] > 0 else 0
        if pct >= 90:
            att_ranges["90-100%"] += 1
        elif pct >= 75:
            att_ranges["75-89%"] += 1
        elif pct >= 60:
            att_ranges["60-74%"] += 1
        else:
            att_ranges["<60%"] += 1

    attendance_chart = [{"range": k, "count": v} for k, v in att_ranges.items()]

    # --- Quiz performance ---
    quizzes = db.query(quiz_model.Quiz).filter(quiz_model.Quiz.subject_id == subject_id).all()
    quiz_perf = []
    for q in quizzes:
        attempts = db.query(attempt_model.QuizAttempt).filter(
            attempt_model.QuizAttempt.quiz_id == q.id
        ).all()
        if attempts:
            avg_score = sum(a.marks_obtained for a in attempts) / len(attempts)
            avg_pct = (avg_score / q.total_marks * 100) if q.total_marks > 0 else 0
        else:
            avg_pct = 0
        quiz_perf.append({
            "quiz_title": q.title,
            "avg_percentage": round(avg_pct, 1),
            "attempts": len(attempts),
            "total_students": len(student_ids)
        })

    # --- At-risk students ---
    at_risk = []
    for s in students:
        name = s.user.username if s.user else "Unknown"
        att_data = att_by_student.get(s.id, {"present": 0, "total": 0})
        att_pct = (att_data["present"] / att_data["total"] * 100) if att_data["total"] > 0 else 100

        # Get avg quiz score
        student_attempts = db.query(attempt_model.QuizAttempt).filter(
            attempt_model.QuizAttempt.student_id == s.id,
            attempt_model.QuizAttempt.quiz_id.in_([q.id for q in quizzes])
        ).all() if quizzes else []

        quiz_avg = 0
        if student_attempts:
            quiz_scores = []
            for a in student_attempts:
                qz = next((q for q in quizzes if q.id == a.quiz_id), None)
                if qz and qz.total_marks > 0:
                    quiz_scores.append(a.marks_obtained / qz.total_marks * 100)
            quiz_avg = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0

        reasons = []
        if att_pct < 75:
            reasons.append(f"Low attendance ({round(att_pct)}%)")
        if quizzes and quiz_avg < 50:
            reasons.append(f"Low quiz avg ({round(quiz_avg)}%)")

        if reasons:
            at_risk.append({
                "student_id": s.id,
                "name": name,
                "enrollment": s.enrollment_number,
                "attendance_pct": round(att_pct),
                "quiz_avg_pct": round(quiz_avg),
                "reasons": reasons
            })

    return {
        "student_count": len(student_ids),
        "attendance_chart": attendance_chart,
        "quiz_performance": quiz_perf,
        "at_risk": at_risk
    }

