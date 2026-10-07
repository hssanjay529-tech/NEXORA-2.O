import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Numeric, Date,
    DateTime, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class FeeStructure(Base):
    __tablename__ = 'fee_structures'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    programme_id = Column(UUID(as_uuid=True), ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False)
    name = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    programme = relationship("Programme")
    term = relationship("Term")


class Scholarship(Base):
    __tablename__ = 'scholarships'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name = Column(Text, nullable=False)
    kind = Column(Text, nullable=False)  # PERCENT, FIXED
    value = Column(Numeric(12, 2), nullable=False)
    criteria = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class StudentScholarship(Base):
    __tablename__ = 'student_scholarships'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    scholarship_id = Column(UUID(as_uuid=True), ForeignKey('scholarships.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False)
    awarded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    scholarship = relationship("Scholarship")
    term = relationship("Term")


class FeeRecord(Base):
    __tablename__ = 'fee_records'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey('fee_structures.id', ondelete='CASCADE'), nullable=False)
    amount_due = Column(Numeric(12, 2), nullable=False)
    discount = Column(Numeric(12, 2), default=0.00, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date)
    status = Column(Text, default='PENDING', nullable=False)  # PENDING, PAID, OVERDUE, PARTIAL, CANCELLED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    fee_structure = relationship("FeeStructure")
    payments = relationship("Payment", back_populates="fee_record")


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    fee_record_id = Column(UUID(as_uuid=True), ForeignKey('fee_records.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    method = Column(Text, nullable=False)  # CARD, UPI, NET_BANKING, CASH, CHEQUE, BANK_TRANSFER
    gateway_ref = Column(Text, nullable=False)
    status = Column(Text, default='INITIATED', nullable=False)  # INITIATED, VERIFIED, FAILED, REFUNDED
    verified_at = Column(DateTime(timezone=True))
    receipt_file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    fee_record = relationship("FeeRecord", back_populates="payments")
    receipt_file = relationship("File")
