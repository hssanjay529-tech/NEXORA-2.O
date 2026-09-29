# NEXORA — Multi-Tenant Database Architecture

PostgreSQL 16 · single database · shared schema · row-level isolation by `tenant_id` (Implementation Plan §2).
The model has **57 tables: 55 tenant-scoped, plus `tenants` and `platform_operators`**, which are global. Every tenant-scoped table has a mandatory FK to `tenants`.

## 1. Global Conventions (apply to every tenant-scoped table)

| Rule                 | Detail                                                                                                                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Primary key          | `id uuid` (UUIDv7, time-ordered for index locality)                                                                                                                                                                                   |
| Tenant link          | `tenant_id uuid NOT NULL REFERENCES tenants(id)` on all 55 tables                                                                                                                                                                     |
| Composite uniqueness | `UNIQUE (tenant_id, id)` on every table, so children use **composite FKs** `(tenant_id, parent_id) → parent(tenant_id, id)`. A row can never point at another college's parent. Diagrams show the single-column form for readability. |
| RLS                  | `ENABLE` + `FORCE ROW LEVEL SECURITY`; policy `tenant_id = current_setting('app.tenant_id')::uuid` (USING and WITH CHECK)                                                                                                             |
| Audit columns        | `created_at`, `updated_at` (`timestamptz`); `created_by` where meaningful (omitted from the tables below)                                                                                                                             |
| Soft delete          | `deleted_at` only on `users`, `students`, `faculty`, `courses`. Grades, fees, documents and audit rows are never hard-deleted.                                                                                                        |
| Indexes              | Every index leads with `tenant_id`, e.g. `(tenant_id, student_id, term_id)`                                                                                                                                                           |
| Files                | No `*_URL` columns. All uploads and generated PDFs are rows in `files`, referenced by `*_file_id`. The PRD's URL fields become file FKs.                                                                                              |
| PRD arrays           | Normalised into junction tables (`courses[]`, `enrolledStudents[]`, `submissions[]`, `readByStudents[]`, `holidays[]`, `examWindows[]`, `events[]`)                                                                                   |
| Money                | `numeric(12,2)`; currency stored in `tenants.settings`                                                                                                                                                                                |
| Workflow status      | Shared enum `DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED` (PRD §13). Each entity keeps its own `status` column for fast queries; `workflow_transitions` holds the validated history (BR-10).                        |
| Polymorphic refs     | `(entity_type, entity_id)` cannot be a real FK. A trigger verifies the target row has the same `tenant_id`.                                                                                                                           |

## 2. ER Diagrams

Each diagram lists keys and foreign keys only. Full columns are in §3. `tenants` is drawn in every diagram, with a relationship to each tenant-scoped table.

### 2.1 Tenancy, Identity and Platform

```mermaid
erDiagram
  tenants {
    uuid id PK
    string slug UK
    string name
    string status
    jsonb settings
  }
  platform_operators {
    uuid id PK
    string email UK
  }
  users {
    uuid id PK
    uuid tenant_id FK
    string role
    string email
    string status
  }
  user_tokens {
    uuid id PK
    uuid tenant_id FK
    uuid user_id FK
    string purpose
  }
  login_attempts {
    uuid id PK
    uuid tenant_id FK
    uuid user_id FK
  }
  students {
    uuid id PK
    uuid tenant_id FK
    uuid user_id FK
    uuid programme_id FK
  }
  faculty {
    uuid id PK
    uuid tenant_id FK
    uuid user_id FK
    uuid department_id FK
  }
  files {
    uuid id PK
    uuid tenant_id FK
    uuid uploaded_by FK
    string storage_key
  }
  audit_logs {
    uuid id PK
    uuid tenant_id FK
    uuid user_id FK
    string action
  }
  background_jobs {
    uuid id PK
    uuid tenant_id FK
    string job_type
    string status
  }
  tenants ||--o{ users : owns
  tenants ||--o{ user_tokens : owns
  tenants ||--o{ login_attempts : owns
  tenants ||--o{ students : owns
  tenants ||--o{ faculty : owns
  tenants ||--o{ files : owns
  tenants ||--o{ audit_logs : owns
  tenants ||--o{ background_jobs : owns
  users ||--o| students : "has profile"
  users ||--o| faculty : "has profile"
  users ||--o{ user_tokens : issues
  users |o--o{ login_attempts : records
  users ||--o{ files : uploads
  users |o--o{ audit_logs : performs
```

### 2.2 Academic Structure and Scheduling

```mermaid
erDiagram
  departments {
    uuid id PK
    uuid tenant_id FK
    uuid head_faculty_id FK
    string name
  }
  programmes {
    uuid id PK
    uuid tenant_id FK
    uuid department_id FK
  }
  academic_years {
    uuid id PK
    uuid tenant_id FK
    string status
    uuid published_by FK
  }
  terms {
    uuid id PK
    uuid tenant_id FK
    uuid academic_year_id FK
  }
  calendar_events {
    uuid id PK
    uuid tenant_id FK
    uuid academic_year_id FK
    uuid term_id FK
    string event_type
  }
  courses {
    uuid id PK
    uuid tenant_id FK
    uuid department_id FK
    string course_code
    uuid syllabus_file_id FK
  }
  programme_courses {
    uuid id PK
    uuid tenant_id FK
    uuid programme_id FK
    uuid course_id FK
  }
  course_offerings {
    uuid id PK
    uuid tenant_id FK
    uuid course_id FK
    uuid term_id FK
    uuid faculty_id FK
  }
  enrollments {
    uuid id PK
    uuid tenant_id FK
    uuid offering_id FK
    uuid student_id FK
  }
  course_materials {
    uuid id PK
    uuid tenant_id FK
    uuid offering_id FK
    uuid file_id FK
  }
  rooms {
    uuid id PK
    uuid tenant_id FK
    string room_type
  }
  timetable_slots {
    uuid id PK
    uuid tenant_id FK
    uuid offering_id FK
    uuid room_id FK
    uuid faculty_id FK
  }
  tenants ||--o{ departments : owns
  tenants ||--o{ programmes : owns
  tenants ||--o{ academic_years : owns
  tenants ||--o{ terms : owns
  tenants ||--o{ calendar_events : owns
  tenants ||--o{ courses : owns
  tenants ||--o{ programme_courses : owns
  tenants ||--o{ course_offerings : owns
  tenants ||--o{ enrollments : owns
  tenants ||--o{ course_materials : owns
  tenants ||--o{ rooms : owns
  tenants ||--o{ timetable_slots : owns
  departments ||--o{ programmes : offers
  departments ||--o{ courses : owns
  departments ||--o{ faculty : employs
  departments }o--o| faculty : "headed by"
  programmes ||--o{ students : enrols
  programmes ||--o{ programme_courses : includes
  courses ||--o{ programme_courses : "listed in"
  academic_years ||--o{ terms : contains
  academic_years ||--o{ calendar_events : schedules
  terms |o--o{ calendar_events : scopes
  courses ||--o{ course_offerings : "offered as"
  terms ||--o{ course_offerings : hosts
  faculty ||--o{ course_offerings : teaches
  course_offerings ||--o{ enrollments : has
  students ||--o{ enrollments : "registers via"
  course_offerings ||--o{ course_materials : has
  files ||--o{ course_materials : stores
  course_offerings ||--o{ timetable_slots : scheduled
  rooms ||--o{ timetable_slots : hosts
  faculty ||--o{ timetable_slots : teaches
```

### 2.3 Assessment and Results

```mermaid
erDiagram
  attendance {
    uuid id PK
    uuid tenant_id FK
    uuid offering_id FK
    uuid student_id FK
    uuid marked_by FK
    date att_date
  }
  assignments {
    uuid id PK
    uuid tenant_id FK
    uuid offering_id FK
    uuid rubric_file_id FK
    string kind
  }
  quiz_questions {
    uuid id PK
    uuid tenant_id FK
    uuid assignment_id FK
  }
  assignment_submissions {
    uuid id PK
    uuid tenant_id FK
    uuid assignment_id FK
    uuid student_id FK
    uuid file_id FK
  }
  grade_records {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid offering_id FK
    string status
  }
  grading_scales {
    uuid id PK
    uuid tenant_id FK
    string grade
  }
  student_term_results {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid term_id FK
  }
  academic_flags {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid raised_by FK
    string flag_type
  }
  tenants ||--o{ attendance : owns
  tenants ||--o{ assignments : owns
  tenants ||--o{ quiz_questions : owns
  tenants ||--o{ assignment_submissions : owns
  tenants ||--o{ grade_records : owns
  tenants ||--o{ grading_scales : owns
  tenants ||--o{ student_term_results : owns
  tenants ||--o{ academic_flags : owns
  course_offerings ||--o{ attendance : tracks
  students ||--o{ attendance : has
  faculty ||--o{ attendance : marks
  course_offerings ||--o{ assignments : has
  assignments ||--o{ quiz_questions : contains
  assignments ||--o{ assignment_submissions : receives
  students ||--o{ assignment_submissions : submits
  files |o--o{ assignment_submissions : attaches
  students ||--o{ grade_records : earns
  course_offerings ||--o{ grade_records : "graded in"
  students ||--o{ student_term_results : summarised
  terms ||--o{ student_term_results : covers
  students ||--o{ academic_flags : "flagged in"
  faculty ||--o{ academic_flags : raises
  course_offerings |o--o{ academic_flags : "context of"
```

### 2.4 Finance, Examinations and Documents

```mermaid
erDiagram
  fee_structures {
    uuid id PK
    uuid tenant_id FK
    uuid programme_id FK
    uuid term_id FK
  }
  scholarships {
    uuid id PK
    uuid tenant_id FK
    string name
  }
  student_scholarships {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid scholarship_id FK
  }
  fee_records {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid fee_structure_id FK
    string status
  }
  payments {
    uuid id PK
    uuid tenant_id FK
    uuid fee_record_id FK
    uuid receipt_file_id FK
    string status
  }
  exams {
    uuid id PK
    uuid tenant_id FK
    uuid term_id FK
    uuid offering_id FK
    uuid room_id FK
  }
  exam_eligibility_rules {
    uuid id PK
    uuid tenant_id FK
    uuid term_id FK
  }
  exam_registrations {
    uuid id PK
    uuid tenant_id FK
    uuid exam_id FK
    uuid student_id FK
  }
  hall_tickets {
    uuid id PK
    uuid tenant_id FK
    uuid registration_id FK
    uuid file_id FK
  }
  document_requests {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid approved_by FK
    uuid file_id FK
  }
  tenants ||--o{ fee_structures : owns
  tenants ||--o{ scholarships : owns
  tenants ||--o{ student_scholarships : owns
  tenants ||--o{ fee_records : owns
  tenants ||--o{ payments : owns
  tenants ||--o{ exams : owns
  tenants ||--o{ exam_eligibility_rules : owns
  tenants ||--o{ exam_registrations : owns
  tenants ||--o{ hall_tickets : owns
  tenants ||--o{ document_requests : owns
  programmes ||--o{ fee_structures : prices
  terms ||--o{ fee_structures : "billed in"
  fee_structures ||--o{ fee_records : generates
  students ||--o{ fee_records : owes
  fee_records ||--o{ payments : "settled by"
  files |o--o{ payments : receipt
  scholarships ||--o{ student_scholarships : grants
  students ||--o{ student_scholarships : receives
  terms ||--o{ exams : schedules
  course_offerings ||--o{ exams : assesses
  rooms |o--o{ exams : hosts
  terms ||--o| exam_eligibility_rules : configures
  exams ||--o{ exam_registrations : has
  students ||--o{ exam_registrations : makes
  exam_registrations ||--o| hall_tickets : issues
  files |o--o{ hall_tickets : pdf
  students ||--o{ document_requests : requests
  users |o--o{ document_requests : approves
  files |o--o{ document_requests : generated
```

### 2.5 Workflow and Requests

```mermaid
erDiagram
  workflow_instances {
    uuid id PK
    uuid tenant_id FK
    string entity_type
    uuid entity_id
    uuid submitted_by FK
    string status
  }
  workflow_transitions {
    uuid id PK
    uuid tenant_id FK
    uuid instance_id FK
    uuid actor_id FK
  }
  course_proposals {
    uuid id PK
    uuid tenant_id FK
    uuid faculty_id FK
    uuid department_id FK
    uuid syllabus_file_id FK
  }
  leave_requests {
    uuid id PK
    uuid tenant_id FK
    uuid faculty_id FK
    uuid approved_by FK
  }
  schedule_change_requests {
    uuid id PK
    uuid tenant_id FK
    uuid faculty_id FK
    uuid slot_id FK
  }
  grievance_tickets {
    uuid id PK
    uuid tenant_id FK
    uuid student_id FK
    uuid assigned_to FK
  }
  tenants ||--o{ workflow_instances : owns
  tenants ||--o{ workflow_transitions : owns
  tenants ||--o{ course_proposals : owns
  tenants ||--o{ leave_requests : owns
  tenants ||--o{ schedule_change_requests : owns
  tenants ||--o{ grievance_tickets : owns
  workflow_instances ||--o{ workflow_transitions : logs
  users ||--o{ workflow_instances : submits
  users ||--o{ workflow_transitions : acts
  faculty ||--o{ course_proposals : proposes
  departments ||--o{ course_proposals : reviews
  faculty ||--o{ leave_requests : applies
  users |o--o{ leave_requests : approves
  faculty ||--o{ schedule_change_requests : requests
  timetable_slots ||--o{ schedule_change_requests : targets
  students ||--o{ grievance_tickets : raises
  users |o--o{ grievance_tickets : "assigned to"
```

### 2.6 Communication and Governance

9

```mermaid
erDiagram
  notifications {
    uuid id PK
    uuid tenant_id FK
    uuid sent_by FK
    uuid offering_id FK
    string target_role
  }
  notification_deliveries {
    uuid id PK
    uuid tenant_id FK
    uuid notification_id FK
    uuid user_id FK
    string channel
  }
  conversations {
    uuid id PK
    uuid tenant_id FK
    string conv_type
  }
  conversation_participants {
    uuid id PK
    uuid tenant_id FK
    uuid conversation_id FK
    uuid user_id FK
  }
  messages {
    uuid id PK
    uuid tenant_id FK
    uuid conversation_id FK
    uuid sender_id FK
    uuid parent_id FK
  }
  message_attachments {
    uuid id PK
    uuid tenant_id FK
    uuid message_id FK
    uuid file_id FK
  }
  discussion_threads {
    uuid id PK
    uuid tenant_id FK
    uuid offering_id FK
    uuid created_by FK
  }
  discussion_posts {
    uuid id PK
    uuid tenant_id FK
    uuid thread_id FK
    uuid author_id FK
    uuid parent_post_id FK
  }
  compliance_records {
    uuid id PK
    uuid tenant_id FK
    uuid department_id FK
    uuid owner_id FK
  }
  compliance_versions {
    uuid id PK
    uuid tenant_id FK
    uuid compliance_id FK
    uuid file_id FK
  }
  analytics_reports {
    uuid id PK
    uuid tenant_id FK
    uuid generated_by FK
    uuid department_id FK
    uuid file_id FK
  }
  tenants ||--o{ notifications : owns
  tenants ||--o{ notification_deliveries : owns
  tenants ||--o{ conversations : owns
  tenants ||--o{ conversation_participants : owns
  tenants ||--o{ messages : owns
  tenants ||--o{ message_attachments : owns
  tenants ||--o{ discussion_threads : owns
  tenants ||--o{ discussion_posts : owns
  tenants ||--o{ compliance_records : owns
  tenants ||--o{ compliance_versions : owns
  tenants ||--o{ analytics_reports : owns
  users ||--o{ notifications : sends
  course_offerings |o--o{ notifications : "announced in"
  notifications ||--o{ notification_deliveries : "delivered as"
  users ||--o{ notification_deliveries : receives
  conversations ||--o{ conversation_participants : includes
  users ||--o{ conversation_participants : joins
  conversations ||--o{ messages : contains
  users ||--o{ messages : sends
  messages |o--o{ messages : "reply to"
  messages ||--o{ message_attachments : has
  files ||--o{ message_attachments : stores
  course_offerings ||--o{ discussion_threads : hosts
  discussion_threads ||--o{ discussion_posts : contains
  discussion_posts |o--o{ discussion_posts : "reply to"
  users ||--o{ discussion_posts : writes
  departments |o--o{ compliance_records : owns
  compliance_records ||--o{ compliance_versions : versions
  files ||--o{ compliance_versions : stores
  users |o--o{ analytics_reports : generates
  files |o--o{ analytics_reports : output
```

## 3. Schema Reference

Columns listed exclude `id`, `tenant_id`, `created_at`, `updated_at`, which every tenant-scoped table has. `UQ` = unique constraint, `IX` = index, `CK` = check. Every `UQ`/`IX` shown starts with `tenant_id`.

### 3.1 Tenancy, Identity and Platform

| Table                         | Columns                                                                                                                                                                   | Constraints and indexes                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `tenants` (global)            | `slug`, `name`, `status` (ACTIVE/SUSPENDED/ARCHIVED), `settings jsonb` (currency, timezone, branding, grading and attendance thresholds), `created_at`                    | `UQ(slug)`. No RLS; readable by the app role for resolution only.                                                                         |
| `platform_operators` (global) | `email`, `password_hash`, `status`, `last_login_at`                                                                                                                       | `UQ(email)`. Separate login, no grants on tenant tables.                                                                                  |
| `users`                       | `role` (ADMIN/FACULTY/STUDENT), `email citext`, `password_hash`, `status` (ACTIVE/INACTIVE/ARCHIVED), `last_login_at`, `failed_login_count`, `locked_until`, `deleted_at` | `UQ(tenant_id,email)`; `IX(tenant_id,role,status)`                                                                                        |
| `user_tokens`                 | `user_id`, `purpose` (REFRESH/PASSWORD_RESET/ACTIVATION), `token_hash`, `expires_at`, `used_at`, `revoked_at`                                                             | `UQ(tenant_id,token_hash)`; `IX(tenant_id,user_id,purpose)`                                                                               |
| `login_attempts`              | `user_id` (nullable), `email`, `success`, `ip_address`, `attempted_at`                                                                                                    | Partition by month; `IX(tenant_id,email,attempted_at)`                                                                                    |
| `students`                    | `user_id`, `programme_id`, `roll_no`, `admission_year`, `current_term_no`, `status`, `deleted_at`                                                                         | `UQ(tenant_id,user_id)`, `UQ(tenant_id,roll_no)`; `IX(tenant_id,programme_id)`                                                            |
| `faculty`                     | `user_id`, `department_id`, `employee_no`, `designation`, `deleted_at`                                                                                                    | `UQ(tenant_id,user_id)`, `UQ(tenant_id,employee_no)`; `IX(tenant_id,department_id)`                                                       |
| `files`                       | `uploaded_by`, `storage_key`, `filename`, `mime_type`, `size_bytes`, `sha256`, `kind`                                                                                     | `UQ(tenant_id,storage_key)`; `storage_key` starts `{tenant_id}/…` (CK)                                                                    |
| `audit_logs`                  | `user_id`, `action`, `entity_type`, `entity_id`, `old_value jsonb`, `new_value jsonb`, `ip_address`, `occurred_at`                                                        | Partition by month; **insert-only** (`REVOKE UPDATE, DELETE`); `IX(tenant_id,entity_type,entity_id)`, `IX(tenant_id,user_id,occurred_at)` |
| `background_jobs`             | `job_type` (REPORT/DOCUMENT/NOTIFY), `payload jsonb`, `status`, `run_at`, `attempts`, `locked_at`, `last_error`                                                           | Worker claims with `FOR UPDATE SKIP LOCKED`; `IX(tenant_id,status,run_at)`                                                                |

### 3.2 Academic Structure and Scheduling

| Table               | Columns                                                                                                                    | Constraints and indexes                                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `departments`       | `name`, `head_faculty_id` (nullable), `budget`, `established_on`                                                           | `UQ(tenant_id,name)`                                                                                                                              |
| `programmes`        | `department_id`, `name`, `duration_terms`, `degree_level`                                                                  | `UQ(tenant_id,name)`                                                                                                                              |
| `academic_years`    | `label` (e.g. 2026-27), `start_date`, `end_date`, `status` (DRAFT/PUBLISHED), `published_by`, `published_at`               | `UQ(tenant_id,label)`; CK `end_date > start_date`                                                                                                 |
| `terms`             | `academic_year_id`, `name`, `term_no`, `start_date`, `end_date`, `enrolment_opens_at`, `enrolment_closes_at`, `is_current` | `UQ(tenant_id,academic_year_id,term_no)`; partial unique on `is_current` per tenant                                                               |
| `calendar_events`   | `academic_year_id`, `term_id` (nullable), `event_type` (HOLIDAY/EXAM_WINDOW/EVENT), `title`, `start_date`, `end_date`      | `IX(tenant_id,academic_year_id,event_type)`. Replaces `holidays[]`, `examWindows[]`, `events[]`.                                                  |
| `courses`           | `department_id`, `course_code`, `title`, `credits`, `syllabus_file_id`, `status`, `deleted_at`                             | `UQ(tenant_id,course_code)`                                                                                                                       |
| `programme_courses` | `programme_id`, `course_id`, `term_no`, `is_mandatory`                                                                     | `UQ(tenant_id,programme_id,course_id)`                                                                                                            |
| `course_offerings`  | `course_id`, `term_id`, `faculty_id`, `section`, `capacity`, `status`                                                      | `UQ(tenant_id,course_id,term_id,section)`; `IX(tenant_id,faculty_id,term_id)`. This is the unit for attendance, grades and timetable.             |
| `enrollments`       | `offering_id`, `student_id`, `status` (ENROLLED/DROPPED/COMPLETED), `enrolled_at`                                          | `UQ(tenant_id,offering_id,student_id)`; `IX(tenant_id,student_id)`                                                                                |
| `course_materials`  | `offering_id`, `file_id`, `title`, `uploaded_by`                                                                           | `IX(tenant_id,offering_id)`                                                                                                                       |
| `rooms`             | `code`, `room_type` (CLASSROOM/LAB), `capacity`, `building`                                                                | `UQ(tenant_id,code)`                                                                                                                              |
| `timetable_slots`   | `offering_id`, `room_id`, `faculty_id`, `day_of_week`, `start_time`, `end_time`                                            | CK `end_time > start_time`; exclusion constraints prevent double-booking a room or a faculty member in overlapping slots within a tenant and term |

### 3.3 Assessment and Results

| Table                    | Columns                                                                                                                                                                                 | Constraints and indexes                                                                                                                                                                                                     |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `attendance`             | `offering_id`, `student_id`, `att_date`, `status` (PRESENT/ABSENT/LATE/EXCUSED), `marked_by`                                                                                            | `UQ(tenant_id,offering_id,student_id,att_date)`; partition by term or year; `IX(tenant_id,student_id,att_date)`. The student must be enrolled (composite FK to `enrollments`). Attendance % is a view, not a stored column. |
| `assignments`            | `offering_id`, `kind` (ASSIGNMENT/QUIZ), `title`, `description`, `due_at`, `max_marks`, `rubric_file_id`, `status`, `created_by`                                                        | `IX(tenant_id,offering_id,due_at)`                                                                                                                                                                                          |
| `quiz_questions`         | `assignment_id`, `question_text`, `options jsonb`, `correct_answer`, `marks`                                                                                                            | Supports auto-grading (FAC-03)                                                                                                                                                                                              |
| `assignment_submissions` | `assignment_id`, `student_id`, `file_id`, `answers jsonb`, `submitted_at`, `marks`, `feedback`, `graded_by`, `status`                                                                   | `UQ(tenant_id,assignment_id,student_id)`                                                                                                                                                                                    |
| `grade_records`          | `student_id`, `offering_id`, `internal_marks`, `final_marks`, `grade`, `grade_points`, `status` (workflow enum), `submitted_by`, `approved_by`, `published_at`                          | `UQ(tenant_id,student_id,offering_id)`; students may read only `status = COMPLETED AND published_at IS NOT NULL` (BR-04)                                                                                                    |
| `grading_scales`         | `grade`, `min_marks`, `max_marks`, `grade_points`                                                                                                                                       | Per-tenant config; `UQ(tenant_id,grade)`                                                                                                                                                                                    |
| `student_term_results`   | `student_id`, `term_id`, `sgpa`, `cgpa`, `credits_earned`, `published_at`                                                                                                               | `UQ(tenant_id,student_id,term_id)`. CGPA is derived and stored here on publish, not in `grade_records`.                                                                                                                     |
| `academic_flags`         | `student_id`, `offering_id` (nullable), `flag_type` (ATTENDANCE/ACADEMIC/PLAGIARISM/MISCONDUCT/WELFARE/PERFORMANCE), `raised_by`, `description`, `status`, `assigned_to`, `resolved_at` | `IX(tenant_id,student_id,status)`                                                                                                                                                                                           |

### 3.4 Finance, Examinations and Documents

| Table                    | Columns                                                                                                                                                                                         | Constraints and indexes                                                                                        |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `fee_structures`         | `programme_id`, `term_id`, `name`, `amount`, `due_date`                                                                                                                                         | `IX(tenant_id,programme_id,term_id)`                                                                           |
| `scholarships`           | `name`, `kind` (PERCENT/FIXED), `value`, `criteria`                                                                                                                                             | `UQ(tenant_id,name)`                                                                                           |
| `student_scholarships`   | `student_id`, `scholarship_id`, `term_id`, `awarded_at`                                                                                                                                         | `UQ(tenant_id,student_id,scholarship_id,term_id)`                                                              |
| `fee_records`            | `student_id`, `fee_structure_id`, `amount_due`, `discount`, `due_date`, `paid_date`, `status` (PENDING/PAID/OVERDUE/PARTIAL/CANCELLED)                                                          | `IX(tenant_id,student_id,status)`; `IX(tenant_id,due_date)` where `status IN (PENDING,OVERDUE)`                |
| `payments`               | `fee_record_id`, `amount`, `method`, `gateway_ref`, `status` (INITIATED/VERIFIED/FAILED), `verified_at`, `receipt_file_id`                                                                      | `UQ(tenant_id,gateway_ref)` for idempotency; a fee record becomes `PAID` only from `VERIFIED` payments (BR-06) |
| `exams`                  | `term_id`, `offering_id`, `exam_type`, `exam_date`, `start_time`, `end_time`, `room_id`, `max_marks`                                                                                            | `IX(tenant_id,term_id,exam_date)`                                                                              |
| `exam_eligibility_rules` | `term_id`, `min_attendance_pct`, `require_fees_cleared`, `extra_rules jsonb`                                                                                                                    | `UQ(tenant_id,term_id)` (BR-07)                                                                                |
| `exam_registrations`     | `exam_id`, `student_id`, `is_eligible`, `status`, `registered_at`                                                                                                                               | `UQ(tenant_id,exam_id,student_id)`                                                                             |
| `hall_tickets`           | `registration_id`, `file_id`, `ticket_no`, `issued_at`                                                                                                                                          | `UQ(tenant_id,registration_id)`, `UQ(tenant_id,ticket_no)`                                                     |
| `document_requests`      | `student_id`, `doc_type` (BONAFIDE/TRANSCRIPT/GRADE_CARD/TRANSFER_CERTIFICATE/COURSE_COMPLETION/OTHER), `status` (workflow enum), `requested_at`, `approved_by`, `file_id`, `verification_code` | `UQ(tenant_id,verification_code)`; download allowed only when `status = APPROVED` or later (BR-08)             |

### 3.5 Workflow and Requests

| Table                      | Columns                                                                                                                                                                       | Constraints and indexes                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `workflow_instances`       | `entity_type`, `entity_id`, `submitted_by`, `status`, `current_step`, `submitted_at`, `completed_at`                                                                          | `UQ(tenant_id,entity_type,entity_id)`; `IX(tenant_id,status)` for the pending-approvals dashboard |
| `workflow_transitions`     | `instance_id`, `from_status`, `to_status`, `actor_id`, `remarks`, `occurred_at`                                                                                               | Insert-only; the service validates allowed transitions (BR-10)                                    |
| `course_proposals`         | `faculty_id`, `department_id`, `course_title`, `course_code`, `credits`, `description`, `syllabus_file_id`, `status`, `submitted_at`, `reviewed_by`, `reviewed_at`, `remarks` | `IX(tenant_id,status)`                                                                            |
| `leave_requests`           | `faculty_id`, `leave_type`, `start_date`, `end_date`, `reason`, `status`, `approved_by`, `approved_at`, `remarks`                                                             | CK `end_date >= start_date`                                                                       |
| `schedule_change_requests` | `faculty_id`, `slot_id`, `requested_day`, `requested_start`, `requested_end`, `reason`, `status`, `reviewed_by`                                                               | `IX(tenant_id,status)`                                                                            |
| `grievance_tickets`        | `student_id`, `category`, `description`, `status` (OPEN/IN_PROGRESS/WAITING_FOR_RESPONSE/RESOLVED/CLOSED/REJECTED), `assigned_to`, `resolved_at`                              | `IX(tenant_id,status,assigned_to)`                                                                |

### 3.6 Communication and Governance

| Table                       | Columns                                                                                                                              | Constraints and indexes                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `notifications`             | `sent_by`, `offering_id` (nullable, for course announcements), `event_type`, `target_role` (nullable), `title`, `message`, `sent_at` | `IX(tenant_id,sent_at)`                                                                         |
| `notification_deliveries`   | `notification_id`, `user_id`, `channel` (IN_APP/EMAIL/SMS/PUSH), `status`, `sent_at`, `read_at`                                      | Partition by month; `IX(tenant_id,user_id,read_at)`. Replaces `readByStudents[]`.               |
| `conversations`             | `conv_type` (DIRECT/GROUP), `title`                                                                                                  | Course discussions use `discussion_threads` instead                                             |
| `conversation_participants` | `conversation_id`, `user_id`, `last_read_at`                                                                                         | `UQ(tenant_id,conversation_id,user_id)`                                                         |
| `messages`                  | `conversation_id`, `sender_id`, `parent_id`, `body`, `search_vector tsvector`, `sent_at`                                             | `IX(tenant_id,conversation_id,sent_at)`; GIN on `(search_vector)` filtered by tenant in queries |
| `message_attachments`       | `message_id`, `file_id`                                                                                                              | `UQ(tenant_id,message_id,file_id)`                                                              |
| `discussion_threads`        | `offering_id`, `title`, `created_by`, `is_locked`                                                                                    | `IX(tenant_id,offering_id)`                                                                     |
| `discussion_posts`          | `thread_id`, `author_id`, `parent_post_id`, `body`, `search_vector`                                                                  | `IX(tenant_id,thread_id,created_at)`                                                            |
| `compliance_records`        | `department_id`, `requirement`, `owner_id`, `submission_date`, `expiry_date`, `status`, `remarks`                                    | `IX(tenant_id,expiry_date)` for expiry alerts                                                   |
| `compliance_versions`       | `compliance_id`, `version_no`, `file_id`, `uploaded_by`                                                                              | `UQ(tenant_id,compliance_id,version_no)`                                                        |
| `analytics_reports`         | `report_type`, `generated_by`, `department_id`, `term_id`, `parameters jsonb`, `status`, `file_id`, `generated_at`                   | Generated through `background_jobs`                                                             |

## 4. Scalability and Isolation Notes

- **Isolation in depth:** `tenant_id` on every row, composite FKs, RLS with `FORCE`, and an app role without `BYPASSRLS`. Cross-tenant references are structurally impossible, not just filtered.
- **Growth tables** (`attendance`, `audit_logs`, `login_attempts`, `notification_deliveries`) are range-partitioned by time. Old partitions can be detached and archived. Audit partitions are kept for the retention period the institution requires.
- **Shard-ready:** because `tenant_id` leads every key and index, a very large college can later be moved to a dedicated database, or the whole schema distributed by `tenant_id` (e.g. Citus), without changing queries.
- **Noisy neighbours:** per-tenant rate limits, a `statement_timeout` on the app role, and keyset pagination on every list endpoint.
- **Analytics:** dashboards read tenant-filtered aggregates. Heavy ones become materialised views or `student_term_results`-style summary tables, refreshed by `background_jobs`. Read replicas can serve reports.
- **Retention:** grades, fees, payments, documents and audit rows are never hard-deleted. Tenant offboarding is an export followed by a batch delete keyed on `tenant_id`.
- **Deliberate deviations from the PRD entity list:** `Course` is split into `courses` (catalogue) and `course_offerings` (per term, with faculty), since attendance, grades and timetables belong to an offering. `CGPA` moves out of `grade_records` into `student_term_results`. `Academic Calendar` is `academic_years` + `terms` + `calendar_events`.
