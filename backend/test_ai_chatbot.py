import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import user as user_model
from app.services.chatbot_service import ChatbotService
from app.config import settings

# Test AI key directly
import google.generativeai as genai
try:
    print(f"Testing API Key: {settings.GOOGLE_API_KEY[:5]}...")
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello! Are you ready to be the Vibe Academic Assistant?")
    print(f"Initial AI Response: {response.text}")
    print("--- SUCCESS ---")
except Exception as e:
    print(f"ERROR: {str(e)}")

# Test Service Logic
db = SessionLocal()
try:
    student_user = db.query(user_model.User).filter(user_model.User.role == user_model.UserRole.STUDENT).first()
    if student_user:
        print(f"Testing for student: {student_user.username}")
        # Test a question that requires data context
        reply = ChatbotService.answer_question(db, student_user, "What is my attendance?")
        print(f"Assistant Reply: {reply}")
except Exception as e:
    print(f"Service Logic Error: {str(e)}")
finally:
    db.close()
