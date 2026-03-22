
from sqlalchemy import Column, Integer, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class AssessmentType(str, enum.Enum):
    MID_TERM = "mid_term"       # Mid 1 (legacy)
    MID_1 = "mid_1"             # Mid-term 1 (30 marks)
    MID_2 = "mid_2"             # Mid-term 2 (30 marks)
    END_TERM = "end_term"       # External / End semester (entered by admin only)
    INTERNAL = "internal"       # Computed internal (legacy)
    ASSIGNMENT = "assignment"   # Assignment marks (5 marks)
    DAILY_ASSESSMENT = "daily_assessment"  # Daily assessment (5 marks)
    LAB_INTERNAL = "lab_internal"   # Lab internal exam (40 marks)
    LAB_EXTERNAL = "lab_external"   # Lab external exam (60 marks)

class Marks(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), index=True)
    assessment_type = Column(String)  # Stores values like 'mid_1', 'assignment', etc.
    score = Column(Integer)
    total = Column(Integer)
    label = Column(String, nullable=True)  # e.g., "Assignment 1", "Viva", "Program 1"

    subject = relationship("Subject")
