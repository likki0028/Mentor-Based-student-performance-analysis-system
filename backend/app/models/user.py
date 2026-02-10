
from sqlalchemy import Boolean, Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    LECTURER = "lecturer"
    MENTOR = "mentor"
    STUDENT = "student"
    BOTH = "both"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True) # Optional
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    
    # Relationships
    # student_profile = relationship("Student", back_populates="user", uselist=False)
    # faculty_profile = relationship("Faculty", back_populates="user", uselist=False)
