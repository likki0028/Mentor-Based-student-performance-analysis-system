from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import pytest

# Create a test client
client = TestClient(app)

def setup_module(module):
    # Reset database and create an admin user
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    admin_user = User(
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        hashed_password=get_password_hash("adminpassword"),
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.close()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Mentor-Based Student Performance System API"}

def test_login_admin():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    return data["access_token"]

def test_register_user():
    # Get admin token
    token = test_login_admin()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/auth/register",
        json={"username": "teststudent", "password": "password123", "email": "test@example.com", "role": "student"},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "teststudent"
    assert "id" in data

def test_login_user():
    # Login as the newly created user
    response = client.post(
        "/auth/login",
        data={"username": "teststudent", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_user():
    response = client.post(
        "/auth/login",
        data={"username": "wronguser", "password": "password123"}
    )
    assert response.status_code == 401

if __name__ == "__main__":
    setup_module(None)
    try:
        test_read_root()
        test_login_admin()
        test_register_user()
        test_login_user()
        test_login_invalid_user()
        print("All Phase 1 tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
