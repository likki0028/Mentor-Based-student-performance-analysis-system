from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class StudentSummary(BaseModel):
    id: int
    name: str
    enrollment_number: str
    current_semester: int
    attendance_percentage: Optional[float] = 0.0
    risk_status: str = "Safe"
    
    class Config:
        from_attributes = True

class FacultyDashboard(BaseModel):
    total_students: int
    at_risk_count: int
    pending_tasks: int
    recent_alerts: List[str] = []

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
