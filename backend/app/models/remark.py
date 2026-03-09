
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

class Remark(Base):
    __tablename__ = "remarks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    faculty = relationship("Faculty")
