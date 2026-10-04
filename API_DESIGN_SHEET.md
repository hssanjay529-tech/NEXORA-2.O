# NEXORA — Comprehensive API Design Sheet & Specification
**Version:** 2.0.0  
**Status:** Approved & Production-Ready  
**Architecture:** RESTful over HTTPS + WebSockets (RFC 6455)  
**Security Standard:** OAuth2.0 / JWT Bearer, RBAC, Multi-Tenant Row Level Security (RLS)  
**Data Interchange:** JSON (`application/json`) & Multipart Form (`multipart/form-data`)

---

## Table of Contents
1. [Architectural Overview & Global Conventions](#1-architectural-overview--global-conventions)
2. [Security, Authentication & Authorization (RBAC)](#2-security-authentication--authorization-rbac)
3. [Global Envelopes, Headers & Status Codes](#3-global-envelopes-headers--status-codes)
4. [Module 1: Authentication, Tenant & Identity Management](#4-module-1-authentication-tenant--identity-management)
5. [Module 2: User Lifecycle & RBAC Management](#5-module-2-user-lifecycle--rbac-management)
6. [Module 3: Academic Structure & Scheduling](#6-module-3-academic-structure--scheduling)
7. [Module 4: Course Management, Offerings & Enrolment](#7-module-4-course-management-offerings--enrolment)
8. [Module 5: Timetable Engine & Room Allocation](#8-module-5-timetable-engine--room-allocation)
9. [Module 6: Learning Management & Assessments](#9-module-6-learning-management--assessments)
10. [Module 7: Attendance & Academic Monitoring](#10-module-7-attendance--academic-monitoring)
11. [Module 8: Examinations, Grading & Transcripts](#11-module-8-examinations-grading--transcripts)
12. [Module 9: Financial Operations & Fee Management](#12-module-9-financial-operations--fee-management)
13. [Module 10: Unified Workflow & Approval Engine](#13-module-10-unified-workflow--approval-engine)
14. [Module 11: Communication, Announcements & Forums](#14-module-11-communication-announcements--forums)
15. [Module 12: Facilities, Placements, Library & Grievances](#15-module-12-facilities-placements-library--grievances)
16. [Module 13: Analytics, Reporting & Audit System](#16-module-13-analytics-reporting--audit-system)
17. [Module 14: File Management & Background Jobs](#17-module-14-file-management--background-jobs)
18. [Module 15: Real-Time WebSocket API Specification](#18-module-15-real-time-websocket-api-specification)
19. [Error Codes Catalog & Standard Errors](#19-error-codes-catalog--standard-errors)

---

# 1. Architectural Overview & Global Conventions

### 1.1 Base URLs
- **Production API:** `https://api.nexora.edu/v1` (or custom institutional tenant subdomain `https://{tenant_slug}.nexora.edu/api/v1`)
- **WebSocket Gateway:** `wss://api.nexora.edu/ws/v1`
- **Platform Management API (SuperAdmin/Operator):** `https://api.nexora.edu/platform/v1`

### 1.2 Multi-Tenancy Resolution
All tenant requests must resolve tenant identity through one of the following mechanisms:
1. **HTTP Header:** `X-Tenant-ID: {tenant_uuid}` or `X-Tenant-Slug: {slug}` (Mandatory for mobile & platform clients).
2. **Host Header / Subdomain:** `xyz-college.nexora.edu` maps automatically to tenant slug `xyz-college`.
3. **Database RLS Context:** The API gateway executes `SET LOCAL app.tenant_id = '{resolved_tenant_uuid}'` on every database connection before query execution.

### 1.3 General Protocol Principles
- **Resource Naming:** RESTful plural nouns (`/departments`, `/courses`, `/grades`).
- **Resource Identification:** UUIDv7 (`018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3d`).
- **Idempotency:** State-mutating endpoints (`POST /payments`, `POST /grades/batch-submit`, `POST /enrolments`) accept an `Idempotency-Key: {uuid}` header to prevent duplicate processing.
- **Date/Time Standard:** ISO-8601 UTC format (`YYYY-MM-DDTHH:mm:ss.sssZ`).
- **Currency & Precision:** All monetary amounts are formatted as standard decimal strings with 2 decimal places (`"15000.00"`).

---

# 2. Security, Authentication & Authorization (RBAC)

### 2.1 Role Matrix
| Role Code | Role Name | Description & Permissions Scope |
| :--- | :--- | :--- |
| `PLATFORM_OPERATOR` | Platform Operator | Global cross-tenant provisioning, license & system metrics. |
| `ADMIN` | System Administrator | Full tenant management: users, academic years, fee structures, timetable, approvals, reports. |
| `FACULTY` | Teaching Staff | Course material authoring, attendance marking, quizzes, grade entries, requests, flagging. |
| `STUDENT` | Enrolled Student | Self-service enrolment, view timetable, submit assignments, take quizzes, fee payments, grievances. |

### 2.2 Token Lifecycle
- **Access Token:** JWT Bearer token (RS256 signed, TTL: 15 minutes). Contains `sub` (user_id), `tenant_id`, `role`, `email`, and `permissions`.
- **Refresh Token:** Opaque cryptographically secure random token (TTL: 7 days, stored in HTTP-only, SameSite=Strict cookie or Authorization body).

---

# 3. Global Envelopes, Headers & Status Codes

### 3.1 Standard Success Envelope
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2026-10-04T18:30:00.000Z",
    "request_id": "req_018f9e6a-7b3b-7221",
    "version": "v1.0"
  },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### 3.2 Standard Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request payload contains invalid fields.",
    "details": [
      {
        "field": "credits",
        "issue": "Credits must be an integer between 1 and 8."
      }
    ],
    "timestamp": "2026-10-04T18:30:00.000Z",
    "request_id": "req_018f9e6a-7b3b-7221"
  }
}
```

### 3.3 HTTP Status Codes Dictionary
- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `202 Accepted`: Asynchronous operation initiated.
- `204 No Content`: Successful deletion or action with empty response body.
- `400 Bad Request`: Malformed syntax or invalid parameters.
- `401 Unauthorized`: Missing or expired authentication token.
- `403 Forbidden`: Authenticated user lacks sufficient RBAC privileges.
- `404 Not Found`: Resource does not exist or belongs to another tenant.
- `409 Conflict`: Business rule violation (e.g., timetable room clash, duplicate enrolment).
- `422 Unprocessable Entity`: Semantic validation failures.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: Unexpected runtime failure.

---

# 4. Module 1: Authentication, Tenant & Identity Management

### 4.1 `POST /auth/login`
- **Description:** Authenticates a user with email and password, returning JWT access and refresh tokens.
- **Access:** Public (Tenant-aware via `X-Tenant-ID` or slug).
- **Request Body:**
```json
{
  "email": "faculty.smith@nexora.edu",
  "password": "SecurePassword123!",
  "remember_me": true
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "rt_8f9e6a7b3b...",
    "expires_in": 900,
    "token_type": "Bearer",
    "user": {
      "id": "018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3d",
      "email": "faculty.smith@nexora.edu",
      "role": "FACULTY",
      "first_name": "John",
      "last_name": "Smith",
      "department_id": "018f9e6a-8c4c-7332-b4e3-2c2e1fac5b4e",
      "avatar_url": "https://storage.nexora.edu/avatars/user-123.jpg",
      "mfa_enabled": false
    }
  }
}
```

### 4.2 `POST /auth/refresh`
- **Description:** Rotates expired access tokens using a valid refresh token.
- **Access:** Public (With valid refresh token).
- **Request Body:**
```json
{
  "refresh_token": "rt_8f9e6a7b3b..."
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "rt_9a0b1c2d3e...",
    "expires_in": 900
  }
}
```

### 4.3 `POST /auth/logout`
- **Description:** Revokes current refresh token and blacklists current access token session.
- **Access:** `Authenticated` (All Roles).
- **Response `204 No Content`**

### 4.4 `POST /auth/password/reset-request`
- **Description:** Triggers a time-limited password reset email token.
- **Access:** Public.
- **Request Body:** `{ "email": "student@nexora.edu" }`
- **Response `200 OK`:** `{ "success": true, "message": "Password reset instructions sent." }`

### 4.5 `POST /auth/password/reset-confirm`
- **Description:** Sets a new password using a verified token.
- **Access:** Public.
- **Request Body:**
```json
{
  "token": "tok_reset_abc123456",
  "new_password": "NewStrongPassword2026!"
}
```
- **Response `200 OK`:** `{ "success": true, "message": "Password successfully updated." }`

### 4.6 `GET /auth/me`
- **Description:** Retrieves current authenticated user session, permissions, and profile context.
- **Access:** `Authenticated` (All Roles).
- **Response `200 OK`:** Returns full user profile object and mapped permissions.

---

# 5. Module 2: User Lifecycle & RBAC Management

### 5.1 `GET /users`
- **Description:** Paginated search and filtering of institution accounts.
- **Access:** `ADMIN`.
- **Query Params:** `page`, `page_size`, `role` (`ADMIN`, `FACULTY`, `STUDENT`), `department_id`, `status` (`ACTIVE`, `INACTIVE`, `SUSPENDED`), `search` (name, email, roll/reg number).
- **Response `200 OK`:** List of user objects with profile summaries.

### 5.2 `POST /users`
- **Description:** Provisions a new institutional user with automatic role profile initialization.
- **Access:** `ADMIN`.
- **Request Body:**
```json
{
  "email": "alex.taylor@nexora.edu",
  "role": "STUDENT",
  "first_name": "Alex",
  "last_name": "Taylor",
  "phone": "+91 9876543210",
  "student_profile": {
    "registration_number": "NEX2026CS101",
    "roll_number": "26CS01",
    "programme_id": "018f9e6a-8c4c-7332-b4e3-2c2e1fac5b4e",
    "batch_year": 2026,
    "current_semester": 1,
    "admission_date": "2026-08-01"
  }
}
```
- **Response `201 Created`:** Created user entity with generated onboarding activation token.

### 5.3 `POST /users/bulk-import`
- **Description:** Asynchronously processes a CSV/XLSX user provisioning roster.
- **Access:** `ADMIN`.
- **Request:** `multipart/form-data` with file upload (`roster.csv`) and role parameter.
- **Response `202 Accepted`:**
```json
{
  "success": true,
  "data": {
    "job_id": "018f9e6b-1234-7000-8000-abcdef123456",
    "status": "PROCESSING",
    "total_rows": 450,
    "check_status_url": "/background-jobs/018f9e6b-1234-7000-8000-abcdef123456"
  }
}
```

### 5.4 `GET /users/{id}` & `PATCH /users/{id}`
- **Description:** Retrieve or update user details, active status, contact details, and assigned roles.
- **Access:** `ADMIN` or `Self` (restricted fields).

### 5.5 `DELETE /users/{id}`
- **Description:** Soft-deletes user account, immediately invalidating active sessions.
- **Access:** `ADMIN`.

---

# 6. Module 3: Academic Structure & Scheduling

### 6.1 `GET /departments` & `POST /departments`
- **Description:** List institutional departments and create new academic departments.
- **Access:** `GET`: All Roles, `POST`: `ADMIN`.
- **Request Body (POST):**
```json
{
  "code": "CSE",
  "name": "Department of Computer Science & Engineering",
  "head_faculty_id": "018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3d",
  "budget_allocated": "5000000.00"
}
```

### 6.2 `GET /programmes` & `POST /programmes`
- **Description:** Degrees and academic programs (e.g., B.Tech CSE, MBA, M.Sc Data Science).
- **Access:** `GET`: All Roles, `POST`: `ADMIN`.
- **Request Body (POST):**
```json
{
  "department_id": "018f9e6a-8c4c-7332-b4e3-2c2e1fac5b4e",
  "code": "BTECH-CSE",
  "name": "Bachelor of Technology in Computer Science",
  "degree_level": "UNDERGRADUATE",
  "total_semesters": 8,
  "required_credits": 160
}
```

### 6.3 `GET /academic-years` & `POST /academic-years`
- **Description:** Manage institutional academic years (e.g., 2026–2027) and mark current active year.
- **Access:** `ADMIN`.

### 6.4 `GET /terms` & `POST /terms`
- **Description:** Manage Semesters / Trimesters with enrolment windows, teaching periods, and exam dates.
- **Access:** `GET`: All Roles, `POST`/`PATCH`: `ADMIN`.
- **Request Body (POST):**
```json
{
  "academic_year_id": "018f9e6a-9a00-7000-8000-000000000001",
  "name": "Fall Semester 2026",
  "term_number": 1,
  "start_date": "2026-08-01",
  "end_date": "2026-12-20",
  "enrolment_start": "2026-07-15T00:00:00Z",
  "enrolment_end": "2026-08-05T23:59:59Z",
  "is_current": true
}
```

### 6.5 `GET /calendar/events` & `POST /calendar/events`
- **Description:** Institutional academic calendar events, holidays, examination dates, and symposiums.
- **Access:** `GET`: All Roles, `POST`: `ADMIN`.

---

# 7. Module 4: Course Management, Offerings & Enrolment

### 7.1 `GET /courses` & `POST /courses`
- **Description:** Master course catalog with codes, credits, prerequisites, and syllabus descriptions.
- **Access:** `GET`: All Roles, `POST`/`PATCH`: `ADMIN`.
- **Request Body (POST):**
```json
{
  "department_id": "018f9e6a-8c4c-7332-b4e3-2c2e1fac5b4e",
  "code": "CS301",
  "name": "Distributed Systems & Cloud Computing",
  "credits": 4,
  "lecture_hours": 3,
  "lab_hours": 2,
  "prerequisite_course_ids": ["018f9e6a-0000-7000-8000-000000000050"],
  "syllabus_summary": "Architectures, consensus protocols, Paxos, Raft, microservices, gRPC."
}
```

### 7.2 `POST /course-offerings`
- **Description:** Instantiates a course section for a specific term, allocating capacity and primary instructor.
- **Access:** `ADMIN`.
- **Request Body:**
```json
{
  "course_id": "018f9e6a-1111-7000-8000-000000000002",
  "term_id": "018f9e6a-9a00-7000-8000-000000000001",
  "section": "A",
  "max_capacity": 60,
  "primary_faculty_id": "018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3d"
}
```

### 7.3 `POST /enrolments/register` (Student Course Registration)
- **Description:** Enrolls a student in a course offering during open enrolment window, verifying prerequisites and capacity.
- **Access:** `STUDENT` (Self) or `ADMIN`.
- **Request Body:**
```json
{
  "course_offering_ids": [
    "018f9e6a-2222-7000-8000-000000000003",
    "018f9e6a-2222-7000-8000-000000000004"
  ]
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "enrolled_courses": [
      {
        "offering_id": "018f9e6a-2222-7000-8000-000000000003",
        "course_code": "CS301",
        "status": "ENROLLED",
        "enrolled_at": "2026-08-02T10:15:30Z"
      }
    ],
    "total_credits_registered": 18
  }
}
```
- **Error `409 Conflict`:** If prerequisite missing, capacity exhausted, or timetable clash occurs.

### 7.4 `DELETE /enrolments/{enrolment_id}/drop`
- **Description:** Drop an enrolled course before the drop deadline.
- **Access:** `STUDENT` (Self), `ADMIN`.

---

# 8. Module 5: Timetable Engine & Room Allocation

### 8.1 `GET /rooms` & `POST /rooms`
- **Description:** Classrooms, lecture halls, and laboratories with capacity and equipment flags.
- **Access:** `GET`: All Roles, `POST`: `ADMIN`.

### 8.2 `POST /timetable/slots`
- **Description:** Schedules a recurring weekly lecture/lab slot with real-time collision detection.
- **Access:** `ADMIN`.
- **Request Body:**
```json
{
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "faculty_id": "018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3d",
  "room_id": "018f9e6a-3333-7000-8000-000000000005",
  "day_of_week": "MONDAY",
  "start_time": "09:00:00",
  "end_time": "10:30:00"
}
```
- **Response `201 Created`**
- **Error `409 Conflict`:**
```json
{
  "success": false,
  "error": {
    "code": "TIMETABLE_CLASH",
    "message": "Room 301 is already allocated to CS201 on MONDAY 09:00:00 - 10:30:00."
  }
}
```

### 8.3 `GET /timetable/my-schedule`
- **Description:** Returns the resolved weekly personalized schedule for the authenticated user (Student or Faculty).
- **Access:** `STUDENT`, `FACULTY`.
- **Query Params:** `term_id`, `week_date` (optional).
- **Response `200 OK`:** Weekly matrix of slots grouped by day, course, instructor, and room.

---

# 9. Module 6: Learning Management & Assessments

### 9.1 `POST /course-materials`
- **Description:** Uploads course slides, notes, or lab sheets linked to a course offering.
- **Access:** `FACULTY` (Assigned to course), `ADMIN`.
- **Request Body:**
```json
{
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "title": "Lecture 04 — Raft Consensus Protocol",
  "file_id": "018f9e6a-ffff-7000-8000-000000000099",
  "unit_number": 2,
  "is_published": true
}
```

### 9.2 `POST /assignments` & `GET /assignments`
- **Description:** Create assignments with deadlines, attachment files, and max points.
- **Access:** `POST`: `FACULTY`, `GET`: Enrolled `STUDENT`, `FACULTY`, `ADMIN`.
- **Request Body (POST):**
```json
{
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "title": "Lab 1 — Building a Key-Value Store with RPC",
  "description": "Implement a sharded KV store with RPC in Go.",
  "due_date": "2026-10-15T23:59:59Z",
  "max_marks": 100,
  "allow_late_submission": false
}
```

### 9.3 `POST /assignments/{id}/submissions`
- **Description:** Student submission for an assignment with attached solution files.
- **Access:** `STUDENT` (Enrolled).
- **Request Body:**
```json
{
  "file_id": "018f9e6a-eeee-7000-8000-000000000088",
  "student_notes": "Implemented with bonus consistency checks."
}
```

### 9.4 `POST /submissions/{id}/grade`
- **Description:** Grade student submission and provide feedback.
- **Access:** `FACULTY` (Assigned to course).
- **Request Body:**
```json
{
  "marks_obtained": 94.50,
  "feedback": "Excellent test coverage and concurrency handling."
}
```

### 9.5 `POST /quizzes` & `POST /quizzes/{id}/questions`
- **Description:** Online timed quizzes with multiple-choice, true/false, and short answer questions.
- **Access:** `FACULTY`.

### 9.6 `POST /quizzes/{id}/start` & `POST /quizzes/{id}/submit`
- **Description:** Timed quiz attempt lifecycle for enrolled students with automatic score computation.
- **Access:** `STUDENT` (Enrolled).

---

# 10. Module 7: Attendance & Academic Monitoring

### 10.1 `POST /attendance/sessions`
- **Description:** Creates an attendance session for a class lecture/lab.
- **Access:** `FACULTY` (Assigned instructor).
- **Request Body:**
```json
{
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "slot_id": "018f9e6a-4444-7000-8000-000000000006",
  "session_date": "2026-10-04",
  "topic_covered": "Distributed Transactions & 2PC"
}
```

### 10.2 `POST /attendance/sessions/{id}/records` (Bulk Mark)
- **Description:** Marks presence status for all enrolled students in a single transaction.
- **Access:** `FACULTY`.
- **Request Body:**
```json
{
  "records": [
    { "student_id": "018f9e6a-5555-7000-8000-000000000010", "status": "PRESENT" },
    { "student_id": "018f9e6a-5555-7000-8000-000000000011", "status": "ABSENT", "remarks": "Unexcused" },
    { "student_id": "018f9e6a-5555-7000-8000-000000000012", "status": "LATE" }
  ]
}
```
- **Response `200 OK`:** Updates percentage caches and triggers automated low-attendance alerts if threshold drops below 75% (BR-05).

### 10.3 `GET /attendance/student/{student_id}` & `GET /attendance/my-summary`
- **Description:** Detailed attendance percentage, total classes held, attended, and eligibility status per course.
- **Access:** `STUDENT` (Own), `FACULTY`, `ADMIN`.

### 10.4 `POST /academic-flags`
- **Description:** Flags a student for academic, attendance, or behavioural risk to trigger counseling workflows.
- **Access:** `FACULTY`, `ADMIN`.
- **Request Body:**
```json
{
  "student_id": "018f9e6a-5555-7000-8000-000000000011",
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "flag_type": "ATTENDANCE_SHORTAGE",
  "severity": "CRITICAL",
  "description": "Attendance currently at 62%, missed two consecutive assessments."
}
```

---

# 11. Module 8: Examinations, Grading & Transcripts

### 11.1 `GET /grading-scales` & `POST /grading-scales`
- **Description:** Configures institutional letter grade thresholds, grade points, and percentage ranges (e.g. A+ = 10.0, 90-100).
- **Access:** `ADMIN`.

### 11.2 `POST /grades/batch-entry`
- **Description:** Faculty enters internal/midterm/endterm marks in bulk for a course section.
- **Access:** `FACULTY` (Assigned).
- **Request Body:**
```json
{
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "evaluation_component": "MID_TERM",
  "max_marks": 50,
  "entries": [
    { "student_id": "018f9e6a-5555-7000-8000-000000000010", "marks_obtained": 46.5 },
    { "student_id": "018f9e6a-5555-7000-8000-000000000011", "marks_obtained": 38.0 }
  ]
}
```

### 11.3 `POST /grades/approval-batches` (BR-04 Workflow)
- **Description:** Submits grade batch for Dean/Admin review and official publication.
- **Access:** `FACULTY`.
- **Request Body:**
```json
{
  "course_offering_id": "018f9e6a-2222-7000-8000-000000000003",
  "term_id": "018f9e6a-9a00-7000-8000-000000000001",
  "comments": "Final internal and laboratory grades compiled."
}
```
- **Response `201 Created`:** Workflow batch created in `SUBMITTED` state.

### 11.4 `POST /grades/approval-batches/{id}/review`
- **Description:** Admin approves or rejects grade submission. Approving publishes final results to students.
- **Access:** `ADMIN`.
- **Request Body:**
```json
{
  "action": "APPROVE",
  "review_remarks": "Approved for publication."
}
```

### 11.5 `GET /results/my-grade-card` & `GET /results/student/{student_id}`
- **Description:** Computes and returns published SGPA, CGPA, earned credits, and course grade breakdown.
- **Access:** `STUDENT` (Self), `ADMIN`.

### 11.6 `POST /transcripts/requests`
- **Description:** Student requests an official stamped academic transcript PDF.
- **Access:** `STUDENT`.
- **Response `201 Created`:** Queues generation background job.

---

# 12. Module 9: Financial Operations & Fee Management

### 12.1 `GET /fee-structures` & `POST /fee-structures`
- **Description:** Configures program-wise and semester-wise fee components (Tuition, Lab, Library, Hostel).
- **Access:** `ADMIN`.
- **Request Body (POST):**
```json
{
  "programme_id": "018f9e6a-8c4c-7332-b4e3-2c2e1fac5b4e",
  "term_id": "018f9e6a-9a00-7000-8000-000000000001",
  "due_date": "2026-08-31",
  "components": [
    { "name": "Tuition Fee", "amount": "45000.00" },
    { "name": "Lab & Computing Facility", "amount": "10000.00" },
    { "name": "Examination Fee", "amount": "2500.00" }
  ]
}
```

### 12.2 `POST /fee-bills/generate-batch`
- **Description:** Triggers background batch generation of student fee invoices based on active fee structures.
- **Access:** `ADMIN`.

### 12.3 `GET /fee-bills/my-bill` & `GET /fee-bills/student/{student_id}`
- **Description:** Detailed view of outstanding, paid, overdue fee dues, and breakdown.
- **Access:** `STUDENT` (Self), `ADMIN`.

### 12.4 `POST /payments/create-order`
- **Description:** Initiates payment gateway transaction (e.g., Razorpay, Stripe, or Cashfree) for fee settlement.
- **Access:** `STUDENT`.
- **Request Body:**
```json
{
  "bill_id": "018f9e6a-6666-7000-8000-000000000020",
  "amount_to_pay": "57500.00",
  "payment_method": "ONLINE_GATEWAY"
}
```
- **Response `200 OK`:** Returns gateway order ID, signed token, and callback metadata.

### 12.5 `POST /payments/webhook`
- **Description:** Payment gateway webhook receiver for asynchronous transaction verification, receipt generation, and ledger update.
- **Access:** Public (Signature Verified).

### 12.6 `GET /payments/receipts/{receipt_id}/download`
- **Description:** Downloads digitally signed institutional fee receipt PDF.
- **Access:** `STUDENT`, `ADMIN`.

---

# 13. Module 10: Unified Workflow & Approval Engine

### 13.1 `POST /requests`
- **Description:** Initiates a formal institutional request (Faculty Leave, Timetable Adjustment, Syllabus Proposal, Student Bonafide Certificate).
- **Access:** `STUDENT`, `FACULTY`.
- **Request Body:**
```json
{
  "request_type": "FACULTY_LEAVE",
  "title": "Medical Leave Application (3 Days)",
  "payload": {
    "start_date": "2026-10-10",
    "end_date": "2026-10-12",
    "reason": "Medical appointment and recovery",
    "substitute_faculty_id": "018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3e"
  },
  "supporting_file_id": "018f9e6a-dddd-7000-8000-000000000077"
}
```
- **Response `201 Created`:** Returns created workflow request in `SUBMITTED` state.

### 13.2 `GET /requests`
- **Description:** List pending, approved, or rejected requests with filters.
- **Access:** `ADMIN` (All), `FACULTY`/`STUDENT` (Own initiated or assigned for review).

### 13.3 `POST /requests/{id}/transition`
- **Description:** Transitions request state through the 5-stage validation machine (`UNDER_REVIEW`, `APPROVED`, `REJECTED`, `COMPLETED`).
- **Access:** `ADMIN` or designated Approver.
- **Request Body:**
```json
{
  "action": "APPROVE",
  "remarks": "Leave approved; substitute notified."
}
```
- **Response `200 OK`:** Records immutable row in `workflow_transitions` (BR-10).

---

# 14. Module 11: Communication, Announcements & Forums

### 14.1 `POST /announcements` & `GET /announcements`
- **Description:** Publish targeted institutional announcements (Campus-wide, Department-specific, or Role-specific).
- **Access:** `POST`: `ADMIN`, `FACULTY`; `GET`: Targeted Users.
- **Request Body (POST):**
```json
{
  "title": "End-Term Examination Schedule Announcement",
  "content": "The final timetable for Fall 2026 is now officially released...",
  "target_roles": ["STUDENT", "FACULTY"],
  "target_department_ids": ["018f9e6a-8c4c-7332-b4e3-2c2e1fac5b4e"],
  "priority": "HIGH",
  "attachment_file_id": "018f9e6a-cccc-7000-8000-000000000066"
}
```

### 14.2 `POST /announcements/{id}/acknowledge-read`
- **Description:** Records student/faculty read receipt for compliance tracking.
- **Access:** `Authenticated` (All Roles).

### 14.3 `GET /discussions/course/{offering_id}` & `POST /discussions/posts`
- **Description:** Academic discussion threads, Q&A, and peer replies for course offerings.
- **Access:** Enrolled `STUDENT`, assigned `FACULTY`, `ADMIN`.

---

# 15. Module 12: Facilities, Placements, Library & Grievances

### 15.1 `GET /hostel/allocations` & `POST /hostel/allocate`
- **Description:** Hostel room inventory, block allocations, and occupant management.
- **Access:** `ADMIN`.

### 15.2 `GET /library/books` & `POST /library/loans/issue`
- **Description:** Library catalog searching, book issue/return tracking, and overdue fine calculations.
- **Access:** `GET`: All Roles, `POST`/`PATCH`: `ADMIN` / Librarian.

### 15.3 `POST /placements/drives` & `POST /placements/apply`
- **Description:** Campus recruitment drives, eligibility filters (CGPA >= 7.5), student applications, and offer tracking.
- **Access:** Drives: `ADMIN`, Apply: Eligible `STUDENT`.

### 15.4 `POST /grievances` & `PATCH /grievances/{id}`
- **Description:** Anonymous or named student grievance filing, escalation, and resolution tracking.
- **Access:** `STUDENT` (Create), `ADMIN` (Manage & Resolve).

---

# 16. Module 13: Analytics, Reporting & Audit System

### 16.1 `GET /analytics/institution/dashboard`
- **Description:** Real-time KPI summaries (Total students, faculty, average attendance, fee collection rate, active courses).
- **Access:** `ADMIN`.
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "total_students": 3450,
    "total_faculty": 180,
    "current_term_attendance_avg": 84.2,
    "total_fee_collected": "145000000.00",
    "total_fee_outstanding": "8500000.00",
    "active_academic_flags": 42
  }
}
```

### 16.2 `GET /analytics/attendance/trends`
- **Description:** Attendance distribution across departments, low-attendance alert lists.
- **Access:** `ADMIN`, `FACULTY` (Own department).

### 16.3 `GET /audit-logs`
- **Description:** Immutable audit logs of all sensitive operations (grade edits, role changes, fee overrides).
- **Access:** `ADMIN`.
- **Query Params:** `user_id`, `action`, `entity_type`, `from_date`, `to_date`, `page`, `page_size`.

---

# 17. Module 14: File Management & Background Jobs

### 17.1 `POST /files/upload-url` (Direct Cloud Upload)
- **Description:** Generates a presigned S3/GCS PUT URL for secure, direct binary uploads.
- **Access:** `Authenticated` (All Roles).
- **Request Body:**
```json
{
  "filename": "assignment_01_solution.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 2450000,
  "category": "ASSIGNMENT_SUBMISSION"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "file_id": "018f9e6a-eeee-7000-8000-000000000088",
    "upload_url": "https://s3.amazonaws.com/nexora-tenant-storage/tenants/123/...",
    "expires_in_seconds": 300
  }
}
```

### 17.2 `GET /background-jobs/{id}`
- **Description:** Polls status and completion details of asynchronous tasks (bulk imports, PDF reports).
- **Access:** `Authenticated` (Task initiator / Admin).

---

# 18. Module 15: Real-Time WebSocket API Specification

### 18.1 Gateway Handshake
- **URL:** `wss://api.nexora.edu/ws/v1`
- **Handshake Authentication:** Query parameter `?token=eyJhbGciOiJSUzI1Ni...` or sub-protocol header.

### 18.2 Inbound Client Actions
```json
{
  "action": "SUBSCRIBE",
  "channels": [
    "user:018f9e6a-7b3b-7221-a3f2-1b1e0fbc4a3d",
    "announcements:tenant",
    "course:018f9e6a-2222-7000-8000-000000000003"
  ]
}
```

### 18.3 Outbound Server Events
```json
{
  "event": "NOTIFICATION_RECEIVED",
  "payload": {
    "id": "018f9e6a-9999-7000-8000-000000000099",
    "type": "ACADEMIC_ALERT",
    "title": "Attendance Shortage Warning",
    "body": "Your attendance in CS301 has dropped to 72.5%.",
    "action_url": "/academics/attendance",
    "created_at": "2026-10-04T18:35:00Z"
  }
}
```

---

# 19. Error Codes Catalog & Standard Errors

| Error Code | HTTP Status | Description / Trigger Scenario |
| :--- | :--- | :--- |
| `AUTH_INVALID_CREDENTIALS` | `401 Unauthorized` | Invalid email or password provided. |
| `AUTH_TOKEN_EXPIRED` | `401 Unauthorized` | JWT access token has expired. |
| `PERMISSION_DENIED` | `403 Forbidden` | User role lacks RBAC permission for endpoint. |
| `TENANT_NOT_FOUND` | `404 Not Found` | Invalid tenant slug or header provided. |
| `RESOURCE_NOT_FOUND` | `404 Not Found` | Specified entity UUID does not exist. |
| `TIMETABLE_CLASH` | `409 Conflict` | Room, faculty, or student group double-booked. |
| `PREREQUISITE_NOT_MET` | `409 Conflict` | Student has not passed required prerequisite course. |
| `CAPACITY_EXCEEDED` | `409 Conflict` | Course offering has reached max student quota. |
| `WORKFLOW_INVALID_STATE` | `409 Conflict` | Invalid state transition attempted on request. |
| `ATTENDANCE_LOCKED` | `409 Conflict` | Attempted edit on attendance session after freeze window. |
| `VALIDATION_FAILED` | `422 Unprocessable` | Payload schema validation failed. |
| `RATE_LIMIT_EXCEEDED` | `429 Too Many Req` | User exceeded role-specific requests/minute ceiling. |
| `INTERNAL_SERVER_ERROR` | `500 Server Error` | Unhandled database or system exception. |

---

*Authored for the NEXORA Multi-Tenant Academic Operations Platform.*
