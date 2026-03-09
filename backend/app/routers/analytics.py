
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
    result = AnalyticsService.get_student_analytics(db, student_id)
    if not result:
        raise HTTPException(status_code=404, detail="Student not found")
    return result

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
