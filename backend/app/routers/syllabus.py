
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import user as user_model
from ..models.syllabus_topic import SyllabusTopic
from ..dependencies import get_current_active_user

router = APIRouter()


class TopicCreate(BaseModel):
    title: str
    subject_id: int


@router.get("/subject/{subject_id}")
async def list_topics(
    subject_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    topics = db.query(SyllabusTopic).filter(
        SyllabusTopic.subject_id == subject_id
    ).order_by(SyllabusTopic.order).all()

    total = len(topics)
    completed = sum(1 for t in topics if t.is_completed)

    return {
        "topics": [
            {
                "id": t.id,
                "title": t.title,
                "is_completed": t.is_completed,
                "order": t.order
            }
            for t in topics
        ],
        "total": total,
        "completed": completed,
        "percentage": round((completed / total) * 100) if total > 0 else 0
    }


@router.post("/")
async def create_topic(
    data: TopicCreate,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get highest order
    last = db.query(SyllabusTopic).filter(
        SyllabusTopic.subject_id == data.subject_id
    ).order_by(SyllabusTopic.order.desc()).first()
    new_order = (last.order + 1) if last else 1

    topic = SyllabusTopic(
        title=data.title,
        subject_id=data.subject_id,
        order=new_order
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return {"id": topic.id, "message": "Topic added"}


@router.patch("/{topic_id}/toggle")
async def toggle_topic(
    topic_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    topic = db.query(SyllabusTopic).filter(SyllabusTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.is_completed = not topic.is_completed
    db.commit()
    return {"is_completed": topic.is_completed}


@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [user_model.UserRole.LECTURER, user_model.UserRole.ADMIN, user_model.UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    topic = db.query(SyllabusTopic).filter(SyllabusTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted"}
