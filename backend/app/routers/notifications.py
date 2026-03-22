
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from ..database import get_db
from ..models.notification import Notification, NotificationType, NotificationPriority, PushSubscription
from ..models import user as user_model
from ..dependencies import get_current_active_user
from ..services.notification_service import create_notification

router = APIRouter()


# --- Schemas ---
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: str
    priority: str
    is_read: bool
    link: Optional[str]
    created_at: str  # ISO string
    timestamp_ms: int  # epoch milliseconds for reliable time-ago


class PushSubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class TestNotificationIn(BaseModel):
    title: str = "Test Notification"
    message: str = "This is a test notification from MSPA System!"
    priority: str = "high"  # low, medium, high


# --- Routes ---

@router.get("/", response_model=List[NotificationOut])
async def get_notifications(
    limit: int = 50,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's notifications (newest first)."""
    notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(limit).all()

    import time
    results = []
    for n in notifs:
        ts_ms = int(n.created_at.timestamp() * 1000) if n.created_at else int(time.time() * 1000)
        results.append(NotificationOut(
            id=n.id,
            title=n.title,
            message=n.message,
            type=n.type.value if n.type else "system",
            priority=n.priority.value if n.priority else "low",
            is_read=n.is_read,
            link=n.link,
            created_at=str(n.created_at) if n.created_at else "",
            timestamp_ms=ts_ms
        ))
    return results


@router.get("/unread-count")
async def get_unread_count(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count for the bell badge."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a single notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.put("/read-all")
async def mark_all_read(
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.post("/subscribe")
async def subscribe_push(
    data: PushSubscriptionIn,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a Web Push subscription for the current user."""
    print(f"DEBUG: Subscribing user {current_user.username} (ID: {current_user.id})")
    print(f"DEBUG: Endpoint: {data.endpoint[:50]}...")
    
    try:
        # Check if exactly this endpoint is already registered (even for another user session)
        existing = db.query(PushSubscription).filter(
            PushSubscription.endpoint == data.endpoint
        ).first()
        
        if existing:
            # If it exists, just update the user_id to the current user and refresh keys
            existing.user_id = current_user.id
            existing.p256dh = data.p256dh
            existing.auth = data.auth
            print("DEBUG: Updated existing push subscription")
        else:
            sub = PushSubscription(
                user_id=current_user.id,
                endpoint=data.endpoint,
                p256dh=data.p256dh,
                auth=data.auth,
            )
            db.add(sub)
            print("DEBUG: Added new push subscription")
        print("DEBUG: Added to DB, committing...")
        db.commit()
        print("DEBUG: Commit successful")
        return {"message": "Push subscription saved"}
    except Exception as e:
        print(f"DEBUG: CRASH in subscribe_push: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def send_test_notification(
    data: TestNotificationIn,
    current_user: user_model.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a test notification to the current user (all 3 layers based on priority)."""
    from ..services.email_service import send_email as direct_send_email

    priority_map = {
        "low": NotificationPriority.LOW,
        "medium": NotificationPriority.MEDIUM,
        "high": NotificationPriority.HIGH,
    }
    priority = priority_map.get(data.priority, NotificationPriority.LOW)

    print(f"🔔 TEST NOTIFICATION: priority={data.priority}, user={current_user.username}, email={current_user.email}")

    notif = create_notification(
        db=db,
        user_id=current_user.id,
        title=data.title,
        message=data.message,
        notif_type=NotificationType.SYSTEM,
        priority=priority,
        link="http://localhost:5174/",
    )

    layers = ["In-App"]
    if priority in [NotificationPriority.MEDIUM, NotificationPriority.HIGH]:
        layers.append("Web Push")
    if priority == NotificationPriority.HIGH:
        layers.append("Email")
        # Directly send email here as a fallback
        if current_user.email:
            print(f"📧 Sending HIGH priority email to {current_user.email}...")
            try:
                result = direct_send_email(
                    to_email=current_user.email,
                    title=data.title,
                    message=data.message,
                    link="http://localhost:5174/",
                    priority="high"
                )
                print(f"📧 Email result: {result}")
            except Exception as e:
                print(f"❌ Email error: {e}")
        else:
            print(f"⚠️ No email found for user {current_user.username}")

    return {
        "message": f"Test notification sent via: {', '.join(layers)}",
        "notification_id": notif.id,
        "layers": layers
    }
