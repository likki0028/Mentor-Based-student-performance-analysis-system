from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..database import Base
from datetime import datetime

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    file_url = Column(String)
    
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
