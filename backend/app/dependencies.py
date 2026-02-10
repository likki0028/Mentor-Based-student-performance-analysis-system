
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .auth.jwt import verify_token
from .services.auth_service import get_user_by_username
from .models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login") # Corrected generic URL

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles and "both" not in self.allowed_roles: # Handle 'both' logic properly in roles if needed, currently straightforward check
             # If "both" is in allowed_roles, we might need specific logic, but assuming "both" is a role in UserRole enum or just a marker here.
             # Based on enum, 'both' is a role. If a user has 'both', they should probably access mentor/lecturer routes.
             # But here we check if user.role is in allowed_roles.
             # If user.role is 'both', and allowed_roles includes 'mentor', we need to successfully pass if user.role is 'both'.
             pass # Logic needs refinement based on specific "both" role handling or if "both" just implies they have that specific role string.
             # For now, let's keep it simple: strict match or if user.role is "both" and the endpoint allows "both" or specific roles.
        
        # Refined logic:
        # If the user has role "both", they should likely have access to "mentor" and "lecturer" routes.
        # So if user.role == "both", we should allow if 'mentor' or 'lecturer' are in allowed_roles?
        # Or does the user have role "both" and the route allows "mentor"?
        
        if user.role in self.allowed_roles:
            return user
        
        if user.role == "both" and ("mentor" in self.allowed_roles or "lecturer" in self.allowed_roles):
             return user

        raise HTTPException(status_code=403, detail="Operation not permitted")

admin_only = RoleChecker(["admin"])
lecturer_only = RoleChecker(["lecturer", "both"])
mentor_only = RoleChecker(["mentor", "both"])
student_only = RoleChecker(["student"])
