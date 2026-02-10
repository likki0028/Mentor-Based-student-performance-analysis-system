
from sqlalchemy import Column, Integer, ForeignKey, Enum
from ..database import Base
import enum

class AssessmentType(str, enum.Enum):
    MID_TERM = "mid_term"
    END_TERM = "end_term"
    INTERNAL = "internal"

class Marks(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    assessment_type = Column(Enum(AssessmentType))
    score = Column(Integer)
    total = Column(Integer)
