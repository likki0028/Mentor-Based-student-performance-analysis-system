
# Backend - Mentor-Based Student Performance System

## Setup

1. Create virtual environment: `python -m venv venv`
2. Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run server: `uvicorn app.main:app --reload`

## Structure

- `app/`: Core application code
- `app/models`: SQLAlchemy models
- `app/schemas`: Pydantic schemas
- `app/routers`: API endpoints
- `app/services`: Business logic
