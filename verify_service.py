"""Directly test the service triggers without hitting the API."""
import os
import sys

# Add backend/app to path
sys.path.append(os.path.abspath('backend'))

from backend.app.database import SessionLocal
from backend.app.models.notification import Notification, NotificationPriority, NotificationType
from backend.app.services import notification_service
from backend.app.models import student as student_model

db = SessionLocal()

def log(msg):
    print(f"--- {msg} ---")

try:
    log("Checking Section 2 students")
    students = db.query(student_model.Student).filter(student_model.Student.section_id == 2).all()
    print(f"Count: {len(students)}")
    uids = [s.user_id for s in students if s.user_id]
    print(f"User IDs: {uids}")

    if uids:
        log("Testing notify_bulk")
        notification_service.notify_bulk(
            db=db,
            user_ids=uids,
            title="Service Layer Test",
            message="Ensuring trigger logic is solid",
            notif_type=NotificationType.SYSTEM,
            priority=NotificationPriority.MEDIUM
        )
        print("Bulk notify done")
    
    log("Latest Notifications in DB")
    notifs = db.query(Notification).order_by(Notification.id.desc()).limit(5).all()
    for n in notifs:
        print(f"ID: {n.id}, User: {n.user_id}, Title: {n.title}")

finally:
    db.close()
