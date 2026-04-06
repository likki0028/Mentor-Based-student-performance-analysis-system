from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Request
from sqlalchemy.orm import Session
import shutil
import os
import logging
import time

from ..database import get_db
from ..models import extracurricular as models
from ..models import student as student_model
from ..models import user as user_model
from ..schemas import extracurricular as schemas
from ..dependencies import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.Extracurricular, status_code=201)
async def upload_certificate(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    issue_date: str = Form(...),
    file: UploadFile = File(...),
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Student uploads an extracurricular certificate."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can upload certificates")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Validate file type (Images or PDF)
    allowed_exts = [".pdf", ".jpg", ".jpeg", ".png"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only PDF and Images (JPG, PNG) are allowed")

    # Parse date
    try:
        parsed_date = date.fromisoformat(issue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Save file
    upload_dir = "uploads/certificates"
    os.makedirs(upload_dir, exist_ok=True)
    
    safe_fname = file.filename.replace(" ", "_")
    save_name = f"cert_{student.id}_{int(time.time())}{file_ext}"
    file_path = os.path.join(upload_dir, save_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create record
    new_cert = models.ExtracurricularCertificate(
        student_id=student.id,
        title=title,
        description=description,
        issue_date=parsed_date,
        file_url=f"/{file_path}"
    )
    db.add(new_cert)
    db.commit()
    db.refresh(new_cert)

    return new_cert

@router.get("/me", response_model=List[schemas.Extracurricular])
async def get_my_certificates(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for the currently logged-in student."""
    if current_user.role != user_model.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view their own certificates")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        return []

    return db.query(models.ExtracurricularCertificate).filter(
        models.ExtracurricularCertificate.student_id == student.id
    ).order_by(models.ExtracurricularCertificate.issue_date.desc()).all()

@router.get("/student/{student_id}", response_model=List[schemas.Extracurricular])
async def get_student_certificates(
    student_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for a specific student (Mentor/Admin/Both access)."""
    if current_user.role not in [user_model.UserRole.MENTOR, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        # A student can only view their own via /me
        raise HTTPException(status_code=403, detail="Not authorized to view these certificates")

    return db.query(models.ExtracurricularCertificate).filter(
        models.ExtracurricularCertificate.student_id == student_id
    ).order_by(models.ExtracurricularCertificate.issue_date.desc()).all()

@router.delete("/{certificate_id}", status_code=200)
async def delete_certificate(
    certificate_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a certificate (Student owner only)."""
    cert = db.query(models.ExtracurricularCertificate).filter(
        models.ExtracurricularCertificate.id == certificate_id
    ).first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    
    if not student or cert.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this certificate")

    # Delete physical file
    file_path = cert.file_url.lstrip("/")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")

    db.delete(cert)
    db.commit()

    return {"message": "Certificate deleted successfully"}
