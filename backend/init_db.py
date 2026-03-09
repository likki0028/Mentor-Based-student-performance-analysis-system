import sys
import os

# Add the current directory to sys.path to make sure we can import app
sys.path.append(os.getcwd())

from app.database import Base, engine
from app.models import (
    user,
    student,
    faculty,
    subject,
    section,
    attendance,
    marks,
    assignment,
    submission,
    quiz,
    quiz_attempt,
    alert
)

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()
