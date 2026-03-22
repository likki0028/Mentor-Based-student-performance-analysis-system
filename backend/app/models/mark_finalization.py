
from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, DateTime
from ..database import Base
from datetime import datetime

class MarkFinalization(Base):
    __tablename__ = "mark_finalizations"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    assessment_type = Column(String, nullable=True)  # e.g. "mid_1", "mid_2", "end_term"
    is_finalized = Column(Boolean, default=False)
    finalized_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    finalized_at = Column(DateTime, nullable=True)
