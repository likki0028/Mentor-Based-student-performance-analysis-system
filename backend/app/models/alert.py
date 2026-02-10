
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from ..database import Base
from datetime import datetime

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    type = Column(String) # e.g. "Low Attendance", "Low Marks"
