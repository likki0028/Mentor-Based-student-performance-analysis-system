from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..schemas.online_meeting import MeetingCreate, MeetingResponse
from ..models.online_meeting import OnlineMeeting
from ..models.user import User
from ..database import get_db
from ..dependencies import get_current_active_user
from ..services.meeting_service import create_meeting, delete_meeting

router = APIRouter()

@router.delete("/{meeting_id}", status_code=204)
def delete_existing_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return delete_meeting(db, meeting_id, current_user.id)

@router.post("/", response_model=MeetingResponse, status_code=201)
def create_new_meeting(
    meeting: MeetingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return create_meeting(db, meeting, current_user.id, background_tasks)

@router.get("/subject/{subject_id}", response_model=List[MeetingResponse])
def get_meetings_for_subject(
    subject_id: int,
    section_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(OnlineMeeting).filter(OnlineMeeting.subject_id == subject_id)
    if section_id:
        query = query.filter(OnlineMeeting.section_id == section_id)
    return query.order_by(OnlineMeeting.meeting_time.desc()).all()
