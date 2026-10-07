import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, Date, Time,
    DateTime, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    __tablename__ = 'departments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    head_faculty_id = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='SET NULL'))
    budget = Column(Numeric(12, 2), default=0.00)
    established_on = Column(Date)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    faculty_members = relationship("Faculty", back_populates="department", foreign_keys="Faculty.department_id")
    programmes = relationship("Programme", back_populates="department")
    courses = relationship("Course", back_populates="department")


class Faculty(Base):
    __tablename__ = 'faculty'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False)
    employee_no = Column(Text, nullable=False)
    designation = Column(Text, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty_members", foreign_keys=[department_id])


class Programme(Base):
    __tablename__ = 'programmes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    duration_terms = Column(Integer, default=8, nullable=False)
    degree_level = Column(Text, nullable=False)  # UNDERGRADUATE, POSTGRADUATE, DIPLOMA, DOCTORAL
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    department = relationship("Department", back_populates="programmes")
    students = relationship("Student", back_populates="programme")


class Student(Base):
    __tablename__ = 'students'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    programme_id = Column(UUID(as_uuid=True), ForeignKey('programmes.id', ondelete='RESTRICT'), nullable=False)
    roll_no = Column(Text, nullable=False)
    admission_year = Column(Integer, nullable=False)
    current_term_no = Column(Integer, default=1, nullable=False)
    status = Column(Text, default='ACTIVE', nullable=False)  # ACTIVE, SUSPENDED, ALUMNI, DROPPED
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="student_profile")
    programme = relationship("Programme", back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student")


class AcademicYear(Base):
    __tablename__ = 'academic_years'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    label = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Text, default='DRAFT', nullable=False)  # DRAFT, PUBLISHED, ARCHIVED
    published_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    terms = relationship("Term", back_populates="academic_year", cascade="all, delete-orphan")


class Term(Base):
    __tablename__ = 'terms'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False)
    name = Column(Text, nullable=False)
    term_no = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    enrolment_opens_at = Column(DateTime(timezone=True))
    enrolment_closes_at = Column(DateTime(timezone=True))
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    academic_year = relationship("AcademicYear", back_populates="terms")


class CalendarEvent(Base):
    __tablename__ = 'calendar_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'))
    event_type = Column(Text, nullable=False)  # HOLIDAY, EXAM_WINDOW, EVENT, ACADEMIC_DEADLINE
    title = Column(Text, nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Course(Base):
    __tablename__ = 'courses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False)
    course_code = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    credits = Column(Integer, default=3, nullable=False)
    syllabus_file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='SET NULL'))
    status = Column(Text, default='ACTIVE', nullable=False)  # ACTIVE, INACTIVE, ARCHIVED
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    department = relationship("Department", back_populates="courses")
    offerings = relationship("CourseOffering", back_populates="course")


class ProgrammeCourse(Base):
    __tablename__ = 'programme_courses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    programme_id = Column(UUID(as_uuid=True), ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    term_no = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class CourseOffering(Base):
    __tablename__ = 'course_offerings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='RESTRICT'), nullable=False)
    section = Column(Text, default='A', nullable=False)
    capacity = Column(Integer, default=60, nullable=False)
    status = Column(Text, default='ACTIVE', nullable=False)  # ACTIVE, CANCELLED, COMPLETED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    course = relationship("Course", back_populates="offerings")
    faculty = relationship("Faculty")
    enrollments = relationship("Enrollment", back_populates="offering")
    materials = relationship("CourseMaterial", back_populates="offering")


class Enrollment(Base):
    __tablename__ = 'enrollments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    status = Column(Text, default='ENROLLED', nullable=False)  # ENROLLED, DROPPED, COMPLETED
    enrolled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    offering = relationship("CourseOffering", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")


class CourseMaterial(Base):
    __tablename__ = 'course_materials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    offering = relationship("CourseOffering", back_populates="materials")
    file = relationship("File")


class Room(Base):
    __tablename__ = 'rooms'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    code = Column(Text, nullable=False)
    room_type = Column(Text, nullable=False)  # CLASSROOM, LAB, SEMINAR_HALL, AUDITORIUM
    capacity = Column(Integer, default=60, nullable=False)
    building = Column(Text, nullable=False)
    floor = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class TimetableSlot(Base):
    __tablename__ = 'timetable_slots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    offering_id = Column(UUID(as_uuid=True), ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey('rooms.id', ondelete='RESTRICT'), nullable=False)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey('faculty.id', ondelete='RESTRICT'), nullable=False)
    day_of_week = Column(Text, nullable=False)  # MONDAY, TUESDAY...
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    offering = relationship("CourseOffering")
    room = relationship("Room")
    faculty = relationship("Faculty")
