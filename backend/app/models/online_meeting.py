from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from ..database import Base
import enum
from datetime import datetime

class MeetingPriority(str, enum.Enum):
    NORMAL = "normal"
    EMERGENCY = "emergency"

class OnlineMeeting(Base):
    __tablename__ = "online_meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    meeting_link = Column(String)
    meeting_time = Column(DateTime)
    priority = Column(Enum(MeetingPriority), default=MeetingPriority.NORMAL)
    created_at = Column(DateTime, default=datetime.now)
    
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True) 
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
