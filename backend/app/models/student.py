
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    enrollment_number = Column(String, unique=True, index=True)
    current_semester = Column(Integer, default=1)
    
    section_id = Column(Integer, ForeignKey("sections.id"))
    section = relationship("Section", backref="students")

    mentor_id = Column(Integer, ForeignKey("faculty.id"))
    mentor = relationship("Faculty", back_populates="mentees")

    user = relationship("User", back_populates="student_profile")
