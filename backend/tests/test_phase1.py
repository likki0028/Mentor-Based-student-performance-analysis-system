from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User
import pytest

# Create a test client
client = TestClient(app)

# Reset database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Mentor-Based Student Performance System API"}

def test_register_user():
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "password123", "email": "test@example.com", "role": "student"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login_user():
    # Login
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password123"}
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
    # Depending on implementation, might be 401 or 400. Auth service usually returns 401.
    assert response.status_code == 401

if __name__ == "__main__":
    # Manually run tests if executed as script
    try:
        test_read_root()
        test_register_user()
        test_login_user()
        test_login_invalid_user()
        print("All Phase 1 tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
