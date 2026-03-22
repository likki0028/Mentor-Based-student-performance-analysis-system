import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.material import Material
from ..models.subject import Subject
from ..models.section import Section
from ..models.faculty import Faculty
from ..models import user as user_model
from .auth import get_current_active_user

router = APIRouter()

UPLOAD_DIR = "uploads/materials"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_material(
    title: str = Form(...),
    subject_id: int = Form(...),
    section_id: int = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.MENTOR, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized to upload materials")

    faculty_record = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty_record:
        raise HTTPException(status_code=403, detail="Faculty profile not found")

    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{subject_id}_{section_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_material = Material(
        title=title,
        description=description,
        file_url=f"/{file_path}",
        subject_id=subject_id,
        section_id=section_id,
        faculty_id=faculty_record.id
    )
    db.add(new_material)
    db.commit()
    db.refresh(new_material)
    return new_material

from ..models.student import Student

@router.get("/subject/{subject_id}")
async def get_materials(
    subject_id: int, 
    section_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if current_user.role == user_model.UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student or not student.section_id:
            return []
        section_id = student.section_id
    elif not section_id:
        raise HTTPException(status_code=400, detail="section_id is required for non-students")

    materials = db.query(Material).filter(
        Material.subject_id == subject_id,
        Material.section_id == section_id
    ).all()
    return materials

@router.get("/{material_id}")
async def get_material_detail(
    material_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

from pydantic import BaseModel
from typing import Optional

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

@router.put("/{material_id}")
async def update_material(
    material_id: int,
    data: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if data.title is not None:
        material.title = data.title
    if data.description is not None:
        material.description = data.description
    db.commit()
    db.refresh(material)
    return material

@router.delete("/{material_id}")
async def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    # Remove file from disk
    if material.file_url:
        file_path = material.file_url.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)
    # Delete related material files
    from ..models.material_file import MaterialFile as MaterialFileModel
    mat_files = db.query(MaterialFileModel).filter(MaterialFileModel.material_id == material_id).all()
    for mf in mat_files:
        fp = mf.file_url.lstrip("/")
        if os.path.exists(fp):
            os.remove(fp)
    db.query(MaterialFileModel).filter(MaterialFileModel.material_id == material_id).delete()
    db.delete(material)
    db.commit()
    return {"message": "Material deleted"}


# --- Material File Attachments ---
from ..models.material_file import MaterialFile as MaterialFileModel

@router.post("/{material_id}/attach-file", status_code=200)
async def attach_material_file(
    material_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Attach an additional file to an existing material."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_filename = f"mat_{material_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/{file_path}"
    if not material.file_url:
        material.file_url = file_url

    new_file = MaterialFileModel(
        material_id=material_id,
        file_url=file_url,
        filename=file.filename
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return {"message": "File attached", "file": {
        "id": new_file.id,
        "file_url": new_file.file_url,
        "filename": new_file.filename,
        "uploaded_at": new_file.uploaded_at
    }}


@router.get("/{material_id}/files")
async def list_material_files(
    material_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all files attached to a material."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    files = db.query(MaterialFileModel).filter(
        MaterialFileModel.material_id == material_id
    ).all()

    # If no files in material_files table but material has a file_url, create one
    if not files and material.file_url:
        filename = material.file_url.split("/")[-1] if material.file_url else "file"
        new_file = MaterialFileModel(
            material_id=material_id,
            file_url=material.file_url,
            filename=filename
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        files = [new_file]

    return [{
        "id": f.id,
        "file_url": f.file_url,
        "filename": f.filename,
        "uploaded_at": f.uploaded_at
    } for f in files]


@router.delete("/{material_id}/remove-file/{file_id}", status_code=200)
async def remove_material_file(
    material_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Remove a specific file from a material."""
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    file_record = db.query(MaterialFileModel).filter(
        MaterialFileModel.id == file_id,
        MaterialFileModel.material_id == material_id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove from disk
    fp = file_record.file_url.lstrip("/")
    if os.path.exists(fp):
        os.remove(fp)

    db.delete(file_record)

    # Update material's file_url to the next available file
    material = db.query(Material).filter(Material.id == material_id).first()
    if material:
        remaining = db.query(MaterialFileModel).filter(
            MaterialFileModel.material_id == material_id,
            MaterialFileModel.id != file_id
        ).first()
        material.file_url = remaining.file_url if remaining else None

    db.commit()
    return {"message": "File removed"}


