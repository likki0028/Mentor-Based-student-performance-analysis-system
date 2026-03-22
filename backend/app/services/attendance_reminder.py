"""
Daily attendance reminder service.
Runs at 2 PM every day. Checks if faculty have posted attendance
for today's date. If not, sends them an email reminder.
"""
from datetime import date
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.faculty import Faculty, FacultyAssignment
from ..models.attendance import Attendance
from ..models import user as user_model
from ..models import subject as subject_model
from ..models import section as section_model
from ..services.email_service import send_email
import logging

logger = logging.getLogger(__name__)


def check_and_remind_attendance(db: Session = None):
    """Check if faculty have posted attendance today. Email reminders to those who haven't."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        today = date.today()
        reminders_sent = 0

        # Get all faculty assignments (faculty -> subject + section mappings)
        faculty_assignments = db.query(FacultyAssignment).all()

        # Group assignments by faculty_id
        faculty_map = {}
        for fa in faculty_assignments:
            if fa.faculty_id not in faculty_map:
                faculty_map[fa.faculty_id] = []
            faculty_map[fa.faculty_id].append(fa)

        for faculty_id, assignments in faculty_map.items():
            # Get faculty details
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
            if not faculty or not faculty.user:
                continue

            user = faculty.user
            if not user.email:
                continue

            # Check each subject this faculty teaches
            missing_subjects = []
            for fa in assignments:
                # Check if ANY attendance record exists for this subject + today
                has_attendance = db.query(Attendance).filter(
                    Attendance.subject_id == fa.subject_id,
                    Attendance.date == today
                ).first()

                if not has_attendance:
                    # Get subject and section names for the email
                    subject = db.query(subject_model.Subject).filter(
                        subject_model.Subject.id == fa.subject_id
                    ).first()
                    section = db.query(section_model.Section).filter(
                        section_model.Section.id == fa.section_id
                    ).first()

                    if subject:
                        subj_info = f"{subject.name} ({subject.code})"
                        if section:
                            subj_info += f" — Section {section.name}"
                        missing_subjects.append(subj_info)

            # If there are missing subjects, send ONE email with all of them
            if missing_subjects:
                subject_list = "\n• ".join(missing_subjects)
                send_email(
                    to_email=user.email,
                    title="Attendance Reminder",
                    message=(
                        f"Hi {user.username},\n\n"
                        f"You have not yet posted attendance for the following subjects today ({today.strftime('%d %b %Y')}):\n\n"
                        f"• {subject_list}\n\n"
                        f"Please mark attendance at your earliest convenience."
                    ),
                    link="http://localhost:5173/faculty/attendance",
                    priority="medium"
                )
                reminders_sent += 1
                logger.info(f"Attendance reminder sent to {user.username} for {len(missing_subjects)} subjects")

        logger.info(f"Attendance reminder check complete: {reminders_sent} reminders sent")
        return reminders_sent

    except Exception as e:
        logger.error(f"Error in attendance reminder: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        if own_session:
            db.close()
