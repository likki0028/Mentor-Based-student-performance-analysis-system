import os
import google.generativeai as genai
from sqlalchemy.orm import Session
from .analytics_service import AnalyticsService
from ..config import settings
from .. import models

class ChatbotService:
    _model_initialized = False

    @classmethod
    def _initialize_model(cls):
        if not cls._model_initialized:
            api_key = settings.GOOGLE_API_KEY
            if not api_key:
                # Fallback to env just in case config hasn't reloaded
                api_key = os.getenv("GOOGLE_API_KEY")
            
            if api_key:
                genai.configure(api_key=api_key)
                cls._model_initialized = True
                return True
            return False
        return True

    @staticmethod
    def answer_question(db: Session, current_user, question: str):
        # Initialize Gemini
        if not ChatbotService._initialize_model():
            return "I'm currently in 'Offline Mode' because my AI engine isn't configured. Please check the GOOGLE_API_KEY."

        # Fetch student context
        student = db.query(models.student.Student).filter(
            models.student.Student.user_id == current_user.id
        ).first()
        
        context_str = ""
        if student:
            analytics = AnalyticsService.get_student_analytics(db, student.id)
            if analytics:
                # Build a concise context for the AI
                context_str = f"""
                Student Name: {analytics.get('name')}
                Enrollment: {analytics.get('enrollment_number')}
                Current Semester: {analytics.get('current_semester')}
                Overall Attendance: {analytics.get('attendance_percentage')}%
                CGPA: {analytics.get('cgpa')}
                Risk Status: {analytics.get('risk_status')}
                
                Subject-wise Performance:
                """
                for sub in analytics.get('subject_stats', []):
                    context_str += f"- {sub['subject_name']} ({sub['subject_code']}): Attendance {sub['attendance_percentage']}%, Sessional Marks: {sub['sessional_marks']}\n"
                
                # Add assignment info
                pending_assignments = []
                for sub in analytics.get('subject_stats', []):
                    if sub.get('assignment_count', 0) > sub.get('assignments_submitted', 0):
                        pending_assignments.append(sub['subject_name'])
                
                if pending_assignments:
                    context_str += f"\nPending Assignments in: {', '.join(pending_assignments)}"
                else:
                    context_str += "\nNo pending assignments."

        # Prepare the System Prompt
        system_prompt = f"""
        You are the "Vibe Academic Assistant," a helpful and professional AI integrated into a Student Performance Analysis system.
        
        YOUR CONTEXT:
        {context_str if context_str else "You are talking to a user, but their specific academic profile isn't available right now."}
        
        YOUR GOAL:
        1. Answer student or mentor questions naturally and concisely.
        2. If asked about academic performance, attendance, or risk, rely on the "YOUR CONTEXT" data above. Be specific (e.g., mention the exact % if asked).
        3. For general academic questions (e.g., "What is a Binary Tree?"), provide a clear, helpful explanation.
        4. Keep your tone encouraging but professional.
        5. If the context doesn't contain the answer (like specific exam dates not listed), politely say you don't have that specific information yet.
        6. Do not mention that you are a "Large Language Model" or "Gemini" unless explicitly asked. Just be the "Vibe Assistant".
        
        User Question: {question}
        """

        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(system_prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            return "I'm having a bit of trouble thinking right now (API Error). I'll be back soon!"
