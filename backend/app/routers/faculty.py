
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_faculty():
    # TODO: Implementation
    return [{"id": 1, "name": "Faculty 1"}]
