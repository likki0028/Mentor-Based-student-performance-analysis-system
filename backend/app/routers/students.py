
from fastapi import APIRouter, Depends
# from ..dependencies import get_current_user

router = APIRouter()

@router.get("/")
def get_students():
    # TODO: Implementation
    return [{"id": 1, "name": "Student 1"}]

@router.get("/{id}")
def get_student_detail(id: int):
    # TODO: Implementation
    return {"id": id, "name": "Detail"}
