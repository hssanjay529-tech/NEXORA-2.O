import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Numeric, Boolean, Date, Time,
    DateTime, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Exam(Base):
    __tablename__ = 'exams'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    exam_type = Column(Text, nullable=False)  # MID_TERM, FINAL, LAB, RE_EXAM
    exam_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey('rooms.id', ondelete='SET NULL'))
    max_marks = Column(Numeric(5, 2), default=100.00, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    term = relationship("Term")
    offering = relationship("CourseOffering")
    room = relationship("Room")


class ExamEligibilityRule(Base):
    __tablename__ = 'exam_eligibility_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False)
    min_attendance_pct = Column(Numeric(5, 2), default=75.00, nullable=False)
    require_fees_cleared = Column(Boolean, default=True, nullable=False)
    extra_rules = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    term = relationship("Term")


class ExamRegistration(Base):
    __tablename__ = 'exam_registrations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    is_eligible = Column(Boolean, default=True, nullable=False)
    status = Column(Text, default='REGISTERED', nullable=False)  # REGISTERED, APPROVED, BLOCKED, CANCELLED
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    exam = relationship("Exam")
    student = relationship("Student")
    hall_ticket = relationship("HallTicket", back_populates="registration", uselist=False)


class HallTicket(Base):
    __tablename__ = 'hall_tickets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    registration_id = Column(UUID(as_uuid=True), ForeignKey('exam_registrations.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    ticket_no = Column(Text, nullable=False)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    registration = relationship("ExamRegistration", back_populates="hall_ticket")
    file = relationship("File")


class DocumentRequest(Base):
    __tablename__ = 'document_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    doc_type = Column(Text, nullable=False)  # BONAFIDE, TRANSCRIPT, GRADE_CARD, TRANSFER_CERTIFICATE, COURSE_COMPLETION, OTHER
    status = Column(Text, default='SUBMITTED', nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    verification_code = Column(Text, nullable=False)
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    file = relationship("File")
