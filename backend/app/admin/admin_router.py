
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..dependencies import admin_only, get_current_active_user
from ..models import user as user_model
from ..models import student as student_model
from ..models import faculty as faculty_model
from ..models import subject as subject_model
from ..models import attendance as attendance_model
from ..models import marks as marks_model
from ..core.security import get_password_hash

router = APIRouter()

# --- Schemas ---
class CreateUserRequest(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: str  # "student", "mentor", "lecturer", "admin"

class AssignMentorRequest(BaseModel):
    student_id: int
    mentor_id: int

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# --- Routes ---
@router.get("/stats")
async def get_system_stats(
    current_user: user_model.User = Depends(admin_only),
    db: Session = Depends(get_db)
):
    """Get system overview statistics."""
    total_students = db.query(student_model.Student).count()
    total_faculty = db.query(faculty_model.Faculty).count()
    total_users = db.query(user_model.User).count()
    total_subjects = db.query(subject_model.Subject).count()

    return {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_users": total_users,
        "total_subjects": total_subjects
    }

@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    current_user: user_model.User = Depends(admin_only),
    db: Session = Depends(get_db)
):
    """List all users with optional role filter."""
    query = db.query(user_model.User)
    if role:
        query = query.filter(user_model.User.role == role)
    users = query.order_by(user_model.User.id).all()

    result = []
    for u in users:
        user_data = {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active
        }
        # Add profile info
        if u.student_profile:
            user_data["enrollment_number"] = u.student_profile.enrollment_number
            user_data["current_semester"] = u.student_profile.current_semester
            user_data["mentor_id"] = u.student_profile.mentor_id
        if u.faculty_profile:
            user_data["employee_id"] = u.faculty_profile.employee_id
        result.append(user_data)

    return result

@router.post("/create-user", status_code=201)
async def create_user(
    data: CreateUserRequest,
    current_user: user_model.User = Depends(admin_only),
    db: Session = Depends(get_db)
):
    """Create a new user with appropriate profile."""
    existing = db.query(user_model.User).filter(
        user_model.User.username == data.username
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    role_map = {
        "student": user_model.UserRole.STUDENT,
        "mentor": user_model.UserRole.MENTOR,
        "lecturer": user_model.UserRole.LECTURER,
        "admin": user_model.UserRole.ADMIN,
        "both": user_model.UserRole.BOTH,
    }

    if data.role not in role_map:
        raise HTTPException(status_code=400, detail=f"Invalid role: {data.role}")

    new_user = user_model.User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=role_map[data.role],
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # Create profile based on role
    if data.role == "student":
        db.add(student_model.Student(
            user_id=new_user.id,
            enrollment_number=f"NEW{new_user.id}",
            current_semester=1
        ))
    elif data.role in ("mentor", "lecturer", "both"):
        db.add(faculty_model.Faculty(
            user_id=new_user.id,
            employee_id=f"FAC{new_user.id}"
        ))

    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: user_model.User = Depends(admin_only),
    db: Session = Depends(get_db)
):
    """Delete a user and their associated profile."""
    target = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Delete associated profiles
    if target.student_profile:
        # Clean up student-related data
        db.query(attendance_model.Attendance).filter(
            attendance_model.Attendance.student_id == target.student_profile.id
        ).delete()
        db.query(marks_model.Marks).filter(
            marks_model.Marks.student_id == target.student_profile.id
        ).delete()
        db.delete(target.student_profile)

    if target.faculty_profile:
        db.delete(target.faculty_profile)

    db.delete(target)
    db.commit()
    return {"message": f"User {target.username} deleted"}

@router.post("/assign-mentor")
async def assign_mentor(
    data: AssignMentorRequest,
    current_user: user_model.User = Depends(admin_only),
    db: Session = Depends(get_db)
):
    """Assign a mentor to a student."""
    student = db.query(student_model.Student).filter(
        student_model.Student.id == data.student_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    mentor = db.query(faculty_model.Faculty).filter(
        faculty_model.Faculty.id == data.mentor_id
    ).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    student.mentor_id = data.mentor_id
    db.commit()
    return {"message": f"Mentor assigned to student {student.enrollment_number}"}
