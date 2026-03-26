"""
Core notification service — creates notifications and routes them by priority.
LOW    → In-App only
MEDIUM → In-App + Web Push
HIGH   → In-App + Web Push + Email
"""
from sqlalchemy.orm import Session
from ..models.notification import Notification, NotificationType, NotificationPriority, PushSubscription
from ..models import user as user_model
from ..services.email_service import send_email
import json


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notif_type: NotificationType = NotificationType.SYSTEM,
    priority: NotificationPriority = NotificationPriority.LOW,
    link: str = None,
) -> Notification:
    """Create a notification and route delivery based on priority."""

    # 1. Always create in-app notification
    from datetime import datetime
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        priority=priority,
        link=link,
        created_at=datetime.now(),
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # 2. Get user details for push/email
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()

    # 3. Medium or High → Web Push
    if priority in [NotificationPriority.MEDIUM, NotificationPriority.HIGH]:
        try:
            send_web_push(db, user_id, title, message, link)
        except Exception as e:
            print(f"Push failed for user {user_id}: {e}")

    # 4. High → Email
    if priority == NotificationPriority.HIGH:
        if user and user.email:
            try:
                send_email(
                    to_email=user.email,
                    title=title,
                    message=message,
                    link=link,
                    priority="high"
                )
            except Exception as e:
                print(f"Email failed for user {user_id}: {e}")

    return notif


def send_web_push(db: Session, user_id: int, title: str, body: str, link: str = None):
    """Send a web push notification to all subscribed browsers for a user."""
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        print("pywebpush not installed, skipping push notification")
        return

    subs = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()

    if not subs:
        print(f"No push subscriptions for user {user_id}")
        return

    # VAPID keys — generated once
    VAPID_PRIVATE_KEY = "SHYjTUbImpYP7UoD-G_ZTiPOKqzQY2K0BUFLspWDqvM"
    VAPID_CLAIMS = {"sub": "mailto:likhith23241a6796@grietcollege.com"}

    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": "/vite.svg",
        "url": link or "/"
    })

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
            print(f"✅ Push sent to user {user_id}")
        except Exception as e:
            print(f"❌ Push failed: {e}")
            # Remove stale subscription
            if "410" in str(e) or "404" in str(e):
                db.delete(sub)
                db.commit()


def notify_bulk(
    db: Session,
    user_ids: list[int],
    title: str,
    message: str,
    notif_type: NotificationType = NotificationType.SYSTEM,
    priority: NotificationPriority = NotificationPriority.LOW,
    link: str = None,
    background_tasks = None,
):
    """Send the same notification to multiple users.
    Uses bulk email (single SMTP connection) for HIGH priority."""
    from datetime import datetime
    from ..services.email_service import send_bulk_email

    email_recipients = []

    for uid in user_ids:
        # 1. Create in-app notification (fast — just DB insert)
        notif = Notification(
            user_id=uid,
            title=title,
            message=message,
            type=notif_type,
            priority=priority,
            link=link,
            created_at=datetime.now(),
        )
        db.add(notif)

        # 2. Collect email for HIGH priority
        if priority == NotificationPriority.HIGH:
            user = db.query(user_model.User).filter(user_model.User.id == uid).first()
            if user and user.email:
                email_recipients.append(user.email)

    db.commit()

    # 3. Send ONE bulk email (single SMTP connection for all recipients)
    if priority == NotificationPriority.HIGH and email_recipients:
        if background_tasks:
            background_tasks.add_task(
                send_bulk_email,
                recipients=email_recipients,
                title=title,
                message=message,
                link=link,
                priority="high"
            )
        else:
            send_bulk_email(
                recipients=email_recipients,
                title=title,
                message=message,
                link=link,
                priority="high"
            )
