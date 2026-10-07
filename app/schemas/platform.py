import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class FileUploadRequest(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int
    kind: Optional[str] = "OTHER"  # SYLLABUS, RUBRIC, SUBMISSION, RECEIPT, HALL_TICKET, etc.


class FileUploadResponse(BaseModel):
    file_id: uuid.UUID
    storage_key: str
    upload_url: str
    expires_in: int = 3600


class NotificationDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notification_id: uuid.UUID
    channel: str
    status: str
    sent_at: datetime
    read_at: Optional[datetime] = None
    title: str
    message: str
    event_type: str


class BackgroundJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_type: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED, RETRYING
    payload: Dict[str, Any]
    attempts: int
    last_error: Optional[str] = None
    run_at: datetime
    created_at: datetime
