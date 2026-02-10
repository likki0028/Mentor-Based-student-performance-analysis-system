
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import admin_only
# from ..schemas.user import UserCreate

router = APIRouter()

@router.post("/create-user", dependencies=[Depends(admin_only)])
def create_user(db: Session = Depends(get_db)):
    # TODO: Admin only
    # 1. Check if user exists
    # 2. Hash temporary password
    # 3. Create user record
    # 4. Create related profile (Student or Faculty) based on role
    pass
