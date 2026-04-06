from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class ExtracurricularCertificate(Base):
    __tablename__ = "extracurricular_certificates"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    issue_date = Column(Date, nullable=False)
    file_url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", backref="certificates")
