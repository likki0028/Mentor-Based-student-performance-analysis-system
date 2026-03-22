
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import marks as marks_model
from ..models import user as user_model
from ..models import student as student_model
from ..models import mark_finalization as mf_model
from ..dependencies import get_current_active_user
from ..services.alert_service import AlertService
from ..services import notification_service
from ..models.notification import NotificationPriority, NotificationType

router = APIRouter()

# --- Schemas ---
class MarkCreate(BaseModel):
    student_id: int
    subject_id: int
    assessment_type: str  # "mid_1", "mid_2", "end_term", "internal" etc.
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
    skipped = 0
    finalized_types = set()
    marks_notifications = []  # Collect for background notification

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

        # Check if this assessment type is finalized for the subject+section
        finalization = db.query(mf_model.MarkFinalization).filter(
            mf_model.MarkFinalization.subject_id == m.subject_id,
            mf_model.MarkFinalization.section_id == student.section_id,
            mf_model.MarkFinalization.assessment_type == assessment.value,
            mf_model.MarkFinalization.is_finalized == True
        ).first()

        if finalization:
            finalized_types.add(assessment.value)
            skipped += 1
            continue

        # Check if marks already exist for this student+subject+assessment
        existing = db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == m.student_id,
            marks_model.Marks.subject_id == m.subject_id,
            marks_model.Marks.assessment_type == assessment
        ).first()

        if existing:
            skipped += 1
            continue

        mark = marks_model.Marks(
            student_id=m.student_id,
            subject_id=m.subject_id,
            assessment_type=assessment,
            score=min(m.score, m.total),
            total=m.total
        )
        db.add(mark)
        created += 1

        # Collect info for background notification
        try:
            if student.user_id:
                subject = db.query(marks_model.subject_model.Subject).filter(
                    marks_model.subject_model.Subject.id == m.subject_id
                ).first()
                marks_notifications.append({
                    "user_id": student.user_id,
                    "subject": subject.name if subject else "Subject",
                    "assessment": m.assessment_type,
                    "score": mark.score,
                    "total": mark.total
                })
        except Exception as e:
            print(f"Failed to collect marks notif info: {e}")

    db.commit()
    
    # --- Send marks notifications in background ---
    if marks_notifications:
        import threading
        from ..database import SessionLocal
        _notifs = list(marks_notifications)

        def _send_marks_alerts():
            bg_db = SessionLocal()
            try:
                for info in _notifs:
                    notification_service.create_notification(
                        db=bg_db,
                        user_id=info["user_id"],
                        title="Marks Uploaded",
                        message=f"Your marks for {info['subject']} ({info['assessment']}) have been uploaded: {info['score']}/{info['total']}",
                        notif_type=NotificationType.SYSTEM,
                        priority=NotificationPriority.LOW,  # Bell only — fast
                        link="/student/marks"
                    )
            except Exception as e:
                print(f"BG marks notification error: {e}")
            finally:
                bg_db.close()

        threading.Thread(target=_send_marks_alerts, daemon=True).start()

    # Trigger automated alerts
    AlertService.generate_alerts(db)

    if finalized_types:
        return {
            "message": f"{created} marks records added, {skipped} skipped",
            "warning": f"The following assessment types are finalized and cannot be modified: {', '.join(finalized_types)}"
        }

    if skipped > 0:
        return {"message": f"{created} marks records added, {skipped} already exist (skipped)"}

    return {"message": f"{created} marks records added"}

@router.get("/{student_id}")
async def get_student_marks(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all marks for a student."""
    from sqlalchemy.orm import joinedload
    records = db.query(marks_model.Marks).options(
        joinedload(marks_model.Marks.subject)
    ).filter(
        marks_model.Marks.student_id == student_id
    ).all()

    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "subject_id": r.subject_id,
            "subject_name": r.subject.name if r.subject else "Unknown",
            "semester": r.subject.semester if r.subject else None,
            "assessment_type": r.assessment_type.value if hasattr(r.assessment_type, 'value') else r.assessment_type,
            "score": r.score,
            "total": r.total
        }
        for r in records
    ]

@router.get("/finalization/{subject_id}/{section_id}")
async def get_finalization_status(
    subject_id: int,
    section_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check which assessment types are finalized for a subject-section."""
    records = db.query(mf_model.MarkFinalization).filter(
        mf_model.MarkFinalization.subject_id == subject_id,
        mf_model.MarkFinalization.section_id == section_id,
        mf_model.MarkFinalization.is_finalized == True
    ).all()

    return [
        {
            "assessment_type": r.assessment_type,
            "finalized_at": r.finalized_at.isoformat() if r.finalized_at else None,
        }
        for r in records
    ]
