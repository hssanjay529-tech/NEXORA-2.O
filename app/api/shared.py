import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.exceptions import NotFoundException
from app.dependencies.auth import get_current_user
from app.models.platform import User, File, BackgroundJob
from app.models.communication import Notification, NotificationDelivery
from app.schemas.platform import FileUploadRequest, FileUploadResponse, NotificationDeliveryOut, BackgroundJobOut

router = APIRouter(tags=["Shared Platform"])


# -----------------------------------------------------------------------------
# Files: Direct Upload Descriptor
# -----------------------------------------------------------------------------

@router.post("/files/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
def request_file_upload(
    payload: FileUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """POST /api/v1/files/upload - Generates upload descriptor and pre-signed S3/GCS URL."""
    file_id = uuid.uuid4()
    storage_key = f"{current_user.tenant_id}/uploads/{file_id}_{payload.filename}"

    file_rec = File(
        id=file_id,
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.id,
        storage_key=storage_key,
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        kind=payload.kind or "OTHER"
    )
    db.add(file_rec)
    db.commit()

    # In production, this would call AWS S3 or Google Cloud Storage client generate_presigned_url
    simulated_upload_url = f"https://storage.nexoracloud.com/upload/{storage_key}?token={uuid.uuid4()}"

    return FileUploadResponse(
        file_id=file_rec.id,
        storage_key=file_rec.storage_key,
        upload_url=simulated_upload_url,
        expires_in=3600
    )


# -----------------------------------------------------------------------------
# Notifications: Feed & Mark Read
# -----------------------------------------------------------------------------

@router.get("/notifications", response_model=List[Dict[str, Any]])
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GET /api/v1/notifications - User In-App Notification Feed."""
    deliveries = db.query(NotificationDelivery).join(Notification).filter(
        NotificationDelivery.tenant_id == current_user.tenant_id,
        NotificationDelivery.user_id == current_user.id,
        NotificationDelivery.read_at.is_(None)
    ).order_by(NotificationDelivery.sent_at.desc()).all()

    return [{
        "delivery_id": str(d.id),
        "notification_id": str(d.notification_id),
        "title": d.notification.title,
        "message": d.notification.message,
        "event_type": d.notification.event_type,
        "sent_at": d.sent_at,
        "channel": d.channel,
        "status": d.status
    } for d in deliveries]


@router.patch("/notifications/{delivery_id}/read", response_model=Dict[str, Any])
def mark_notification_read(
    delivery_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """PATCH /api/v1/notifications/{id}/read - Mark Notification as Read."""
    delivery = db.query(NotificationDelivery).filter(
        NotificationDelivery.tenant_id == current_user.tenant_id,
        NotificationDelivery.id == delivery_id,
        NotificationDelivery.user_id == current_user.id
    ).first()
    if not delivery:
        raise NotFoundException("Notification delivery not found")

    delivery.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "message": "Notification marked as read"}


# -----------------------------------------------------------------------------
# Background Jobs: Status Polling
# -----------------------------------------------------------------------------

@router.get("/background-jobs/{job_id}", response_model=Dict[str, Any])
def get_background_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GET /api/v1/background-jobs/{id} - Poll Async Background Job Status."""
    job = db.query(BackgroundJob).filter(
        BackgroundJob.tenant_id == current_user.tenant_id,
        BackgroundJob.id == job_id
    ).first()
    if not job:
        raise NotFoundException("Background job not found")

    return {
        "job_id": str(job.id),
        "job_type": job.job_type,
        "status": job.status,
        "attempts": job.attempts,
        "payload": job.payload,
        "last_error": job.last_error,
        "run_at": job.run_at,
        "created_at": job.created_at
    }
