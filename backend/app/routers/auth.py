from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import user as user_model
from ..models import student as student_model
from ..models import faculty as faculty_model
from ..schemas import token
from ..schemas import user as user_schema
from ..core.security import verify_password, create_access_token
from ..config import settings
from ..dependencies import get_current_active_user, admin_only

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/login", response_model=token.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(user_model.User).filter(user_model.User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=201)
async def register_new_user(
    user_data: user_schema.UserCreate,
    db: Session = Depends(get_db),
    current_admin: user_model.User = Depends(admin_only)
):
    """Admin-only: Create a new user with optional student/faculty profile."""
    existing = db.query(user_model.User).filter(user_model.User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    from ..core.security import get_password_hash
    
    new_user = user_model.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_model.UserRole(user_data.role.value),
        is_active=True
    )
    db.add(new_user)
    db.flush()

    if user_data.role.value == "student":
        db.add(student_model.Student(
            user_id=new_user.id,
            enrollment_number=f"NEW{new_user.id}",
            current_semester=1
        ))
    elif user_data.role.value in ("mentor", "lecturer", "both"):
        db.add(faculty_model.Faculty(
            user_id=new_user.id,
            employee_id=f"FAC{new_user.id}"
        ))

    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role}

@router.post("/change-password")
async def change_password(
    current_password: str = "",
    new_password: str = "",
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change the current user's password."""
    from ..core.security import get_password_hash
    
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(new_password) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters")
    
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}
