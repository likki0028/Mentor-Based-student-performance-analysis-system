
from sqlalchemy import Column, Integer, String, Enum
from ..database import Base
import enum

class SubjectType(str, enum.Enum):
    THEORY = "THEORY"
    LAB = "LAB"
    NPTEL = "NPTEL"  # Open Elective - external NPTEL exam
    NON_CREDIT = "NON_CREDIT"

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    semester = Column(Integer, index=True)
    subject_type = Column(Enum(SubjectType), default=SubjectType.THEORY)
    credits = Column(Integer, default=3)
