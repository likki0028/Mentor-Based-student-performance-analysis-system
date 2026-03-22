
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Request
from sqlalchemy.orm import Session
import shutil
import os
from pydantic import BaseModel
import logging
import traceback

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models import assignment as assignment_model
from ..models import submission as submission_model
from ..models import student as student_model
from ..models import user as user_model
from ..models.faculty import Faculty
from ..schemas import assignment as assignment_schema
from ..dependencies import get_current_active_user
from ..services import notification_service
from ..models.notification import NotificationPriority, NotificationType

router = APIRouter()

# --- Extra Schemas ---
class MyAssignmentPayload(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: str
    subject_id: int
    section_id: Optional[int] = None

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

class SubmissionDetailOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    student_name: str = "Unknown"
    enrollment_number: str = ""
    submission_date: date
    file_url: Optional[str] = None
    grade: Optional[int] = None

class GradeInput(BaseModel):
    grade: int

class ValidateInput(BaseModel):
    valid: bool

class AssignmentUpdatePayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None

# --- Routes ---
@router.get("/", response_model=List[assignment_schema.Assignment])
async def get_assignments(
    subject_id: Optional[int] = None,
    section_id: Optional[int] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all assignments, optionally filter by subject and section."""
    query = db.query(assignment_model.Assignment)
    
    if subject_id:
        query = query.filter(assignment_model.Assignment.subject_id == subject_id)
        
    if section_id:
        query = query.filter(assignment_model.Assignment.section_id == section_id)
        
    if current_user.role == user_model.UserRole.STUDENT:
        student = db.query(student_model.Student).filter(student_model.Student.user_id == current_user.id).first()
        if student and student.section_id:
            query = query.filter(assignment_model.Assignment.section_id == student.section_id)
            
    return query.order_by(assignment_model.Assignment.due_date.desc()).all()

@router.post("/", status_code=201)
async def create_assignment(
    data: MyAssignmentPayload,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new assignment (Faculty/Admin only). Use POST /assignments/{id}/attach-file to attach a file."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    faculty_record = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    f_id = faculty_record.id if faculty_record else None

    try:
        # Use dateutil.parser for maximum robustness across different browser formats
        import dateutil.parser
        parsed_due_date = dateutil.parser.parse(data.due_date)
        due_date_str = parsed_due_date.isoformat()
    except Exception as e:
        logger.error(f"Date parsing error for {data.due_date}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid due_date format: {e}")

    try:
        new_assignment = assignment_model.Assignment(
            title=data.title,
            description=data.description or "",
            due_date=due_date_str,
            subject_id=data.subject_id,
            section_id=data.section_id,
            faculty_id=f_id,
            file_url=None
        )
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during assignment creation: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # --- Notify Students (Background Thread) ---
    if new_assignment.section_id:
        try:
            students_in_section = db.query(student_model.Student).filter(
                student_model.Student.section_id == new_assignment.section_id
            ).all()
            student_user_ids = [s.user_id for s in students_in_section if s.user_id]
            
            if student_user_ids:
                import threading
                from ..database import SessionLocal

                _title = new_assignment.title
                _due = str(new_assignment.due_date)[:10]
                _id = new_assignment.id
                _uids = list(student_user_ids)

                def _send_notifications():
                    bg_db = SessionLocal()
                    try:
                        notification_service.notify_bulk(
                            db=bg_db,
                            user_ids=_uids,
                            title="New Assignment Posted",
                            message=f"A new assignment '{_title}' has been posted. Due date: {_due}",
                            notif_type=NotificationType.SYSTEM,
                            priority=NotificationPriority.HIGH,  # Email + Bell (runs in background thread)
                            link=f"/student/assignments/{_id}"
                        )
                    except Exception as e:
                        logger.error(f"BG notification error: {e}")
                    finally:
                        bg_db.close()

                threading.Thread(target=_send_notifications, daemon=True).start()
                logger.info(f"Notification queued for {len(student_user_ids)} students (assignment {new_assignment.id})")
        except Exception as e:
            logger.error(f"Failed to queue notifications: {e}")

    return {
        "id": new_assignment.id,
        "title": new_assignment.title,
        "description": new_assignment.description,
        "due_date": str(new_assignment.due_date),
        "subject_id": new_assignment.subject_id,
        "section_id": new_assignment.section_id,
        "file_url": new_assignment.file_url
    }
from ..models import assignment_file as assignment_file_model

@router.post("/{assignment_id}/attach-file", status_code=200)
async def attach_file_to_assignment(
    assignment_id: int,
    request: Request,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Attach a file to an existing assignment (supports multiple files)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    form = await request.form()
    file = form.get("file")
    
    if not file or not hasattr(file, 'filename') or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    upload_dir = "uploads/assignments"
    os.makedirs(upload_dir, exist_ok=True)
    safe_fname = file.filename.replace(" ", "_")
    # Use timestamp to avoid name collisions
    import time
    safe_filename = f"asm_{assignment_id}_{int(time.time())}_{safe_fname}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Also keep the legacy file_url column updated for backward compat
    file_url = f"/{file_path}"
    assignment.file_url = file_url
    
    # Insert into assignment_files table
    new_file = assignment_file_model.AssignmentFile(
        assignment_id=assignment_id,
        file_url=file_url,
        filename=file.filename
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {
        "id": new_file.id,
        "assignment_id": assignment_id,
        "file_url": new_file.file_url,
        "filename": new_file.filename,
        "uploaded_at": new_file.uploaded_at
    }

@router.get("/{assignment_id}/files")
async def list_assignment_files(
    assignment_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all files attached to an assignment."""
    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    files = db.query(assignment_file_model.AssignmentFile).filter(
        assignment_file_model.AssignmentFile.assignment_id == assignment_id
    ).all()

    return [
        {
            "id": f.id,
            "file_url": f.file_url,
            "filename": f.filename,
            "uploaded_at": f.uploaded_at
        }
        for f in files
    ]

@router.delete("/{assignment_id}/remove-file/{file_id}", status_code=200)
async def remove_file_from_assignment(
    assignment_id: int,
    file_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a specific file from an assignment."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    file_record = db.query(assignment_file_model.AssignmentFile).filter(
        assignment_file_model.AssignmentFile.id == file_id,
        assignment_file_model.AssignmentFile.assignment_id == assignment_id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Try to delete the physical file
    file_path = file_record.file_url.lstrip("/")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {e}")

    db.delete(file_record)
    
    # Update legacy file_url: set to latest remaining file or None
    remaining = db.query(assignment_file_model.AssignmentFile).filter(
        assignment_file_model.AssignmentFile.assignment_id == assignment_id,
        assignment_file_model.AssignmentFile.id != file_id
    ).first()
    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == assignment_id
    ).first()
    if assignment:
        assignment.file_url = remaining.file_url if remaining else None
    
    db.commit()

    return {"message": "File removed successfully"}

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

    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == data.assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

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

    # --- Notify Faculty (Background) ---
    if assignment.faculty_id:
        import threading
        from ..database import SessionLocal
        _fac_id = assignment.faculty_id
        _username = current_user.username
        _atitle = assignment.title
        _aid = assignment.id

        def _notify_faculty():
            bg_db = SessionLocal()
            try:
                fac = bg_db.query(Faculty).filter(Faculty.id == _fac_id).first()
                if fac and fac.user_id:
                    notification_service.create_notification(
                        db=bg_db,
                        user_id=fac.user_id,
                        title="New Assignment Submission",
                        message=f"Student {_username} submitted assignment: {_atitle}",
                        notif_type=NotificationType.SYSTEM,
                        priority=NotificationPriority.LOW,
                        link=f"/faculty/assignments/{_aid}"
                    )
            except Exception as e:
                logger.error(f"BG faculty notif error: {e}")
            finally:
                bg_db.close()

        threading.Thread(target=_notify_faculty, daemon=True).start()

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

@router.post("/upload/{assignment_id}", response_model=SubmissionOut, status_code=201)
async def upload_assignment(
    assignment_id: int,
    request: Request,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Student uploads a PDF for an assignment."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit assignments")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    form = await request.form()
    file = form.get("file")
    
    if not file or not hasattr(file, 'filename') or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    upload_dir = "uploads/assignments"
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    save_name = f"sub_{assignment_id}_{student.id}{file_ext}"
    file_path = os.path.join(upload_dir, save_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    existing = db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id == assignment_id,
        submission_model.Submission.student_id == student.id
    ).first()
    
    if existing:
        existing.submission_date = date.today()
        existing.file_url = file_path
        db.commit()
        db.refresh(existing)
        return existing

    submission = submission_model.Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        submission_date=date.today(),
        file_url=file_path
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

@router.patch("/grade/{submission_id}", response_model=SubmissionOut)
async def grade_submission(
    submission_id: int,
    data: GradeInput,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Faculty grades a student submission."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    submission = db.query(submission_model.Submission).filter(
        submission_model.Submission.id == submission_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.grade = data.grade
    db.commit()
    db.refresh(submission)
    return submission

@router.post("/validate/{submission_id}")
async def validate_submission(
    submission_id: int,
    data: ValidateInput,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate a student submission. Valid = grade 1, Invalid = grade 0."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    submission = db.query(submission_model.Submission).filter(
        submission_model.Submission.id == submission_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.grade = 1 if data.valid else 0
    db.commit()
    db.refresh(submission)
    return {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "grade": submission.grade,
        "validation_status": "valid" if submission.grade == 1 else "invalid"
    }

@router.get("/{assignment_id}/submissions")
async def get_submissions(
    assignment_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all submissions for an assignment with student details (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    submissions = db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id == assignment_id
    ).all()

    results = []
    for sub in submissions:
        student = db.query(student_model.Student).filter(student_model.Student.id == sub.student_id).first()
        student_name = "Unknown"
        enrollment_number = ""
        if student:
            enrollment_number = student.enrollment_number or ""
            if student.user:
                student_name = student.user.username
        
        # Determine validation status from grade
        if sub.grade is None:
            validation_status = "pending"
        elif sub.grade == 1:
            validation_status = "valid"
        else:
            validation_status = "invalid"
        
        results.append({
            "id": sub.id,
            "assignment_id": sub.assignment_id,
            "student_id": sub.student_id,
            "student_name": student_name,
            "enrollment_number": enrollment_number,
            "submission_date": str(sub.submission_date),
            "file_url": sub.file_url,
            "grade": sub.grade,
            "validation_status": validation_status,
        })
    return results

@router.get("/{assignment_id}")
async def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    assignment = db.query(assignment_model.Assignment).filter(assignment_model.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.get("/{assignment_id}/status")
async def get_assignment_status(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if current_user.role != user_model.UserRole.STUDENT:
        return {"detail": "Not a student"}
    
    student = db.query(student_model.Student).filter(student_model.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    submission = db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id == assignment_id,
        submission_model.Submission.student_id == student.id
    ).first()
    
    if not submission:
        return {"status": "missing", "submission": None}
        
    return {"status": "submitted", "submission": submission}


@router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    data: AssignmentUpdatePayload,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Edit an existing assignment (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if data.title is not None:
        assignment.title = data.title
    if data.description is not None:
        assignment.description = data.description
    if data.due_date is not None:
        try:
            import dateutil.parser
            parsed = dateutil.parser.parse(data.due_date)
            assignment.due_date = parsed.isoformat()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid due_date: {e}")

    db.commit()
    db.refresh(assignment)
    return {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "due_date": str(assignment.due_date),
        "subject_id": assignment.subject_id,
        "section_id": assignment.section_id,
        "file_url": assignment.file_url,
    }


@router.delete("/{assignment_id}", status_code=200)
async def delete_assignment(
    assignment_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an assignment, its submissions, files, and cascaded marks (Faculty/Admin only)."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    assignment = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    subject_id = assignment.subject_id
    section_id = assignment.section_id

    # Delete related submissions first
    db.query(submission_model.Submission).filter(
        submission_model.Submission.assignment_id == assignment_id
    ).delete()

    # Delete related assignment files
    db.query(assignment_file_model.AssignmentFile).filter(
        assignment_file_model.AssignmentFile.assignment_id == assignment_id
    ).delete()

    db.delete(assignment)
    db.flush()

    # Check if any assignments remain for this subject+section
    remaining_count = db.query(assignment_model.Assignment).filter(
        assignment_model.Assignment.subject_id == subject_id,
        assignment_model.Assignment.section_id == section_id
    ).count()

    marks_deleted = 0
    if remaining_count == 0 and section_id:
        # No more assignments — delete assignment marks for all students in this section
        from ..models.marks import Marks, AssessmentType
        students_in_section = db.query(student_model.Student.id).filter(
            student_model.Student.section_id == section_id
        ).all()
        student_ids = [s[0] for s in students_in_section]
        if student_ids:
            marks_deleted = db.query(Marks).filter(
                Marks.student_id.in_(student_ids),
                Marks.subject_id == subject_id,
                Marks.assessment_type == AssessmentType.ASSIGNMENT
            ).delete(synchronize_session='fetch')

    db.commit()

    msg = "Assignment deleted successfully"
    if marks_deleted > 0:
        msg += f". {marks_deleted} assignment marks also cleared (no assignments remaining)."
    return {"message": msg}
