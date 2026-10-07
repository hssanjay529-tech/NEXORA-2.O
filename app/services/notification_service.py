import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.communication import Notification, NotificationDelivery
from app.models.platform import User


def send_system_notification(
    db: Session,
    tenant_id: uuid.UUID,
    title: str,
    message: str,
    event_type: str,
    target_role: Optional[str] = None,
    target_user_ids: Optional[List[uuid.UUID]] = None,
    offering_id: Optional[uuid.UUID] = None,
    sent_by: Optional[uuid.UUID] = None,
    channel: str = "IN_APP"
) -> Notification:
    """Inserts a notification and dispatches deliveries to recipients."""
    notification = Notification(
        tenant_id=tenant_id,
        sent_by=sent_by,
        offering_id=offering_id,
        event_type=event_type,
        target_role=target_role,
        title=title,
        message=message,
        sent_at=datetime.now(timezone.utc)
    )
    db.add(notification)
    db.flush()

    recipient_ids: List[uuid.UUID] = []
    if target_user_ids:
        recipient_ids = target_user_ids
    elif target_role:
        query = db.query(User.id).filter(
            User.tenant_id == tenant_id,
            User.status == 'ACTIVE',
            User.deleted_at.is_(None)
        )
        if target_role != "ALL":
            query = query.filter(User.role == target_role)
        users = query.all()
        recipient_ids = [u[0] for u in users]

    for uid in recipient_ids:
        delivery = NotificationDelivery(
            tenant_id=tenant_id,
            notification_id=notification.id,
            user_id=uid,
            channel=channel,
            status='DELIVERED',
            sent_at=datetime.now(timezone.utc)
        )
        db.add(delivery)

    db.flush()
    return notification
