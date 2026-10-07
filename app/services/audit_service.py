import uuid
from typing import Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.platform import AuditLog


def log_audit_action(
    db: Session,
    tenant_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Creates an immutable audit log entry in the audit_logs table."""
    audit_entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        occurred_at=datetime.now(timezone.utc)
    )
    db.add(audit_entry)
    db.flush()
    return audit_entry
