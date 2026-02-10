
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from ..database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    due_date = Column(Date)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
