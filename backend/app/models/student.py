
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    enrollment_number = Column(String, unique=True, index=True)
    
    # Mentor relationship (Many students to one mentor)
    # mentor_id = Column(Integer, ForeignKey("faculty.id"))
    # mentor = relationship("Faculty", back_populates="mentees")

    # user = relationship("User", back_populates="student_profile")
