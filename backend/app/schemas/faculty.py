from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class StudentSummary(BaseModel):
    id: int
    name: str
    enrollment_number: str
    current_semester: int
    attendance_percentage: Optional[float] = 0.0
    average_marks: Optional[float] = 0.0
    risk_status: str = "Safe"
    cgpa: Optional[float] = 0.0
    backlogs: Optional[int] = 0
    backlog_subjects: Optional[List[Any]] = []
    
    class Config:
        from_attributes = True

from . import alert as alert_schema

class FacultyDashboard(BaseModel):
    total_students: int
    at_risk_count: int
    recent_alerts: List[alert_schema.Alert] = []
    section_name: Optional[str] = None
    year: Optional[int] = None
    current_semester: Optional[int] = None

class SubjectSectionOut(BaseModel):
    subject_id: int
    subject_name: str
    subject_code: str
    section_id: int
    section_name: str

    class Config:
        from_attributes = True

class RemarkCreate(BaseModel):
    student_id: int
    message: str

class RemarkOut(BaseModel):
    id: int
    student_id: int
    faculty_id: int
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FacultyAssignmentCreate(BaseModel):
    faculty_id: int
    subject_id: int
    section_id: int

class FacultyAssignmentOut(FacultyAssignmentCreate):
    id: int
    
    class Config:
        from_attributes = True
