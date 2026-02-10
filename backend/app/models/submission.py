
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from ..database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    submission_date = Column(Date)
    file_url = Column(String) # Placeholder
    grade = Column(Integer, nullable=True)
