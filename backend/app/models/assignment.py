
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    due_date = Column(String)
    file_url = Column(String, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True) 
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
