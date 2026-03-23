import os
from sqlalchemy import text
from app.database import engine

def add_backlogs_column():
    print("Adding backlogs column to students table...")
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN backlogs INTEGER DEFAULT 0"))
            print("Successfully added backlogs column.")
        except Exception as e:
            if "already exists" in str(e) or "Duplicate column" in str(e):
                print("Column already exists. Skipping.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    add_backlogs_column()
