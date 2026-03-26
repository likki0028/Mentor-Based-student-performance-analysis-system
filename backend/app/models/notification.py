
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
import enum
from datetime import datetime


class NotificationType(str, enum.Enum):
    ATTENDANCE_ALERT = "attendance_alert"
    ASSIGNMENT_NEW = "assignment_new"
    MARKS_PUBLISHED = "marks_published"
    RISK_CHANGE = "risk_change"
    QUIZ_ACTIVE = "quiz_active"
    DEADLINE_REMINDER = "deadline_reminder"
    SUBMISSION_UPDATE = "submission_update"
    ONLINE_MEETING = "online_meeting"
    SYSTEM = "system"


class NotificationPriority(str, enum.Enum):
    LOW = "low"        # In-App only
    MEDIUM = "medium"  # In-App + Web Push
    HIGH = "high"      # In-App + Web Push + Email


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.SYSTEM)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.LOW)
    is_read = Column(Boolean, default=False)
    link = Column(String, nullable=True)  # Optional URL to navigate to
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    endpoint = Column(String, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")
