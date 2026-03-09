import sys
import os

# Add the parent directory of 'backend' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
# backend_dir = os.path.dirname(current_dir)
# sys.path.append(backend_dir)

from sqlalchemy import create_engine
from app.database import Base, engine
from app.models import user, student, faculty, subject, section, attendance, marks

try:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
except Exception as e:
    print("Error creating tables:")
    print(e)
