
from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), index=True)
    date = Column(Date)
    status = Column(Boolean) # Present/Absent
    period = Column(Integer, nullable=True)  # Period number 1-7

    subject = relationship("Subject")
