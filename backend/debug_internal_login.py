from app.database import SessionLocal
from app.models import user as user_model
from app.core.security import verify_password
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

def test_internal_login(username, password):
    db = SessionLocal()
    try:
        print(f"Searching for user: {username}")
        user = db.query(user_model.User).filter(user_model.User.username == username).first()
        
        if not user:
            print(f"User '{username}' NOT FOUND in DB via SQLAlchemy")
            return
        
        print(f"User found: ID={user.id}, Username={user.username}, Role={user.role}")
        print(f"Hashed Password in Model: {user.hashed_password}")
        
        is_valid = verify_password(password, user.hashed_password)
        print(f"Password '{password}' vs Hash: {is_valid}")
        
        if not user.is_active:
            print("User is NOT ACTIVE")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_internal_login("admin", "admin123")
    print("-" * 20)
    test_internal_login("student", "student123")
