
from sqlalchemy import Column, Integer, ForeignKey
from ..database import Base

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    marks_obtained = Column(Integer)
