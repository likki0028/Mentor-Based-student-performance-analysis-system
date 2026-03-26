from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.online_meeting import MeetingPriority

class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    meeting_link: str
    meeting_time: datetime
    priority: MeetingPriority = MeetingPriority.NORMAL
    subject_id: int
    section_id: Optional[int] = None

class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    meeting_link: str
    meeting_time: datetime
    priority: MeetingPriority
    created_at: datetime
    subject_id: int
    section_id: Optional[int]
    faculty_id: int

    class Config:
        from_attributes = True
        orm_mode = True
