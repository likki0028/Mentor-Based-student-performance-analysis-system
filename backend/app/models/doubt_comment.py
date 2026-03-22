
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

class DoubtComment(Base):
    __tablename__ = "doubt_comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    doubt_id = Column(Integer, ForeignKey("doubts.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    doubt = relationship("Doubt", back_populates="comments")
    user = relationship("User")
