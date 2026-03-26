from sqlalchemy.orm import Session
from ..models.online_meeting import OnlineMeeting, MeetingPriority
from ..schemas.online_meeting import MeetingCreate
from ..models.student import Student
from ..models.faculty import Faculty
from ..services.notification_service import notify_bulk, NotificationType, NotificationPriority
from fastapi import HTTPException, BackgroundTasks

def delete_meeting(db: Session, meeting_id: int, faculty_user_id: int):
    faculty = db.query(Faculty).filter(Faculty.user_id == faculty_user_id).first()
    if not faculty:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_meeting = db.query(OnlineMeeting).filter(OnlineMeeting.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if db_meeting.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this meeting")
        
    db.delete(db_meeting)
    db.commit()
    return True

def create_meeting(db: Session, meeting_in: MeetingCreate, faculty_user_id: int, background_tasks: BackgroundTasks = None) -> OnlineMeeting:
    # Get faculty profile
    faculty = db.query(Faculty).filter(Faculty.user_id == faculty_user_id).first()
    if not faculty:
        raise HTTPException(status_code=403, detail="Only faculty can create meetings")

    # Create meeting
    db_meeting = OnlineMeeting(
        title=meeting_in.title,
        description=meeting_in.description,
        meeting_link=meeting_in.meeting_link,
        meeting_time=meeting_in.meeting_time,
        priority=meeting_in.priority,
        subject_id=meeting_in.subject_id,
        section_id=meeting_in.section_id,
        faculty_id=faculty.id
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)

    # Trigger notifications
    notify_students_of_meeting(db, db_meeting, background_tasks)

    return db_meeting

def notify_students_of_meeting(db: Session, meeting: OnlineMeeting, background_tasks: BackgroundTasks = None):
    query = db.query(Student)
    if meeting.section_id:
        query = query.filter(Student.section_id == meeting.section_id)
    
    students = query.all()
    user_ids = [s.user_id for s in students if s.user_id]
    
    if not user_ids:
        return
        
    priority_map = {
        MeetingPriority.NORMAL: NotificationPriority.MEDIUM,
        MeetingPriority.EMERGENCY: NotificationPriority.HIGH
    }
    
    title = f"{'🚨 EMERGENCY: ' if meeting.priority == MeetingPriority.EMERGENCY else ''}Online Meeting: {meeting.title}"
    message = f"An online meeting has been scheduled for {meeting.meeting_time.strftime('%b %d, %Y %I:%M %p')}.\n\n{meeting.description or ''}"
    
    notify_bulk(
        db=db,
        user_ids=user_ids,
        title=title,
        message=message,
        notif_type=NotificationType.ONLINE_MEETING, # type: ignore
        priority=priority_map[meeting.priority],
        link=meeting.meeting_link,
        background_tasks=background_tasks
    )
