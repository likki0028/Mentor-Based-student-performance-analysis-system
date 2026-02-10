
from fastapi import APIRouter

router = APIRouter()

@router.post("/mark")
def mark_attendance():
    # TODO: Implementation
    pass

@router.get("/{student_id}")
def get_attendance(student_id: int):
    # TODO: Implementation
    return []
