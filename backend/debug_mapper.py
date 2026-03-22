import traceback
try:
    from app.database import Base
    from app.models import user, faculty, subject, section, student, remark, material, marks, attendance, assignment, submission, alert, quiz, quiz_attempt
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    print("Mappers configured successfully!")
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
