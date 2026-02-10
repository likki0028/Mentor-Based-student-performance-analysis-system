
from sqlalchemy import Column, Integer, String
from ..database import Base

class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # e.g. "Section A"
    # year = Column(Integer)
