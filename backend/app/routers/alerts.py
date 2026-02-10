
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_alerts():
    # TODO: Implementation
    return []

@router.post("/read/{id}")
def mark_alert_as_read(id: int):
    # TODO: Implementation
    pass
