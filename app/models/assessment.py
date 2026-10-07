import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Numeric, Boolean, Date,
    DateTime, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Attendance(Base):
    __tablename__ = 'attendance'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    att_date = Column(Date, nullable=False)
    status = Column(Text, nullable=False)  # PRESENT, ABSENT, LATE, EXCUSED
    marked_by = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='SET NULL'))
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    offering = relationship("CourseOffering")
    student = relationship("Student")


class Assignment(Base):
    __tablename__ = 'assignments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    kind = Column(Text, nullable=False)  # ASSIGNMENT, QUIZ
    title = Column(Text, nullable=False)
    description = Column(Text)
    due_at = Column(DateTime(timezone=True), nullable=False)
    max_marks = Column(Numeric(5, 2), default=100.00, nullable=False)
    rubric_file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    status = Column(Text, default='PUBLISHED', nullable=False)  # DRAFT, PUBLISHED, CLOSED, GRADED
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    offering = relationship("CourseOffering")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    quiz_questions = relationship("QuizQuestion", back_populates="assignment", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSONB, default=list, nullable=False)
    correct_answer = Column(Text, nullable=False)
    marks = Column(Numeric(5, 2), default=1.00, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    assignment = relationship("Assignment", back_populates="quiz_questions")


class AssignmentSubmission(Base):
    __tablename__ = 'assignment_submissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    answers = Column(JSONB, default=dict)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    marks = Column(Numeric(5, 2))
    feedback = Column(Text)
    graded_by = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='SET NULL'))
    status = Column(Text, default='SUBMITTED', nullable=False)  # SUBMITTED, GRADED, LATE, RESUBMISSION_REQUESTED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student")


class GradingScale(Base):
    __tablename__ = 'grading_scales'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    grade = Column(Text, nullable=False)
    min_marks = Column(Numeric(5, 2), nullable=False)
    max_marks = Column(Numeric(5, 2), nullable=False)
    grade_points = Column(Numeric(4, 2), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class GradeRecord(Base):
    __tablename__ = 'grade_records'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    internal_marks = Column(Numeric(5, 2), default=0.00)
    final_marks = Column(Numeric(5, 2), default=0.00)
    grade = Column(Text)
    grade_points = Column(Numeric(4, 2))
    status = Column(Text, default='DRAFT', nullable=False)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    submitted_by = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='SET NULL'))
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    offering = relationship("CourseOffering")


class StudentTermResult(Base):
    __tablename__ = 'student_term_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False)
    sgpa = Column(Numeric(4, 2), nullable=False)
    cgpa = Column(Numeric(4, 2), nullable=False)
    credits_earned = Column(Integer, default=0, nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    term = relationship("Term")


class AcademicFlag(Base):
    __tablename__ = 'academic_flags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='SET NULL'))
    flag_type = Column(Text, nullable=False)  # ATTENDANCE, ACADEMIC, PLAGIARISM, MISCONDUCT, WELFARE, PERFORMANCE
    raised_by = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='RESTRICT'), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Text, default='OPEN', nullable=False)  # OPEN, IN_PROGRESS, RESOLVED, DISMISSED
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student")
    offering = relationship("CourseOffering")
    reporter = relationship("Faculty", foreign_keys=[raised_by])
