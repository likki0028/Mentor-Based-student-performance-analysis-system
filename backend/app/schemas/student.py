from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class AttendanceBase(BaseModel):
    date: date
    status: bool 
    subject_name: Optional[str] = None

class AttendanceOut(AttendanceBase):
    id: int
    class Config:
        from_attributes = True

class MarkOut(BaseModel):
    id: int
    subject_id: int
    subject_name: Optional[str] = None
    semester: Optional[int] = None
    assessment_type: str
    score: int
    total: int
    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    enrollment_number: str
    name: Optional[str] = None
    current_semester: Optional[int] = None
    backlogs: Optional[int] = 0

class StudentOut(StudentBase):
    id: int
    user_id: int
    # mentor_name: Optional[str] = None # Add back if mentor relationship is restored
    attendance_percentage: Optional[float] = None
    section_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class StudentDetail(StudentOut):
    attendance_records: List[AttendanceOut] = []
    marks: List[MarkOut] = []
