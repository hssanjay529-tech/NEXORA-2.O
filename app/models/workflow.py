import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Date, Time,
    DateTime, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class WorkflowInstance(Base):
    __tablename__ = 'workflow_instances'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = Column(Text, default='SUBMITTED', nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    current_step = Column(Text, default='HOD_APPROVAL', nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    transitions = relationship("WorkflowTransition", back_populates="instance", cascade="all, delete-orphan")


class WorkflowTransition(Base):
    __tablename__ = 'workflow_transitions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    instance_id = Column(UUID(as_uuid=True), ForeignKey('workflow_instances.id', ondelete='CASCADE'), nullable=False)
    from_status = Column(Text, nullable=False)
    to_status = Column(Text, nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    remarks = Column(Text)
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    instance = relationship("WorkflowInstance", back_populates="transitions")
    actor = relationship("User")


class CourseProposal(Base):
    __tablename__ = 'course_proposals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False)
    course_title = Column(Text, nullable=False)
    course_code = Column(Text, nullable=False)
    credits = Column(Integer, default=3, nullable=False)
    description = Column(Text)
    syllabus_file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    status = Column(Text, default='SUBMITTED', nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    reviewed_at = Column(DateTime(timezone=True))
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    faculty = relationship("Faculty")
    department = relationship("Department")


class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='CASCADE'), nullable=False)
    leave_type = Column(Text, nullable=False)  # CASUAL, SICK, EARNED, DUTY, MATERNITY, SABBATICAL
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Text, default='SUBMITTED', nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    approved_at = Column(DateTime(timezone=True))
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    faculty = relationship("Faculty")


class ScheduleChangeRequest(Base):
    __tablename__ = 'schedule_change_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='CASCADE'), nullable=False)
    slot_id = Column(UUID(as_uuid=True), ForeignKey('timetable_slots.id', ondelete='CASCADE'), nullable=False)
    requested_day = Column(Text, nullable=False)  # MONDAY, TUESDAY...
    requested_start = Column(Time, nullable=False)
    requested_end = Column(Time, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Text, default='SUBMITTED', nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    faculty = relationship("Faculty")
    slot = relationship("TimetableSlot")


class GrievanceTicket(Base):
    __tablename__ = 'grievance_tickets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    category = Column(Text, nullable=False)  # ACADEMIC, FINANCE, FACILITY, EXAMINATION, HARASSMENT, OTHER
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Text, default='OPEN', nullable=False)  # OPEN, IN_PROGRESS, WAITING_FOR_RESPONSE, RESOLVED, CLOSED, REJECTED
    priority = Column(Text, default='MEDIUM', nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    assignee = relationship("User")
