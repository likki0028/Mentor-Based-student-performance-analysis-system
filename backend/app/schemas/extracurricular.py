from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class ExtracurricularBase(BaseModel):
    title: str
    description: Optional[str] = None
    issue_date: date

class ExtracurricularCreate(ExtracurricularBase):
    pass

class ExtracurricularUpdate(ExtracurricularBase):
    title: Optional[str] = None
    issue_date: Optional[date] = None

class Extracurricular(ExtracurricularBase):
    id: int
    student_id: int
    file_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
