
from sqlalchemy import Column, Integer, String, ForeignKey
from ..database import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    total_marks = Column(Integer)
