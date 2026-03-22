
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import user as user_model, student as student_model
from ..models.doubt import Doubt
from ..models.doubt_comment import DoubtComment
from ..dependencies import get_current_active_user

router = APIRouter()


class DoubtCreate(BaseModel):
    title: str
    content: str
    subject_id: int


class CommentCreate(BaseModel):
    content: str


@router.get("/subject/{subject_id}")
async def list_doubts(
    subject_id: int,
    resolved: Optional[bool] = None,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    q = db.query(Doubt).filter(Doubt.subject_id == subject_id)
    if resolved is not None:
        q = q.filter(Doubt.is_resolved == resolved)
    doubts = q.order_by(Doubt.is_pinned.desc(), Doubt.created_at.desc()).all()

    result = []
    for d in doubts:
        student_name = "Unknown"
        if d.student:
            student_name = d.student.user.username if d.student.user else "Unknown"
        comments = []
        for c in d.comments:
            comments.append({
                "id": c.id,
                "content": c.content,
                "user_name": c.user.username if c.user else "Unknown",
                "user_role": c.user.role.value if c.user else "unknown",
                "created_at": c.created_at.isoformat() if c.created_at else None
            })
        result.append({
            "id": d.id,
            "title": d.title,
            "content": d.content,
            "student_name": student_name,
            "is_resolved": d.is_resolved,
            "is_pinned": d.is_pinned,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "comment_count": len(comments),
            "comments": comments
        })
    return result


@router.post("/")
async def create_doubt(
    data: DoubtCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Find student_id from current user
    student = db.query(student_model.Student).filter(
        student_model.Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=400, detail="Only students can create doubts")

    doubt = Doubt(
        title=data.title,
        content=data.content,
        subject_id=data.subject_id,
        student_id=student.id
    )
    db.add(doubt)
    db.commit()
    db.refresh(doubt)
    return {"id": doubt.id, "message": "Doubt posted successfully"}


@router.post("/{doubt_id}/comments")
async def add_comment(
    doubt_id: int,
    data: CommentCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    doubt = db.query(Doubt).filter(Doubt.id == doubt_id).first()
    if not doubt:
        raise HTTPException(status_code=404, detail="Doubt not found")

    comment = DoubtComment(
        content=data.content,
        doubt_id=doubt_id,
        user_id=current_user.id
    )
    db.add(comment)
    db.commit()
    return {"message": "Comment added"}


@router.patch("/{doubt_id}/resolve")
async def toggle_resolve(
    doubt_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    doubt = db.query(Doubt).filter(Doubt.id == doubt_id).first()
    if not doubt:
        raise HTTPException(status_code=404, detail="Doubt not found")
    doubt.is_resolved = not doubt.is_resolved
    db.commit()
    return {"is_resolved": doubt.is_resolved}


@router.patch("/{doubt_id}/pin")
async def toggle_pin(
    doubt_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    doubt = db.query(Doubt).filter(Doubt.id == doubt_id).first()
    if not doubt:
        raise HTTPException(status_code=404, detail="Doubt not found")
    doubt.is_pinned = not doubt.is_pinned
    db.commit()
    return {"is_pinned": doubt.is_pinned}
