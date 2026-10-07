from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class FlagType(str, Enum):
    ATTENDANCE = "ATTENDANCE"
    ACADEMIC = "ACADEMIC"
    PLAGIARISM = "PLAGIARISM"
    MISCONDUCT = "MISCONDUCT"
    WELFARE = "WELFARE"
    PERFORMANCE = "PERFORMANCE"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class DocumentType(str, Enum):
    BONAFIDE = "BONAFIDE"
    TRANSCRIPT = "TRANSCRIPT"
    GRADE_CARD = "GRADE_CARD"
    TRANSFER_CERTIFICATE = "TRANSFER_CERTIFICATE"
    COURSE_COMPLETION = "COURSE_COMPLETION"
    OTHER = "OTHER"
