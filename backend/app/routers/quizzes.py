
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_quizzes():
    # TODO: Implementation
    return []

@router.post("/")
def create_quiz():
    # TODO: Implementation
    pass
