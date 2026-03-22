
from sqlalchemy import Column, Integer, String, ForeignKey
from ..database import Base

class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    selected_option = Column(String, nullable=False)  # 'a', 'b', 'c', or 'd'
