from app.schemas.common import APIResponse, PaginatedResponse, StatusResponse, FileOut, AuditLogOut
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest, UserMeResponse
from app.schemas.admin import (
    UserCreate, UserUpdate, UserOut,
    AcademicYearCreate, AcademicYearOut, TermCreate, TermUpdate, TermOut,
    CalendarEventCreate, CalendarEventOut,
    DepartmentCreate, DepartmentUpdate, DepartmentOut,
    ProgrammeCreate, ProgrammeOut,
    FeeStructureCreate, FeeStructureOut, BatchInvoicingRequest,
    ScholarshipCreate, AwardScholarshipRequest,
    RoomCreate, RoomOut, TimetableSlotCreate, TimetableSlotUpdate, TimetableSlotOut,
    BroadcastNotificationRequest, ProposalReviewRequest,
    ComplianceRecordCreate, GradeBatchReviewRequest, AnalyticsReportGenerateRequest
)
from app.schemas.faculty import (
    CourseMaterialCreate, CourseMaterialOut,
    AttendanceSessionCreate, AttendanceBatchRecordRequest, AttendanceRecordItem,
    AssignmentCreate, QuizCreate, QuizQuestionItem, GradeSubmissionRequest,
    GradeBatchEntryRequest, GradeBatchEntryItem, SubmitGradeApprovalRequest,
    AcademicFlagCreate, DiscussionThreadCreate, DiscussionPostCreate,
    TimetableChangeRequestCreate, LeaveApplicationCreate, FacultyCourseProposalCreate
)
from app.schemas.student import (
    CourseRegisterRequest, AssignmentSubmitRequest,
    FeePaymentRequest, ExamRegisterRequest,
    GrievanceCreate, GrievanceOut,
    DocumentRequestCreate, DocumentRequestOut,
    DirectMessageSendRequest
)
from app.schemas.platform import FileUploadRequest, FileUploadResponse, NotificationDeliveryOut, BackgroundJobOut

__all__ = [
    "APIResponse", "PaginatedResponse", "StatusResponse", "FileOut", "AuditLogOut",
    "LoginRequest", "TokenResponse", "RefreshTokenRequest", "LogoutRequest", "UserMeResponse",
    "UserCreate", "UserUpdate", "UserOut",
    "AcademicYearCreate", "AcademicYearOut", "TermCreate", "TermUpdate", "TermOut",
    "CalendarEventCreate", "CalendarEventOut",
    "DepartmentCreate", "DepartmentUpdate", "DepartmentOut",
    "ProgrammeCreate", "ProgrammeOut",
    "FeeStructureCreate", "FeeStructureOut", "BatchInvoicingRequest",
    "ScholarshipCreate", "AwardScholarshipRequest",
    "RoomCreate", "RoomOut", "TimetableSlotCreate", "TimetableSlotUpdate", "TimetableSlotOut",
    "BroadcastNotificationRequest", "ProposalReviewRequest",
    "ComplianceRecordCreate", "GradeBatchReviewRequest", "AnalyticsReportGenerateRequest",
    "CourseMaterialCreate", "CourseMaterialOut",
    "AttendanceSessionCreate", "AttendanceBatchRecordRequest", "AttendanceRecordItem",
    "AssignmentCreate", "QuizCreate", "QuizQuestionItem", "GradeSubmissionRequest",
    "GradeBatchEntryRequest", "GradeBatchEntryItem", "SubmitGradeApprovalRequest",
    "AcademicFlagCreate", "DiscussionThreadCreate", "DiscussionPostCreate",
    "TimetableChangeRequestCreate", "LeaveApplicationCreate", "FacultyCourseProposalCreate",
    "CourseRegisterRequest", "AssignmentSubmitRequest",
    "FeePaymentRequest", "ExamRegisterRequest",
    "GrievanceCreate", "GrievanceOut",
    "DocumentRequestCreate", "DocumentRequestOut",
    "DirectMessageSendRequest",
    "FileUploadRequest", "FileUploadResponse", "NotificationDeliveryOut", "BackgroundJobOut"
]
