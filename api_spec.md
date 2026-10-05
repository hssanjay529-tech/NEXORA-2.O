# NEXORA — Complete API Specification (`api_spec.md`)

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Protocol:** RESTful HTTPS + WebSockets (RFC 6455)  
**Database:** PostgreSQL 16 (Multi-Tenant Row-Level Security via `tenant_id`)  
**Specification Standard:** Strict feature-to-database CRUD mapping grouped by portal.

---

## 1. Global Conventions & Architecture Standards

1. **Multi-Tenancy & Isolation:** Every query strictly enforces `tenant_id = current_setting('app.tenant_id')::uuid` via Row-Level Security (RLS) on all 55 tenant-scoped tables.
2. **Key Formats:** Primary Keys (`id`) are UUIDv7. Foreign Keys utilize composite constraints `(tenant_id, parent_id)`.
3. **Files & Documents:** No raw file binary or public URLs in data tables; all uploads point to the `files` table (`file_id`).
4. **Auditability:** All state transitions and sensitive mutations write immutable logs into `workflow_transitions` and `audit_logs`.

---

# 2. Admin Portal API Endpoints

The Admin Portal covers institutional setup, user lifecycle, academic structure, room allocations, fee management, curriculum governance, compliance, approvals, and system-wide analytics.

| Route | Feature & PRD Ref | Database Table(s) | How it Interacts (SQL & Logic) |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/admin/users` | **ADM-01** User Account Provisioning | `users`, `students`, `faculty`, `audit_logs` | **INSERT** into `users` (with hashed password, role, email); conditionally **INSERT** profile record into `students` or `faculty`; **INSERT** entry into `audit_logs` recording admin action. |
| `GET /api/v1/admin/users` | **ADM-01** User Directory & Search | `users`, `students`, `faculty`, `departments` | **SELECT** from `users` with LEFT JOIN on `students`, `faculty`, and `departments` filtering by role, department, active status, and search query. |
| `GET /api/v1/admin/users/{id}` | **ADM-01** User Profile Retrieval | `users`, `students`, `faculty`, `departments` | **SELECT** user metadata, profile attributes, contact info, and role scopes for specified `user_id`. |
| `PATCH /api/v1/admin/users/{id}` | **ADM-01** Update User Details & Status | `users`, `students`, `faculty`, `audit_logs` | **UPDATE** `users` (email, status `ACTIVE`/`SUSPENDED`, role); **UPDATE** associated `students` or `faculty` fields; **INSERT** record into `audit_logs`. |
| `DELETE /api/v1/admin/users/{id}` | **ADM-01** Soft-Delete / Deactivate User | `users`, `user_tokens`, `audit_logs` | **UPDATE** `users SET deleted_at = NOW(), status = 'INACTIVE'`; **DELETE** or revoke all active sessions in `user_tokens`; **INSERT** into `audit_logs`. |
| `POST /api/v1/admin/users/bulk-import` | **ADM-01** Bulk Roster Ingestion | `background_jobs`, `files`, `users`, `students`, `faculty` | **INSERT** uploaded CSV into `files`; **INSERT** entry into `background_jobs` (`status = 'PENDING'`); worker parses CSV and executes batch **INSERT** into `users`, `students`, and `faculty`. |
| `POST /api/v1/admin/academic-years` | **ADM-02** Define Academic Year | `academic_years`, `audit_logs` | **INSERT** into `academic_years` (`code`, `name`, `start_date`, `end_date`, `is_current`); **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/academic-years` | **ADM-02** List Academic Years | `academic_years`, `terms` | **SELECT** all academic years with nested count of `terms` ordered by `start_date DESC`. |
| `POST /api/v1/admin/terms` | **ADM-02** Semester / Term Lifecycle | `terms`, `academic_years`, `audit_logs` | **INSERT** into `terms` with term dates, enrolment window (`enrolment_start`, `enrolment_end`), and examination window; **INSERT** into `audit_logs`. |
| `PATCH /api/v1/admin/terms/{id}` | **ADM-02** Term Window Modifications | `terms`, `audit_logs` | **UPDATE** `terms` (dates, `is_current` active flag); **INSERT** record into `audit_logs`. |
| `POST /api/v1/admin/calendar/events` | **ADM-02** Publish Calendar Events & Holidays | `calendar_events`, `notifications` | **INSERT** into `calendar_events` (`event_type`, `title`, `start_date`, `end_date`, `is_holiday`); **INSERT** broadcast notification triggers into `notifications`. |
| `GET /api/v1/admin/calendar/events` | **ADM-02** List Calendar Schedule | `calendar_events` | **SELECT** from `calendar_events` filtered by `term_id`, `date_range`, or `event_type`. |
| `POST /api/v1/admin/departments` | **ADM-03** Create Department & Budget | `departments`, `faculty`, `audit_logs` | **INSERT** into `departments` (`code`, `name`, `head_faculty_id`, `budget_allocated`); **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/departments` | **ADM-03** List Departments | `departments`, `faculty`, `programmes` | **SELECT** from `departments` with JOIN on `faculty` (HOD details) and aggregate count of active `programmes` and students. |
| `PATCH /api/v1/admin/departments/{id}` | **ADM-03** Update Department & HOD | `departments`, `audit_logs` | **UPDATE** `departments` (`head_faculty_id`, `budget_allocated`, `name`); **INSERT** record into `audit_logs`. |
| `POST /api/v1/admin/programmes` | **ADM-03** Academic Degree Program Config | `programmes`, `departments`, `audit_logs` | **INSERT** into `programmes` (`department_id`, `code`, `name`, `degree_level`, `total_semesters`, `required_credits`); **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/programmes` | **ADM-03** List Degree Programmes | `programmes`, `departments` | **SELECT** from `programmes` with JOIN on `departments`. |
| `GET /api/v1/admin/analytics/dashboard` | **ADM-04** Institution KPI Dashboard | `students`, `faculty`, `enrollments`, `payments`, `attendance` | **SELECT** aggregated metrics: count of active students/faculty, average attendance rate across terms, total revenue collected vs pending. |
| `GET /api/v1/admin/analytics/enrolments` | **ADM-04** Enrolment Trend Reports | `enrollments`, `programmes`, `terms` | **SELECT** enrolment volume grouped by `programme_id`, `term_id`, and gender/category demographics. |
| `GET /api/v1/admin/analytics/pass-rates` | **ADM-04** Academic Pass/Fail Analytics | `student_term_results`, `courses`, `terms` | **SELECT** grade distributions, SGPA/CGPA percentiles, and pass percentages grouped by course and department. |
| `POST /api/v1/admin/analytics/reports/generate` | **ADM-04** Export Custom Analytics Report | `analytics_reports`, `files`, `background_jobs` | **INSERT** into `analytics_reports` (`report_type`, `parameters`, `status = 'GENERATING'`); **INSERT** into `background_jobs`; worker generates PDF/XLSX and updates `file_id`. |
| `POST /api/v1/admin/fee-structures` | **ADM-05** Configure Fee Structures | `fee_structures`, `programmes`, `terms`, `audit_logs` | **INSERT** into `fee_structures` (`programme_id`, `term_id`, `components` JSONB, `total_amount`, `due_date`); **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/fee-structures` | **ADM-05** List Fee Structures | `fee_structures`, `programmes`, `terms` | **SELECT** from `fee_structures` JOIN `programmes` and `terms`. |
| `POST /api/v1/admin/fee-records/batch-generate` | **ADM-05** Batch Student Invoicing | `fee_records`, `fee_structures`, `students`, `student_scholarships` | **SELECT** eligible students; compute discounts from `student_scholarships`; batch **INSERT** invoice rows into `fee_records` (`status = 'PENDING'`). |
| `POST /api/v1/admin/scholarships` | **ADM-05** Manage Scholarships | `scholarships`, `audit_logs` | **INSERT** into `scholarships` (`name`, `grant_type`, `percentage`, `amount`, `criteria`); **INSERT** into `audit_logs`. |
| `POST /api/v1/admin/students/{id}/scholarships` | **ADM-05** Award Scholarship to Student | `student_scholarships`, `fee_records`, `audit_logs` | **INSERT** into `student_scholarships`; **UPDATE** corresponding `fee_records` net balance; **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/finance/collection-summary` | **ADM-05** Fee Collection Overview | `fee_records`, `payments`, `students` | **SELECT** sum of total billed, sum of payments received, and list of defaulters/overdue bills. |
| `POST /api/v1/admin/rooms` | **ADM-06** Classrooms & Labs Setup | `rooms`, `audit_logs` | **INSERT** into `rooms` (`building`, `room_number`, `capacity`, `room_type` `'LECTURE_HALL'/'LAB'`, `is_active`); **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/rooms` | **ADM-06** List Facilities & Rooms | `rooms` | **SELECT** all rooms with capacity and equipment flags. |
| `POST /api/v1/admin/timetable/slots` | **ADM-06** Allocate Timetable Slot | `timetable_slots`, `rooms`, `course_offerings`, `faculty` | Check for room/faculty clashes via **SELECT**; if clean, **INSERT** into `timetable_slots` (`course_offering_id`, `faculty_id`, `room_id`, `day_of_week`, `start_time`, `end_time`). |
| `PATCH /api/v1/admin/timetable/slots/{id}` | **ADM-06** Modify Timetable Slot | `timetable_slots`, `audit_logs` | Clash check via **SELECT**; **UPDATE** `timetable_slots` (room, timing, faculty); **INSERT** into `audit_logs`. |
| `DELETE /api/v1/admin/timetable/slots/{id}` | **ADM-06** Remove Timetable Slot | `timetable_slots`, `audit_logs` | **DELETE** from `timetable_slots` where `id = $1`; **INSERT** into `audit_logs`. |
| `POST /api/v1/admin/notifications/broadcast` | **ADM-07** Broadcast Targeted Notification | `notifications`, `notification_deliveries`, `users` | **INSERT** notification header into `notifications`; resolve target users by role/department; batch **INSERT** recipient rows into `notification_deliveries`. |
| `GET /api/v1/admin/course-proposals` | **ADM-08** List Faculty Course Proposals | `course_proposals`, `workflow_instances`, `faculty` | **SELECT** from `course_proposals` JOIN `workflow_instances` where status is `SUBMITTED` or `UNDER_REVIEW`. |
| `POST /api/v1/admin/course-proposals/{id}/review` | **ADM-08** Approve/Reject Course Proposal | `course_proposals`, `courses`, `programme_courses`, `workflow_transitions`, `workflow_instances` | **UPDATE** `workflow_instances` and `course_proposals` status (`APPROVED`/`REJECTED`); if approved, **INSERT** new row into `courses` and `programme_courses`; **INSERT** record into `workflow_transitions`. |
| `POST /api/v1/admin/compliance/records` | **ADM-09** Track Accreditation & Compliance | `compliance_records`, `compliance_versions`, `files`, `audit_logs` | **INSERT** record into `compliance_records` (`agency`, `standard_code`, `due_date`); **INSERT** initial version file into `compliance_versions`; **INSERT** into `audit_logs`. |
| `GET /api/v1/admin/compliance/records` | **ADM-09** List Compliance Audit Records | `compliance_records`, `compliance_versions`, `files` | **SELECT** from `compliance_records` with latest version metadata and expiry dates. |
| `POST /api/v1/admin/grading/approval-batches/{id}/review` | **BR-04** Approve/Reject Final Course Grades | `grade_records`, `student_term_results`, `workflow_instances`, `workflow_transitions` | **UPDATE** `workflow_instances` (`status = 'APPROVED'`); **UPDATE** `grade_records` (`is_final = TRUE`); batch compute and **INSERT** / **UPDATE** rows in `student_term_results`; **INSERT** into `workflow_transitions`. |
| `GET /api/v1/admin/audit-logs` | **BR-09** Institutional Audit Trail | `audit_logs`, `users` | **SELECT** immutable system events with filters on `action`, `user_id`, `entity_type`, and timestamp ranges. |

---

# 3. Faculty Portal API Endpoints

The Faculty Portal empowers teaching staff to upload learning content, record student attendance, publish quizzes and assignments, grade submissions, submit official internal and final grade books, raise academic alerts, and submit operational workflow requests.

| Route | Feature & PRD Ref | Database Table(s) | How it Interacts (SQL & Logic) |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/faculty/course-materials` | **FAC-01** Upload Lecture Notes & Slides | `course_materials`, `course_offerings`, `files` | **INSERT** file row into `files`; **INSERT** entry into `course_materials` (`course_offering_id`, `title`, `unit_number`, `file_id`, `is_published`). |
| `GET /api/v1/faculty/courses/{offering_id}/materials` | **FAC-01** List Uploaded Course Materials | `course_materials`, `files` | **SELECT** all materials for the specified `course_offering_id` JOIN `files` ordered by `unit_number ASC, created_at DESC`. |
| `DELETE /api/v1/faculty/course-materials/{id}` | **FAC-01** Delete Course Material | `course_materials`, `files` | **DELETE** from `course_materials` where `id = $1` and `faculty_id = current_user`; soft-delete file reference. |
| `POST /api/v1/faculty/attendance/sessions` | **FAC-02** Create Attendance Session | `attendance`, `course_offerings`, `timetable_slots` | **INSERT** into `attendance` session metadata (`course_offering_id`, `timetable_slot_id`, `session_date`, `topic_covered`). |
| `POST /api/v1/faculty/attendance/batch-record` | **FAC-02** Bulk Record Class Attendance | `attendance`, `enrollments`, `academic_flags`, `notifications` | Batch **INSERT** / **UPDATE** `attendance` rows (`status = 'PRESENT'/'ABSENT'/'LATE'`); calculate updated attendance %; if `< 75%`, auto **INSERT** alert into `academic_flags` & `notifications`. |
| `GET /api/v1/faculty/courses/{offering_id}/attendance` | **FAC-02** Course Attendance Register | `attendance`, `enrollments`, `students`, `users` | **SELECT** matrix of student attendance records per session date for a course offering with calculated totals. |
| `POST /api/v1/faculty/assignments` | **FAC-03** Create Assignment / Homework | `assignments`, `course_offerings`, `files`, `notifications` | **INSERT** into `assignments` (`course_offering_id`, `title`, `due_date`, `max_marks`, `rubric` JSONB, `file_id`); trigger class broadcast **INSERT** into `notifications`. |
| `GET /api/v1/faculty/courses/{offering_id}/assignments` | **FAC-03** List Course Assignments | `assignments`, `assignment_submissions` | **SELECT** from `assignments` with aggregate counts of total submissions, graded count, and pending count. |
| `GET /api/v1/faculty/assignments/{id}/submissions` | **FAC-03** List Student Submissions | `assignment_submissions`, `students`, `users`, `files` | **SELECT** from `assignment_submissions` JOIN `students` and `files` for the target assignment. |
| `POST /api/v1/faculty/submissions/{id}/grade` | **FAC-03** Grade Submission & Rubric Feedback | `assignment_submissions`, `notifications` | **UPDATE** `assignment_submissions` (`marks_obtained`, `feedback`, `graded_at`, `graded_by`); **INSERT** grade alert into `notifications` for student. |
| `POST /api/v1/faculty/quizzes` | **FAC-03** Create Online Timed Quiz | `assignments`, `quiz_questions` | **INSERT** into `assignments` (`is_quiz = TRUE`, `duration_minutes`); batch **INSERT** question items into `quiz_questions` (`question_text`, `options` JSONB, `correct_answer`, `marks`). |
| `POST /api/v1/faculty/grades/batch-entry` | **FAC-04** Enter Internal / Exam Marks | `grade_records`, `grading_scales`, `course_offerings` | Validate scale in `grading_scales`; batch **INSERT** / **UPDATE** rows in `grade_records` (`course_offering_id`, `student_id`, `component`, `marks_obtained`, `grade_point`). |
| `POST /api/v1/faculty/grades/submit-approval` | **FAC-04** Submit Grade Book for Admin Approval | `workflow_instances`, `workflow_transitions`, `grade_records` | **INSERT** into `workflow_instances` (`entity_type = 'GRADE_BATCH'`, `status = 'SUBMITTED'`); **INSERT** initial transition row into `workflow_transitions`; lock `grade_records` from further edits. |
| `POST /api/v1/faculty/academic-flags` | **FAC-05** Raise Student Concern Flag | `academic_flags`, `students`, `notifications` | **INSERT** into `academic_flags` (`student_id`, `course_offering_id`, `flag_type` `'ATTENDANCE'/'ACADEMIC'/'BEHAVIORAL'`, `severity`, `description`); **INSERT** alert into `notifications`. |
| `GET /api/v1/faculty/academic-flags` | **FAC-05** List Raised Concern Flags | `academic_flags`, `students`, `users` | **SELECT** from `academic_flags` JOIN `students` where `faculty_id = current_user` or assigned department. |
| `POST /api/v1/faculty/discussions/threads` | **FAC-06** Start Course Discussion Thread | `discussion_threads`, `course_offerings` | **INSERT** into `discussion_threads` (`course_offering_id`, `author_user_id`, `title`, `is_pinned`, `is_locked`). |
| `POST /api/v1/faculty/discussions/posts` | **FAC-06** Post Reply in Course Forum | `discussion_posts`, `discussion_threads` | **INSERT** into `discussion_posts` (`thread_id`, `author_user_id`, `content`, `parent_post_id`). |
| `GET /api/v1/faculty/timetable/my-schedule` | **FAC-07** View Personal Teaching Timetable | `timetable_slots`, `rooms`, `course_offerings`, `courses` | **SELECT** weekly schedule from `timetable_slots` JOIN `rooms` and `courses` where `faculty_id = current_user`. |
| `POST /api/v1/faculty/timetable/change-requests` | **FAC-07** Request Timetable Reschedule / Swap | `schedule_change_requests`, `workflow_instances`, `workflow_transitions` | **INSERT** into `schedule_change_requests` (`slot_id`, `target_room_id`, `target_day`, `target_time`, `reason`); **INSERT** into `workflow_instances` (`status = 'SUBMITTED'`). |
| `POST /api/v1/faculty/leave/applications` | **FAC-08** Submit Leave Application | `leave_requests`, `workflow_instances`, `workflow_transitions` | **INSERT** into `leave_requests` (`faculty_id`, `leave_type`, `start_date`, `end_date`, `reason`, `substitute_faculty_id`); **INSERT** into `workflow_instances`. |
| `GET /api/v1/faculty/leave/applications` | **FAC-08** Track My Leave Requests | `leave_requests`, `workflow_instances`, `workflow_transitions` | **SELECT** from `leave_requests` JOIN `workflow_instances` where `faculty_id = current_user`. |
| `POST /api/v1/faculty/course-proposals` | **FAC-09** Propose New Course / Syllabus Update | `course_proposals`, `workflow_instances`, `files` | **INSERT** proposal metadata into `course_proposals` (`title`, `department_id`, `credits`, `syllabus_summary`, `file_id`); **INSERT** into `workflow_instances`. |
| `GET /api/v1/faculty/course-proposals` | **FAC-09** Track My Course Proposals | `course_proposals`, `workflow_instances` | **SELECT** proposals submitted by current faculty user. |

---

# 4. Student Portal API Endpoints

The Student Portal provides self-service features for degree progression, course registration, personal schedules, assignment submissions, fee clearing, exam ticketing, performance analytics, support grievances, and document requests.

| Route | Feature & PRD Ref | Database Table(s) | How it Interacts (SQL & Logic) |
| :--- | :--- | :--- | :--- |
| `GET /api/v1/student/courses/available` | **STU-01** Browse Enrolment Course Catalog | `course_offerings`, `courses`, `faculty`, `terms` | **SELECT** open offerings from `course_offerings` JOIN `courses` where `term.enrolment_window` is active; verify prerequisites against completed courses. |
| `POST /api/v1/student/enrolments/register` | **STU-01** Enrol into Selected Courses | `enrollments`, `course_offerings`, `students` | Verify seat capacity and prerequisite clearance; execute batch **INSERT** into `enrollments` (`student_id`, `course_offering_id`, `status = 'ENROLLED'`); **UPDATE** enrolled count. |
| `DELETE /api/v1/student/enrolments/{id}/drop` | **STU-01** Drop Enrolled Course | `enrollments`, `terms`, `audit_logs` | Verify drop deadline in `terms`; **UPDATE** `enrollments SET status = 'DROPPED', dropped_at = NOW()`; **INSERT** into `audit_logs`. |
| `GET /api/v1/student/timetable` | **STU-02** View Personalized Class Timetable | `enrollments`, `timetable_slots`, `rooms`, `courses`, `faculty` | **SELECT** timetable entries from `timetable_slots` for all `course_offerings` where student has an active `enrollments` record. |
| `GET /api/v1/student/attendance/summary` | **STU-02** Track Attendance Breakdown & Eligibility | `attendance`, `enrollments`, `course_offerings`, `courses` | **SELECT** total sessions held vs present count per enrolled course; calculate real-time percentage and exam eligibility flag (`>= 75%`). |
| `GET /api/v1/student/calendar` | **STU-02** View Academic Calendar & Holidays | `calendar_events`, `terms` | **SELECT** from `calendar_events` for current active term and holidays. |
| `GET /api/v1/student/assignments` | **STU-03** View Upcoming & Past Assignments | `assignments`, `assignment_submissions`, `enrollments`, `courses` | **SELECT** assignments for all enrolled courses LEFT JOIN `assignment_submissions` to show pending, submitted, and graded statuses. |
| `POST /api/v1/student/assignments/{id}/submit` | **STU-03** Submit Assignment Work | `assignment_submissions`, `assignments`, `files`, `audit_logs` | Verify deadline; **INSERT** file into `files`; **INSERT** or **UPDATE** `assignment_submissions` (`assignment_id`, `student_id`, `file_id`, `submitted_at = NOW()`). |
| `GET /api/v1/student/grades/term-results` | **STU-04** View Term Results & Grade Cards | `student_term_results`, `grade_records`, `terms`, `courses` | **SELECT** approved published results from `student_term_results` JOIN `grade_records` for the authenticated student. |
| `GET /api/v1/student/fees/bills` | **STU-05** View Fee Dues & Ledger | `fee_records`, `fee_structures`, `payments` | **SELECT** all issued fee bills from `fee_records` showing original amount, scholarship waiver deductions, payments credited, and remaining balance. |
| `POST /api/v1/student/fees/pay` | **STU-05** Initiate Online Fee Settlement | `payments`, `fee_records` | **INSERT** initiated payment order into `payments` (`fee_record_id`, `amount`, `payment_gateway_ref`, `status = 'INITIATED'`). |
| `GET /api/v1/student/fees/receipts/{payment_id}` | **STU-05** Download Official Fee Receipt | `payments`, `fee_records`, `files` | **SELECT** verified payment transaction; generate digitally signed PDF receipt via `files` record. |
| `GET /api/v1/student/exams/available` | **STU-06** List Eligible Examinations | `exams`, `exam_eligibility_rules`, `attendance`, `fee_records` | **SELECT** exams where student satisfies attendance minimums and fee clearance rules. |
| `POST /api/v1/student/exams/register` | **STU-06** Register for Exam Schedule | `exam_registrations`, `exams`, `audit_logs` | Verify eligibility rules; **INSERT** into `exam_registrations` (`exam_id`, `student_id`, `registered_at`). |
| `GET /api/v1/student/exams/hall-tickets/{exam_id}` | **STU-06** Download Exam Hall Ticket | `hall_tickets`, `exam_registrations`, `exams`, `rooms`, `files` | Verify approved registration; **SELECT** allocated seat/room; return generated hall ticket PDF from `files`. |
| `GET /api/v1/student/analytics/performance` | **STU-07** Performance & CGPA Trend Dashboard | `student_term_results`, `students`, `grade_records` | **SELECT** historical SGPA/CGPA progression series, credit completion tally, and class rank percentiles. |
| `POST /api/v1/student/grievances` | **STU-08** File Grievance / Support Ticket | `grievance_tickets`, `files` | **INSERT** into `grievance_tickets` (`student_id`, `category`, `subject`, `description`, `is_anonymous`, `file_id`, `status = 'OPEN'`). |
| `GET /api/v1/student/grievances` | **STU-08** Track Grievance Status & Replies | `grievance_tickets` | **SELECT** grievances filed by current student with administrative replies and resolution state. |
| `POST /api/v1/student/documents/requests` | **STU-09** Request Official Certificates / Transcripts | `document_requests`, `workflow_instances`, `workflow_transitions` | **INSERT** into `document_requests` (`student_id`, `document_type` `'BONAFIDE'/'TRANSCRIPT'/'NOC'`, `purpose`); **INSERT** into `workflow_instances`. |
| `GET /api/v1/student/documents/requests` | **STU-09** Track Document Issuance Status | `document_requests`, `workflow_instances`, `files` | **SELECT** from `document_requests` with download link from `files` once status is `COMPLETED`. |
| `GET /api/v1/student/discussions/threads` | **STU-10** View Course Discussions | `discussion_threads`, `discussion_posts`, `enrollments` | **SELECT** discussion threads and reply count for enrolled courses. |
| `POST /api/v1/student/discussions/posts` | **STU-10** Post Question / Peer Reply | `discussion_posts`, `discussion_threads` | **INSERT** into `discussion_posts` (`thread_id`, `author_user_id`, `content`, `parent_post_id`). |
| `POST /api/v1/student/messages/send` | **STU-10** In-Portal Direct Message to Faculty | `conversations`, `conversation_participants`, `messages`, `message_attachments` | Find or **INSERT** into `conversations`; ensure participant rows in `conversation_participants`; **INSERT** message into `messages`. |

---

# 5. Shared & Cross-Cutting Platform Endpoints

| Route | Feature & Description | Database Table(s) | How it Interacts (SQL & Logic) |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/auth/login` | User Authentication & JWT Issuance | `users`, `user_tokens`, `login_attempts`, `tenants` | **SELECT** user by email and tenant; verify password hash via pgcrypto; **INSERT** record into `login_attempts`; issue JWT and **INSERT** refresh token into `user_tokens`. |
| `POST /api/v1/auth/refresh` | Token Rotation | `user_tokens`, `users` | **SELECT** valid refresh token; **UPDATE** / rotate token in `user_tokens`; return new short-lived access JWT. |
| `POST /api/v1/auth/logout` | Session Invalidation | `user_tokens` | **DELETE** or revoke refresh token row in `user_tokens` where `id = $1`. |
| `GET /api/v1/auth/me` | Current Session & Permissions | `users`, `students`, `faculty`, `tenants` | **SELECT** user profile, active tenant settings, and RBAC permission scopes. |
| `POST /api/v1/files/upload` | Secure Direct Cloud Upload Descriptor | `files` | **INSERT** record into `files` (`storage_key`, `file_name`, `mime_type`, `file_size_bytes`, `uploaded_by`); return presigned S3/GCS upload URL. |
| `GET /api/v1/notifications` | User In-App Notification Feed | `notifications`, `notification_deliveries` | **SELECT** notifications from `notifications` JOIN `notification_deliveries` where `user_id = current_user` and `is_read = FALSE`. |
| `PATCH /api/v1/notifications/{id}/read` | Mark Notification as Read | `notification_deliveries` | **UPDATE** `notification_deliveries SET is_read = TRUE, read_at = NOW() WHERE id = $1`. |
| `GET /api/v1/background-jobs/{id}` | Poll Async Background Job Status | `background_jobs` | **SELECT** `status`, `progress_percentage`, `result_summary`, and `error_log` from `background_jobs`. |

---

*Verified and mapped against `project_requirements.md` (28 Functional Requirements) and `database_architecture.md` (57 Multi-Tenant Relational Tables).*
