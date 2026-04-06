import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine, Base
from app.models import user as user_model
from app.models import student as student_model
from app.services.chatbot_service import ChatbotService

db = SessionLocal()
try:
    # Get a student user
    student_user = db.query(user_model.User).filter(user_model.User.role == user_model.UserRole.STUDENT).first()
    if not student_user:
        print("No student user found in database.")
    else:
        print(f"Testing for student: {student_user.username}")
        # Test a question
        reply = ChatbotService.answer_question(db, student_user, "What is my attendance?")
        print(f"Reply: {reply}")
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
