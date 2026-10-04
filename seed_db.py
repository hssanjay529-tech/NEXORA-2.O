"""
NEXORA Database Seeding Script
==============================
Connects to local PostgreSQL (localhost:5432) and seeds realistic data for:
- 2 Colleges (Tenants)
- 2 Admins (1 per college)
- 10 Faculty Members (5 per college across various departments)
- 50 Students (25 per college across various programmes and departments)
- Full relational ecosystem: Academic Years, Terms, Departments, Programmes,
  Courses, Offerings, Rooms, Timetables, Enrollments, Attendance, Assignments,
  Grading Scales, Grade Records, Term Results, Fee Structures, Fee Records,
  Payments, Exams, Scholarships, Grievances, Flags, and Notifications.

Usage:
    python seed_db.py [--clean] [--database-url DATABASE_URL]
"""

import os
import sys
import uuid
import random
import argparse
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal

import bcrypt
from faker import Faker

from sqlalchemy import (
    create_engine,
    text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    String,
    Integer,
    Numeric,
    Boolean,
    Date,
    Time,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, CITEXT
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://nexora_admin:changeme123@localhost:5432/nexora",
)

# Standard password for all seeded demo users
DEFAULT_PASSWORD = "Password123!"
PASSWORD_HASH = bcrypt.hashpw(DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ==============================================================================
# SQLAlchemy Models
# ==============================================================================
class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ACTIVE")
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PlatformOperator(Base):
    __tablename__ = "platform_operators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ACTIVE")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)  # ADMIN, FACULTY, STUDENT
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ACTIVE")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        UniqueConstraint("tenant_id", "id", name="uq_users_tenant_id"),
    )


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    head_faculty_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    established_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_departments_tenant_name"),
        UniqueConstraint("tenant_id", "code", name="uq_departments_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_departments_tenant_id"),
    )


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    employee_no: Mapped[str] = mapped_column(Text, nullable=False)
    designation: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_faculty_tenant_user"),
        UniqueConstraint("tenant_id", "employee_no", name="uq_faculty_tenant_empno"),
        UniqueConstraint("tenant_id", "id", name="uq_faculty_tenant_id"),
    )


class Programme(Base):
    __tablename__ = "programmes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    duration_terms: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    degree_level: Mapped[str] = mapped_column(Text, nullable=False)  # UNDERGRADUATE, POSTGRADUATE, DIPLOMA, DOCTORATE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_programmes_tenant_name"),
        UniqueConstraint("tenant_id", "code", name="uq_programmes_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_programmes_tenant_id"),
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    programme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("programmes.id", ondelete="RESTRICT"), nullable=False)
    roll_no: Mapped[str] = mapped_column(Text, nullable=False)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    current_term_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ACTIVE")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_students_tenant_user"),
        UniqueConstraint("tenant_id", "roll_no", name="uq_students_tenant_rollno"),
        UniqueConstraint("tenant_id", "id", name="uq_students_tenant_id"),
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PUBLISHED")
    published_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "label", name="uq_academic_years_tenant_label"),
        UniqueConstraint("tenant_id", "id", name="uq_academic_years_tenant_id"),
    )


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    term_no: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    enrolment_opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enrolment_closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "academic_year_id", "term_no", name="uq_terms_tenant_ay_term"),
        UniqueConstraint("tenant_id", "id", name="uq_terms_tenant_id"),
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    course_code: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    syllabus_file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ACTIVE")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "course_code", name="uq_courses_tenant_course_code"),
        UniqueConstraint("tenant_id", "id", name="uq_courses_tenant_id"),
    )


class ProgrammeCourse(Base):
    __tablename__ = "programme_courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    programme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    term_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "programme_id", "course_id", name="uq_programme_courses_tenant_prog_course"),
        UniqueConstraint("tenant_id", "id", name="uq_programme_courses_tenant_id"),
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    room_type: Mapped[str] = mapped_column(Text, nullable=False, default="CLASSROOM")  # CLASSROOM, LAB, SEMINAR_HALL, AUDITORIUM
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    building: Mapped[str] = mapped_column(Text, nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_rooms_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_rooms_tenant_id"),
    )


class CourseOffering(Base):
    __tablename__ = "course_offerings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    section: Mapped[str] = mapped_column(Text, nullable=False, default="A")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "course_id", "term_id", "section", name="uq_course_offerings_tenant_combo"),
        UniqueConstraint("tenant_id", "id", name="uq_course_offerings_tenant_id"),
    )


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(Text, nullable=False)  # MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_timetable_slots_tenant_id"),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ENROLLED")  # ENROLLED, DROPPED, COMPLETED
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "offering_id", "student_id", name="uq_enrollments_tenant_offering_student"),
        UniqueConstraint("tenant_id", "id", name="uq_enrollments_tenant_id"),
    )


class GradingScale(Base):
    __tablename__ = "grading_scales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    grade: Mapped[str] = mapped_column(Text, nullable=False)
    min_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade_points: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "grade", name="uq_grading_scales_tenant_grade"),
        UniqueConstraint("tenant_id", "id", name="uq_grading_scales_tenant_id"),
    )


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    att_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PRESENT")  # PRESENT, ABSENT, LATE, EXCUSED
    marked_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "offering_id", "student_id", "att_date", name="uq_attendance_tenant_day"),
        UniqueConstraint("tenant_id", "id", name="uq_attendance_tenant_id"),
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="ASSIGNMENT")  # ASSIGNMENT, QUIZ
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=100.0)
    rubric_file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PUBLISHED")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_assignments_tenant_id"),
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSONB, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=5.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_quiz_questions_tenant_id"),
    )


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="GRADED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "assignment_id", "student_id", name="uq_assignment_submissions_tenant_assign_stu"),
        UniqueConstraint("tenant_id", "id", name="uq_assignment_submissions_tenant_id"),
    )


class GradeRecord(Base):
    __tablename__ = "grade_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    internal_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    final_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(Text, nullable=False)
    grade_points: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="COMPLETED")
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", "offering_id", name="uq_grade_records_tenant_student_offering"),
        UniqueConstraint("tenant_id", "id", name="uq_grade_records_tenant_id"),
    )


class StudentTermResult(Base):
    __tablename__ = "student_term_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    sgpa: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    cgpa: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    credits_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", "term_id", name="uq_student_term_results_tenant_student_term"),
        UniqueConstraint("tenant_id", "id", name="uq_student_term_results_tenant_id"),
    )


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    programme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_fee_structures_tenant_id"),
    )


class FeeRecord(Base):
    __tablename__ = "fee_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_structures.id", ondelete="RESTRICT"), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PAID")  # PENDING, PAID, OVERDUE, PARTIAL, CANCELLED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_fee_records_tenant_id"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    fee_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_records.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False, default="UPI")  # CARD, UPI, NET_BANKING, CASH, CHEQUE, BANK_TRANSFER
    gateway_ref: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="VERIFIED")  # INITIATED, VERIFIED, FAILED, REFUNDED
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    receipt_file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "gateway_ref", name="uq_payments_tenant_gateway_ref"),
        UniqueConstraint("tenant_id", "id", name="uq_payments_tenant_id"),
    )


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="PERCENT")  # PERCENT, FIXED
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_scholarships_tenant_name"),
        UniqueConstraint("tenant_id", "id", name="uq_scholarships_tenant_id"),
    )


class StudentScholarship(Base):
    __tablename__ = "student_scholarships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    scholarship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", "scholarship_id", "term_id", name="uq_student_scholarships_tenant_combo"),
        UniqueConstraint("tenant_id", "id", name="uq_student_scholarships_tenant_id"),
    )


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    exam_type: Mapped[str] = mapped_column(Text, nullable=False, default="FINAL")  # MID_TERM, FINAL, LAB, RE_EXAM
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=100.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_exams_tenant_id"),
    )


class ExamEligibilityRule(Base):
    __tablename__ = "exam_eligibility_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    min_attendance_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=75.0)
    require_fees_cleared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extra_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "term_id", name="uq_exam_eligibility_rules_tenant_term"),
        UniqueConstraint("tenant_id", "id", name="uq_exam_eligibility_rules_tenant_id"),
    )


class ExamRegistration(Base):
    __tablename__ = "exam_registrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="APPROVED")  # REGISTERED, APPROVED, BLOCKED, CANCELLED
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "exam_id", "student_id", name="uq_exam_registrations_tenant_exam_student"),
        UniqueConstraint("tenant_id", "id", name="uq_exam_registrations_tenant_id"),
    )


class AcademicFlag(Base):
    __tablename__ = "academic_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    offering_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="SET NULL"), nullable=True)
    flag_type: Mapped[str] = mapped_column(Text, nullable=False)  # ATTENDANCE, ACADEMIC, PLAGIARISM, MISCONDUCT, WELFARE, PERFORMANCE
    raised_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="RESOLVED")  # OPEN, IN_PROGRESS, RESOLVED, DISMISSED
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_academic_flags_tenant_id"),
    )


class GrievanceTicket(Base):
    __tablename__ = "grievance_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)  # ACADEMIC, FINANCE, FACILITY, EXAMINATION, HARASSMENT, OTHER
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="RESOLVED")  # OPEN, IN_PROGRESS, WAITING_FOR_RESPONSE, RESOLVED, CLOSED, REJECTED
    priority: Mapped[str] = mapped_column(Text, nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_grievance_tickets_tenant_id"),
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    leave_type: Mapped[str] = mapped_column(Text, nullable=False, default="CASUAL")  # CASUAL, SICK, EARNED, DUTY, MATERNITY, SABBATICAL
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="APPROVED")  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_leave_requests_tenant_id"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    sent_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    offering_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_role: Mapped[str | None] = mapped_column(Text, nullable=True)  # ADMIN, FACULTY, STUDENT, ALL
    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_notifications_tenant_id"),
    )


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    notification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False, default="IN_APP")  # IN_APP, EMAIL, SMS, PUSH
    status: Mapped[str] = mapped_column(Text, nullable=False, default="DELIVERED")  # PENDING, SENT, DELIVERED, FAILED
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_notification_deliveries_tenant_id"),
    )


# ==============================================================================
# Helper Data Generation Functions
# ==============================================================================

def clean_database(session):
    """Truncates all tenant tables safely to allow fresh seeding."""
    print("\n[i] Cleaning up existing tables...")
    truncate_sql = """
    TRUNCATE TABLE 
        workflow_transitions, workflow_instances,
        compliance_versions, compliance_records, analytics_reports,
        message_attachments, messages, conversation_participants, conversations,
        notification_deliveries, notifications, grievance_tickets,
        schedule_change_requests, leave_requests, course_proposals,
        document_requests, hall_tickets, exam_registrations, exam_eligibility_rules, exams,
        payments, fee_records, student_scholarships, scholarships, fee_structures,
        academic_flags, student_term_results, grade_records,
        assignment_submissions, quiz_questions, assignments, grading_scales,
        attendance, timetable_slots, course_materials, enrollments,
        course_offerings, programme_courses, courses, calendar_events,
        terms, academic_years, rooms, students, faculty, programmes,
        departments, login_attempts, user_tokens, audit_logs, background_jobs,
        files, users, platform_operators, tenants
    CASCADE;
    """
    session.execute(text(truncate_sql))
    session.commit()
    print("    Existing data wiped successfully.")


def seed_database(db_url: str, clean: bool = False):
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if clean:
            clean_database(session)

        print("\n" + "=" * 80)
        print("  NEXORA MULTI-TENANT DATABASE SEEDER")
        print("=" * 80)

        # ----------------------------------------------------------------------
        # 1. Platform Operator
        # ----------------------------------------------------------------------
        print("\n[*] Seeding Platform Operator...")
        operator = PlatformOperator(
            email="root@nexora.io",
            password_hash=PASSWORD_HASH,
            status="ACTIVE",
            last_login_at=datetime.now(timezone.utc),
        )
        session.add(operator)
        session.flush()

        # ----------------------------------------------------------------------
        # 2. Colleges (Tenants) - 2 Required
        # ----------------------------------------------------------------------
        print("[*] Seeding 2 Colleges (Tenants)...")
        tenant1 = Tenant(
            slug="apex-tech",
            name="Apex Institute of Technology & Management",
            status="ACTIVE",
            settings={
                "branding": {"primary_color": "#1e40af", "logo_url": None, "short_name": "APEX"},
                "currency": "INR",
                "timezone": "Asia/Kolkata",
                "thresholds": {"min_attendance_pct": 75.0, "passing_grade_pct": 40.0},
            },
        )
        tenant2 = Tenant(
            slug="horizon-univ",
            name="Horizon University of Engineering & Science",
            status="ACTIVE",
            settings={
                "branding": {"primary_color": "#047857", "logo_url": None, "short_name": "HUES"},
                "currency": "INR",
                "timezone": "Asia/Kolkata",
                "thresholds": {"min_attendance_pct": 80.0, "passing_grade_pct": 45.0},
            },
        )
        session.add_all([tenant1, tenant2])
        session.flush()

        # Define Standard Grading Scale for both colleges
        grading_data = [
            ("A+", Decimal("90.0"), Decimal("100.0"), Decimal("10.0"), "Outstanding"),
            ("A", Decimal("80.0"), Decimal("89.99"), Decimal("9.0"), "Excellent"),
            ("B+", Decimal("70.0"), Decimal("79.99"), Decimal("8.0"), "Very Good"),
            ("B", Decimal("60.0"), Decimal("69.99"), Decimal("7.0"), "Good"),
            ("C", Decimal("50.0"), Decimal("59.99"), Decimal("6.0"), "Average"),
            ("P", Decimal("40.0"), Decimal("49.99"), Decimal("4.0"), "Pass"),
            ("F", Decimal("0.0"), Decimal("39.99"), Decimal("0.0"), "Fail"),
        ]

        for tenant in [tenant1, tenant2]:
            for g, min_m, max_m, gp, desc in grading_data:
                gs = GradingScale(
                    tenant_id=tenant.id,
                    grade=g,
                    min_marks=min_m,
                    max_marks=max_m,
                    grade_points=gp,
                    description=desc,
                )
                session.add(gs)

        # ----------------------------------------------------------------------
        # 3. Admins (2 Admins Total: 1 per College)
        # ----------------------------------------------------------------------
        print("[*] Seeding 2 Admins (1 per college)...")
        admin1_user = User(
            tenant_id=tenant1.id,
            role="ADMIN",
            email="admin.apex@nexora.edu",
            first_name="Rajeshwar",
            last_name="Sharma",
            password_hash=PASSWORD_HASH,
            status="ACTIVE",
        )
        admin2_user = User(
            tenant_id=tenant2.id,
            role="ADMIN",
            email="admin.horizon@nexora.edu",
            first_name="Sunita",
            last_name="Kulkarni",
            password_hash=PASSWORD_HASH,
            status="ACTIVE",
        )
        session.add_all([admin1_user, admin2_user])
        session.flush()

        # ----------------------------------------------------------------------
        # 4. Academic Years & Terms
        # ----------------------------------------------------------------------
        print("[*] Seeding Academic Calendars & Terms...")
        terms_map = {}  # tenant_id -> list of terms
        for tenant, admin_user in [(tenant1, admin1_user), (tenant2, admin2_user)]:
            ay = AcademicYear(
                tenant_id=tenant.id,
                label="2025-26",
                start_date=date(2025, 8, 1),
                end_date=date(2026, 7, 31),
                status="PUBLISHED",
                published_by=admin_user.id,
                published_at=datetime.now(timezone.utc),
            )
            session.add(ay)
            session.flush()

            term_odd = Term(
                tenant_id=tenant.id,
                academic_year_id=ay.id,
                name="Fall Semester 2025 (Odd)",
                term_no=1,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 12, 20),
                enrolment_opens_at=datetime(2025, 7, 15, 0, 0, tzinfo=timezone.utc),
                enrolment_closes_at=datetime(2025, 8, 10, 23, 59, tzinfo=timezone.utc),
                is_current=False,
            )
            term_even = Term(
                tenant_id=tenant.id,
                academic_year_id=ay.id,
                name="Spring Semester 2026 (Even)",
                term_no=2,
                start_date=date(2026, 1, 10),
                end_date=date(2026, 5, 30),
                enrolment_opens_at=datetime(2025, 12, 15, 0, 0, tzinfo=timezone.utc),
                enrolment_closes_at=datetime(2026, 1, 20, 23, 59, tzinfo=timezone.utc),
                is_current=True,
            )
            session.add_all([term_odd, term_even])
            session.flush()
            terms_map[tenant.id] = [term_odd, term_even]

            # Exam Eligibility Rule for Current Term
            elig_rule = ExamEligibilityRule(
                tenant_id=tenant.id,
                term_id=term_even.id,
                min_attendance_pct=Decimal("75.0"),
                require_fees_cleared=True,
            )
            session.add(elig_rule)

        # ----------------------------------------------------------------------
        # 5. Rooms for each college
        # ----------------------------------------------------------------------
        rooms_map = {}
        for tenant in [tenant1, tenant2]:
            rooms_list = []
            for b_idx, building in enumerate(["Aryabhata Block", "Ramanujan Tower"]):
                for fl in range(1, 4):
                    for rm_num in range(1, 3):
                        code = f"{building[:3].upper()}-{fl}0{rm_num}"
                        room_type = "LAB" if rm_num == 2 else "CLASSROOM"
                        cap = 40 if room_type == "LAB" else 60
                        room = Room(
                            tenant_id=tenant.id,
                            code=code,
                            room_type=room_type,
                            capacity=cap,
                            building=building,
                            floor=fl,
                        )
                        session.add(room)
                        rooms_list.append(room)
            session.flush()
            rooms_map[tenant.id] = rooms_list

        # ----------------------------------------------------------------------
        # 6. Departments, Programmes, and 10 Faculty Members (5 per college)
        # ----------------------------------------------------------------------
        print("[*] Seeding Departments, Programmes, and 10 Faculty members across colleges...")

        # College 1 Setup (Apex Institute)
        # 3 Departments: CSE, ECE, MECH
        dept_configs_t1 = [
            ("Department of Computer Science & Engineering", "CSE", Decimal("5000000.00"), [
                ("B.Tech in Computer Science & Engineering", "BTECH-CSE", 8, "UNDERGRADUATE"),
                ("M.Tech in Artificial Intelligence", "MTECH-AI", 4, "POSTGRADUATE"),
            ]),
            ("Department of Electronics & Communication", "ECE", Decimal("4000000.00"), [
                ("B.Tech in Electronics & Communication", "BTECH-ECE", 8, "UNDERGRADUATE"),
            ]),
            ("Department of Mechanical Engineering", "MECH", Decimal("3500000.00"), [
                ("B.Tech in Mechanical Engineering", "BTECH-MECH", 8, "UNDERGRADUATE"),
            ]),
        ]

        # Faculty 1 to 5 for College 1
        faculty_meta_t1 = [
            ("Arvind", "Menon", "prof.menon@apex.edu", "Professor & HOD", "CSE"),
            ("Ananya", "Iyer", "dr.ananya@apex.edu", "Associate Professor", "CSE"),
            ("Vikram", "Joshi", "prof.joshi@apex.edu", "Professor & HOD", "ECE"),
            ("Priyanka", "Deshmukh", "dr.priyanka@apex.edu", "Assistant Professor", "ECE"),
            ("Suresh", "Nambiar", "prof.nambiar@apex.edu", "Professor & HOD", "MECH"),
        ]

        # College 2 Setup (Horizon University)
        # 3 Departments: ITAI, DSA, BMS
        dept_configs_t2 = [
            ("Department of Information Technology & AI", "ITAI", Decimal("6000000.00"), [
                ("B.Tech in Artificial Intelligence & Data Science", "BTECH-AIDS", 8, "UNDERGRADUATE"),
            ]),
            ("Department of Data Science & Analytics", "DSA", Decimal("4500000.00"), [
                ("M.Tech in Data Analytics & Machine Learning", "MTECH-DA", 4, "POSTGRADUATE"),
            ]),
            ("Department of Business & Management Studies", "BMS", Decimal("5500000.00"), [
                ("Master of Business Administration", "MBA", 4, "POSTGRADUATE"),
            ]),
        ]

        # Faculty 6 to 10 for College 2
        faculty_meta_t2 = [
            ("Rohan", "Bhattacharya", "prof.rohan@horizon.edu", "Professor & HOD", "ITAI"),
            ("Shalini", "Verma", "dr.shalini@horizon.edu", "Associate Professor", "ITAI"),
            ("Amitav", "Roy", "prof.roy@horizon.edu", "Professor & HOD", "DSA"),
            ("Neha", "Agarwal", "dr.neha@horizon.edu", "Assistant Professor", "DSA"),
            ("Deepak", "Saxena", "prof.saxena@horizon.edu", "Professor & HOD", "BMS"),
        ]

        all_departments = {}
        all_programmes = {}
        all_faculty = {tenant1.id: [], tenant2.id: []}

        for tenant, dept_configs, faculty_meta in [
            (tenant1, dept_configs_t1, faculty_meta_t1),
            (tenant2, dept_configs_t2, faculty_meta_t2),
        ]:
            # Create Departments & Programmes
            dept_obj_map = {}
            for dept_name, dept_code, budget, progs in dept_configs:
                dept = Department(
                    tenant_id=tenant.id,
                    name=dept_name,
                    code=dept_code,
                    budget=budget,
                    established_on=date(2015, 6, 1),
                )
                session.add(dept)
                session.flush()
                dept_obj_map[dept_code] = dept
                all_departments[dept.id] = dept

                for prog_name, prog_code, duration, deg_lvl in progs:
                    prog = Programme(
                        tenant_id=tenant.id,
                        department_id=dept.id,
                        name=prog_name,
                        code=prog_code,
                        duration_terms=duration,
                        degree_level=deg_lvl,
                    )
                    session.add(prog)
                    session.flush()
                    all_programmes[prog.id] = prog

            # Create Faculty Members
            emp_counter = 101 if tenant == tenant1 else 201
            for fname, lname, femail, desig, dcode in faculty_meta:
                f_user = User(
                    tenant_id=tenant.id,
                    role="FACULTY",
                    email=femail,
                    first_name=fname,
                    last_name=lname,
                    password_hash=PASSWORD_HASH,
                    status="ACTIVE",
                )
                session.add(f_user)
                session.flush()

                dept = dept_obj_map[dcode]
                fac = Faculty(
                    tenant_id=tenant.id,
                    user_id=f_user.id,
                    department_id=dept.id,
                    employee_no=f"EMP-{emp_counter}",
                    designation=desig,
                )
                session.add(fac)
                session.flush()
                all_faculty[tenant.id].append(fac)
                emp_counter += 1

                # If HOD, assign as department head
                if "HOD" in desig and dept.head_faculty_id is None:
                    dept.head_faculty_id = fac.id

            session.flush()

        # ----------------------------------------------------------------------
        # 7. Courses & Programme-Course Mappings
        # ----------------------------------------------------------------------
        print("[*] Seeding Courses and Programme Curriculum...")
        course_catalog = {
            "CSE": [
                ("CS201", "Data Structures & Algorithms", 4),
                ("CS202", "Database Management Systems", 4),
                ("CS203", "Operating Systems & Concurrency", 4),
                ("CS204", "Computer Networks & Protocols", 3),
            ],
            "ECE": [
                ("EC201", "Digital Signal Processing", 4),
                ("EC202", "VLSI Design & Architecture", 4),
                ("EC203", "Analog & Digital Communication", 4),
            ],
            "MECH": [
                ("ME201", "Thermodynamics & Heat Transfer", 4),
                ("ME202", "Fluid Mechanics & Machinery", 4),
                ("ME203", "Kinematics of Machines", 4),
            ],
            "ITAI": [
                ("AI201", "Machine Learning Foundations", 4),
                ("AI202", "Deep Neural Networks & NLP", 4),
                ("AI203", "Cloud Computing & DevOps", 3),
            ],
            "DSA": [
                ("DS501", "Big Data Analytics & Pipelines", 4),
                ("DS502", "Statistical Inference & Modeling", 4),
                ("DS503", "Data Visualization & BI", 3),
            ],
            "BMS": [
                ("MB501", "Strategic Management & Leadership", 3),
                ("MB502", "Financial Accounting & Valuation", 4),
                ("MB503", "Marketing & Consumer Analytics", 3),
            ],
        }

        all_courses = {}
        for d_id, dept in all_departments.items():
            if dept.code in course_catalog:
                for c_code, c_title, creds in course_catalog[dept.code]:
                    course = Course(
                        tenant_id=dept.tenant_id,
                        department_id=dept.id,
                        course_code=c_code,
                        title=c_title,
                        credits=creds,
                        status="ACTIVE",
                    )
                    session.add(course)
                    session.flush()
                    all_courses[course.id] = course

                    # Link to programmes of this department
                    for p_id, prog in all_programmes.items():
                        if prog.department_id == dept.id:
                            pc = ProgrammeCourse(
                                tenant_id=dept.tenant_id,
                                programme_id=prog.id,
                                course_id=course.id,
                                term_no=2,
                                is_mandatory=True,
                            )
                            session.add(pc)

        session.flush()

        # ----------------------------------------------------------------------
        # 8. Course Offerings & Timetable Slots for Current Term
        # ----------------------------------------------------------------------
        print("[*] Seeding Course Offerings & Timetable Schedule...")
        all_offerings = {tenant1.id: [], tenant2.id: []}
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

        for tenant in [tenant1, tenant2]:
            current_term = terms_map[tenant.id][1]  # Spring 2026 (current)
            fac_list = all_faculty[tenant.id]
            tenant_rooms = rooms_map[tenant.id]

            tenant_courses = [c for c in all_courses.values() if c.tenant_id == tenant.id]
            for idx, crs in enumerate(tenant_courses):
                assigned_fac = fac_list[idx % len(fac_list)]
                offering = CourseOffering(
                    tenant_id=tenant.id,
                    course_id=crs.id,
                    term_id=current_term.id,
                    faculty_id=assigned_fac.id,
                    section="A",
                    capacity=60,
                    status="ACTIVE",
                )
                session.add(offering)
                session.flush()
                all_offerings[tenant.id].append(offering)

                # Timetable slot (e.g. Monday/Wednesday at 09:00 - 10:30)
                room = tenant_rooms[idx % len(tenant_rooms)]
                start_h = 9 + ((idx * 2) % 6)
                slot = TimetableSlot(
                    tenant_id=tenant.id,
                    offering_id=offering.id,
                    room_id=room.id,
                    faculty_id=assigned_fac.id,
                    day_of_week=days[idx % len(days)],
                    start_time=time(start_h, 0),
                    end_time=time(start_h + 1, 30),
                )
                session.add(slot)

                # Create an Assignment & Quiz for this offering
                asg = Assignment(
                    tenant_id=tenant.id,
                    offering_id=offering.id,
                    kind="ASSIGNMENT",
                    title=f"{crs.course_code} - Mid-Term Problem Set",
                    description="Complete all problems and submit the solution PDF.",
                    due_at=datetime.now(timezone.utc) + timedelta(days=14),
                    max_marks=Decimal("100.00"),
                    status="PUBLISHED",
                    created_by=assigned_fac.user_id,
                )
                session.add(asg)
                session.flush()

                quiz = Assignment(
                    tenant_id=tenant.id,
                    offering_id=offering.id,
                    kind="QUIZ",
                    title=f"{crs.course_code} - Concept Evaluation Quiz",
                    description="Multiple choice questions testing core theoretical principles.",
                    due_at=datetime.now(timezone.utc) + timedelta(days=7),
                    max_marks=Decimal("20.00"),
                    status="PUBLISHED",
                    created_by=assigned_fac.user_id,
                )
                session.add(quiz)
                session.flush()

                # Quiz questions
                q1 = QuizQuestion(
                    tenant_id=tenant.id,
                    assignment_id=quiz.id,
                    question_text=f"What is the primary operational objective of {crs.title}?",
                    options={"A": "Performance optimization", "B": "Resource isolation", "C": "Fault tolerance", "D": "All of the above"},
                    correct_answer="D",
                    marks=Decimal("10.00"),
                )
                q2 = QuizQuestion(
                    tenant_id=tenant.id,
                    assignment_id=quiz.id,
                    question_text=f"Which algorithm/technique is standard in {crs.title}?",
                    options={"A": "Dynamic Programming", "B": "Gradient Descent", "C": "Round Robin", "D": "Domain Specific"},
                    correct_answer="A",
                    marks=Decimal("10.00"),
                )
                session.add_all([q1, q2])

                # Exam for this offering
                exam = Exam(
                    tenant_id=tenant.id,
                    term_id=current_term.id,
                    offering_id=offering.id,
                    exam_type="FINAL",
                    exam_date=date(2026, 5, 15 + (idx % 10)),
                    start_time=time(10, 0),
                    end_time=time(13, 0),
                    room_id=room.id,
                    max_marks=Decimal("100.00"),
                )
                session.add(exam)

        session.flush()

        # ----------------------------------------------------------------------
        # 9. Fee Structures & Scholarships
        # ----------------------------------------------------------------------
        print("[*] Seeding Fee Structures and Scholarships...")
        fee_struct_map = {}
        for p_id, prog in all_programmes.items():
            current_term = terms_map[prog.tenant_id][1]
            amount = Decimal("65000.00") if "B.Tech" in prog.name else Decimal("85000.00")
            fs = FeeStructure(
                tenant_id=prog.tenant_id,
                programme_id=prog.id,
                term_id=current_term.id,
                name=f"{prog.code} Tuition & Laboratory Fee - Term {current_term.term_no}",
                amount=amount,
                due_date=date(2026, 2, 15),
            )
            session.add(fs)
            session.flush()
            fee_struct_map[prog.id] = fs

        # Merit Scholarships
        scholarship_map = {}
        for tenant in [tenant1, tenant2]:
            sch = Scholarship(
                tenant_id=tenant.id,
                name="Dean's Academic Excellence Merit Grant",
                kind="PERCENT",
                value=Decimal("25.00"),
                criteria="SGPA >= 8.5 in previous term",
            )
            session.add(sch)
            session.flush()
            scholarship_map[tenant.id] = sch

        # ----------------------------------------------------------------------
        # 10. 50 Students (25 per College) & Full Academics Seeding
        # ----------------------------------------------------------------------
        print("[*] Seeding 50 Students (25 in College 1, 25 in College 2) with full relational data...")

        student_count = 0
        all_seeded_students = []

        for tenant_idx, tenant in enumerate([tenant1, tenant2]):
            t_progs = [p for p in all_programmes.values() if p.tenant_id == tenant.id]
            t_offerings = all_offerings[tenant.id]
            current_term = terms_map[tenant.id][1]
            t_fac = all_faculty[tenant.id]
            t_sch = scholarship_map[tenant.id]

            # 25 students for this college
            for s_idx in range(1, 26):
                student_count += 1
                prog = t_progs[(s_idx - 1) % len(t_progs)]
                fs = fee_struct_map[prog.id]

                # Realistic Indian Names
                first_name = fake.first_name()
                last_name = fake.last_name()
                college_domain = "apex.edu" if tenant == tenant1 else "horizon.edu"
                s_email = f"student{student_count}.{first_name.lower()}@{college_domain}"
                roll_prefix = "APX" if tenant == tenant1 else "HRZ"
                admission_year = random.choice([2023, 2024, 2025])
                roll_no = f"{roll_prefix}-{prog.code}-{admission_year % 100}-{s_idx:03d}"

                s_user = User(
                    tenant_id=tenant.id,
                    role="STUDENT",
                    email=s_email,
                    first_name=first_name,
                    last_name=last_name,
                    password_hash=PASSWORD_HASH,
                    status="ACTIVE",
                    last_login_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)),
                )
                session.add(s_user)
                session.flush()

                student = Student(
                    tenant_id=tenant.id,
                    user_id=s_user.id,
                    programme_id=prog.id,
                    roll_no=roll_no,
                    admission_year=admission_year,
                    current_term_no=2,
                    status="ACTIVE",
                )
                session.add(student)
                session.flush()
                all_seeded_students.append(student)

                # Enroll in matching department course offerings
                dept_offerings = [
                    o for o in t_offerings
                    if all_courses[o.course_id].department_id == prog.department_id
                ]
                enrolled_for_student = dept_offerings if dept_offerings else t_offerings[:2]

                for off in enrolled_for_student:
                    enr = Enrollment(
                        tenant_id=tenant.id,
                        offering_id=off.id,
                        student_id=student.id,
                        status="ENROLLED",
                        enrolled_at=datetime.now(timezone.utc) - timedelta(days=45),
                    )
                    session.add(enr)
                    session.flush()

                    # Attendance records (Past 10 class dates)
                    today = date.today()
                    for d_offset in range(1, 11):
                        att_date = today - timedelta(days=d_offset * 2)
                        att_status = "PRESENT" if random.random() < 0.90 else random.choice(["ABSENT", "LATE"])
                        att = Attendance(
                            tenant_id=tenant.id,
                            offering_id=off.id,
                            student_id=student.id,
                            att_date=att_date,
                            status=att_status,
                            marked_by=off.faculty_id,
                        )
                        session.add(att)

                    # Grade Record for this course offering
                    internal = Decimal(str(round(random.uniform(22.0, 30.0), 2)))
                    final_m = Decimal(str(round(random.uniform(50.0, 70.0), 2)))
                    total_marks = internal + final_m
                    if total_marks >= 90:
                        grd, gp = "A+", Decimal("10.0")
                    elif total_marks >= 80:
                        grd, gp = "A", Decimal("9.0")
                    elif total_marks >= 70:
                        grd, gp = "B+", Decimal("8.0")
                    elif total_marks >= 60:
                        grd, gp = "B", Decimal("7.0")
                    else:
                        grd, gp = "C", Decimal("6.0")

                    gr = GradeRecord(
                        tenant_id=tenant.id,
                        student_id=student.id,
                        offering_id=off.id,
                        internal_marks=internal,
                        final_marks=final_m,
                        grade=grd,
                        grade_points=gp,
                        status="COMPLETED",
                        submitted_by=off.faculty_id,
                        approved_by=admin1_user.id if tenant == tenant1 else admin2_user.id,
                        published_at=datetime.now(timezone.utc) - timedelta(days=5),
                    )
                    session.add(gr)

                # Term Result Summary
                sgpa = Decimal(str(round(random.uniform(7.2, 9.8), 2)))
                cgpa = Decimal(str(round(random.uniform(7.0, 9.7), 2)))
                term_res = StudentTermResult(
                    tenant_id=tenant.id,
                    student_id=student.id,
                    term_id=current_term.id,
                    sgpa=sgpa,
                    cgpa=cgpa,
                    credits_earned=20,
                    published_at=datetime.now(timezone.utc) - timedelta(days=5),
                )
                session.add(term_res)

                # Fee Record & Payment
                discount = Decimal("16250.00") if (s_idx % 5 == 0) else Decimal("0.00")
                amount_due = fs.amount - discount
                is_paid = (s_idx % 4 != 0)  # 75% have completed payment

                fee_rec = FeeRecord(
                    tenant_id=tenant.id,
                    student_id=student.id,
                    fee_structure_id=fs.id,
                    amount_due=amount_due,
                    discount=discount,
                    due_date=fs.due_date,
                    paid_date=date(2026, 2, 10) if is_paid else None,
                    status="PAID" if is_paid else "PENDING",
                )
                session.add(fee_rec)
                session.flush()

                if is_paid:
                    pmt = Payment(
                        tenant_id=tenant.id,
                        fee_record_id=fee_rec.id,
                        amount=amount_due,
                        method=random.choice(["UPI", "CARD", "NET_BANKING"]),
                        gateway_ref=f"PAY-TXN-{tenant.slug.upper()}-{uuid.uuid4().hex[:10].upper()}",
                        status="VERIFIED",
                        verified_at=datetime(2026, 2, 10, 14, 30, tzinfo=timezone.utc),
                    )
                    session.add(pmt)

                # Award Scholarship if top performer
                if discount > 0:
                    st_sch = StudentScholarship(
                        tenant_id=tenant.id,
                        student_id=student.id,
                        scholarship_id=t_sch.id,
                        term_id=current_term.id,
                        awarded_at=datetime.now(timezone.utc) - timedelta(days=30),
                    )
                    session.add(st_sch)

                # Academic Flag or Grievance for occasional students
                if s_idx == 3:
                    flag = AcademicFlag(
                        tenant_id=tenant.id,
                        student_id=student.id,
                        offering_id=enrolled_for_student[0].id,
                        flag_type="ATTENDANCE",
                        raised_by=t_fac[0].id,
                        description="Shortage of attendance (< 75%) flagged for counselor review.",
                        status="RESOLVED",
                        assigned_to=t_fac[0].user_id,
                        resolved_at=datetime.now(timezone.utc) - timedelta(days=2),
                    )
                    session.add(flag)

                if s_idx == 7:
                    ticket = GrievanceTicket(
                        tenant_id=tenant.id,
                        student_id=student.id,
                        category="FACILITY",
                        title="GPU Access Request for CV Lab",
                        priority="MEDIUM",
                        description="Request for additional GPU access in Computer Vision Lab 202.",
                        status="RESOLVED",
                        assigned_to=admin1_user.id if tenant == tenant1 else admin2_user.id,
                        resolved_at=datetime.now(timezone.utc) - timedelta(days=1),
                        resolution_notes="Granted supplementary compute quota on Lab Server 2.",
                    )
                    session.add(ticket)

        session.flush()

        # ----------------------------------------------------------------------
        # 11. Notifications & Faculty Leave Requests
        # ----------------------------------------------------------------------
        print("[*] Seeding System Notifications & Faculty Requests...")
        for tenant, admin_user in [(tenant1, admin1_user), (tenant2, admin2_user)]:
            notif = Notification(
                tenant_id=tenant.id,
                sent_by=admin_user.id,
                event_type="CIRCULAR",
                target_role="ALL",
                title="Spring 2026 Mid-Term Schedule Published",
                message="The mid-term examination timetable and hall ticket guidelines are now accessible on your portal dashboard.",
            )
            session.add(notif)
            session.flush()

            # Deliver to admin + first 5 faculty + first 10 students
            target_users = [admin_user] + [
                session.get(User, f.user_id) for f in all_faculty[tenant.id][:3]
            ]
            for u in target_users:
                if u:
                    nd = NotificationDelivery(
                        tenant_id=tenant.id,
                        notification_id=notif.id,
                        user_id=u.id,
                        channel="IN_APP",
                        status="DELIVERED",
                        read_at=datetime.now(timezone.utc) - timedelta(hours=1),
                    )
                    session.add(nd)

            # Sample Faculty Leave Request
            fac = all_faculty[tenant.id][0]
            leave = LeaveRequest(
                tenant_id=tenant.id,
                faculty_id=fac.id,
                leave_type="DUTY",
                start_date=date(2026, 4, 10),
                end_date=date(2026, 4, 12),
                reason="Attending IEEE International Conference on AI in Higher Education as Keynote Speaker.",
                status="APPROVED",
                approved_by=admin_user.id,
                approved_at=datetime.now(timezone.utc) - timedelta(days=3),
                remarks="Approved with duty leave concession.",
            )
            session.add(leave)

        # Commit all transactions
        session.commit()
        print("\n" + "=" * 80)
        print("  SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Print Detailed Summary
        t_count = session.query(Tenant).count()
        u_count = session.query(User).count()
        adm_count = session.query(User).filter(User.role == "ADMIN").count()
        fac_count = session.query(Faculty).count()
        stu_count = session.query(Student).count()
        dept_count = session.query(Department).count()
        prog_count = session.query(Programme).count()
        crs_count = session.query(Course).count()
        off_count = session.query(CourseOffering).count()
        enr_count = session.query(Enrollment).count()
        att_count = session.query(Attendance).count()
        gr_count = session.query(GradeRecord).count()
        fee_count = session.query(FeeRecord).count()
        pmt_count = session.query(Payment).count()

        print(f"\nEntity Counts in Database:")
        print(f"  Colleges (Tenants)  : {t_count}")
        print(f"  Total Users         : {u_count} (Admins: {adm_count}, Faculty: {fac_count}, Students: {stu_count})")
        print(f"  Departments         : {dept_count}")
        print(f"  Programmes          : {prog_count}")
        print(f"  Courses             : {crs_count}")
        print(f"  Course Offerings    : {off_count}")
        print(f"  Enrollments         : {enr_count}")
        print(f"  Attendance Records  : {att_count}")
        print(f"  Grade Records       : {gr_count}")
        print(f"  Fee Records         : {fee_count} (Payments: {pmt_count})")

        print("\n" + "-" * 80)
        print("DEMO CREDENTIALS (All passwords: Password123!)")
        print("-" * 80)
        print(f"  Platform Operator: root@nexora.io")
        print(f"  College 1 Admin  : admin.apex@nexora.edu (Apex Institute of Technology)")
        print(f"  College 2 Admin  : admin.horizon@nexora.edu (Horizon University)")
        print(f"  Faculty 1 (HOD)  : prof.menon@apex.edu (Apex - CSE HOD)")
        print(f"  Faculty 2 (HOD)  : prof.rohan@horizon.edu (Horizon - ITAI HOD)")
        s1_user = session.get(User, all_seeded_students[0].user_id)
        s2_user = session.get(User, all_seeded_students[25].user_id)
        print(f"  Student Sample 1 : {s1_user.email} (Roll: {all_seeded_students[0].roll_no})")
        print(f"  Student Sample 2 : {s2_user.email} (Roll: {all_seeded_students[25].roll_no})")
        print("-" * 80 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n[!] ERROR during database seeding: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise e
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed NEXORA PostgreSQL Database with realistic multi-tenant data.")
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help=f"PostgreSQL database URL (default: {DEFAULT_DATABASE_URL})",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Wipe and reseed all tables from scratch (default: True)",
    )
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Do not wipe existing data before seeding",
    )
    args = parser.parse_args()

    seed_database(db_url=args.database_url, clean=args.clean)


if __name__ == "__main__":
    main()
