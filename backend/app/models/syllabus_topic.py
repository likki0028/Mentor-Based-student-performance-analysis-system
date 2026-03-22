
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from ..database import Base

class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    is_completed = Column(Boolean, default=False)
    order = Column(Integer, default=0)
