================================================================================
  NEXORA — COLLEGE MANAGEMENT PORTAL
  Implementation Plan v1.0
  26-Week Build Roadmap
================================================================================

Project Snapshot
----------------
Phases                  : 6
Requirements            : 28
Modules                 : 24
Estimated Duration      : ~26 Weeks
User Roles              : Admin, Faculty, Student
Core Data Entities      : 16
Approval Workflows      : 5
Business Rules          : 10
High-Priority Reqs      : 17
Notification Channels   : 4


================================================================================
  1. BUILD PHASES
================================================================================

────────────────────────────────────────────────────────────────────────────────
PHASE 1 — FOUNDATION & AUTHENTICATION                          Weeks 1–3 (3 wks)
────────────────────────────────────────────────────────────────────────────────

Modules & Requirements:
  [1] Project Setup
        - Repository, CI/CD, development / staging / production environments

  [2] Authentication System                                       [ADM-01 · High]
        - Login, sessions, role-based access control (RBAC)

  [3] User Management                                            [ADM-01 · High]
        - Create, update, deactivate, and archive accounts (Admin/Faculty/Student)

  [4] Role-Based Access Control                                   [BR-01 · High]
        - Enforce the full permission matrix at API and service level

  [5] Database Schema
        - Model all 16 core entities with relationships and migrations

  [6] Audit Trail                                                 [BR-09 · High]
        - Log all sensitive create, update, approve, reject, delete operations

Milestone — Week 3:
  All three roles can authenticate and log in.
  RBAC enforced. Database schema live. Audit trail recording sensitive actions.


────────────────────────────────────────────────────────────────────────────────
PHASE 2 — ACADEMIC CORE                                        Weeks 4–9 (6 wks)
────────────────────────────────────────────────────────────────────────────────

Modules & Requirements:
  [1] Department Management                                      [ADM-03 · High]
        - Create departments, assign heads, allocate budgets

  [2] Academic Calendar                                          [ADM-02 · High]
        - Semesters, holidays, examination windows, publish to all roles

  [3] Course Management                                          [STU-01 · High]
        - Students register for courses during enrolment window

  [4] Course Materials                                           [FAC-01 · High]
        - Faculty upload lecture notes, slides, and reading materials

  [5] Timetable                                               [ADM-06 · Medium]
        - Visual timetable editor; faculty and students view own schedule
        - Refs: ADM-06, STU-02, FAC-07

  [6] Attendance                                                 [FAC-02 · High]
        - Faculty mark daily attendance; students view own percentage
        - Refs: FAC-02, STU-02, BR-05

Milestone — Week 9:
  Core academic operations functional.
  Departments, courses, timetable, and attendance are live.
  Faculty can record attendance; students can view their schedule.


────────────────────────────────────────────────────────────────────────────────
PHASE 3 — ASSESSMENTS & GRADING                               Weeks 10–14 (5 wks)
────────────────────────────────────────────────────────────────────────────────

Modules & Requirements:
  [1] Assignments & Quizzes                                      [FAC-03 · High]
        - Faculty create, publish, and auto-grade; students submit
        - Refs: FAC-03, STU-03

  [2] Grade Management                                           [FAC-04 · High]
        - Faculty enter internal marks and final results; students view grade cards
        - Refs: FAC-04, STU-04, BR-04

  [3] Grade Approval Workflow                                     [BR-04 · High]
        - Faculty → Submit → Admin Review → Approved/Rejected → Student Result

  [4] Examination Management                                     [STU-06 · High]
        - Students register for exams, download hall tickets, check eligibility (BR-07)

  [5] Academic Flag System                                     [FAC-05 · Medium]
        - Faculty raise flags (ATTENDANCE, ACADEMIC, PLAGIARISM, WELFARE, etc.)
        - Admin reviews and assigns intervention; resolution tracked

  [6] Course Proposals                                           [FAC-09 · Low]
        - Faculty propose new courses or syllabus changes
        - Department Review → Admin Review → Approved/Rejected
        - Refs: FAC-09, ADM-08

Milestone — Week 14:
  Assessments and grade workflows run end-to-end.
  Faculty create assignments, students submit, grades pass through approval,
  and results publish to students.


────────────────────────────────────────────────────────────────────────────────
PHASE 4 — FINANCE & DOCUMENTS                                 Weeks 15–18 (4 wks)
────────────────────────────────────────────────────────────────────────────────

Modules & Requirements:
  [1] Fee Management                                             [ADM-05 · High]
        - Configure fee structures, apply scholarships, track payment status
        - Refs: ADM-05, STU-05, BR-06

  [2] Payment Integration                                         [BR-06 · High]
        - Online payment gateway; verify transaction before marking PAID
        - Generate and download official payment receipts

  [3] Document Management                                      [STU-09 · Medium]
        - Students request bonafide certificates, transcripts, grade cards, etc.
        - Supported types: BONAFIDE, TRANSCRIPT, GRADE_CARD, TRANSFER_CERTIFICATE,
          COURSE_COMPLETION, OTHER

  [4] Document Approval Workflow                                   [BR-08 · High]
        - Request → Validation → Admin Approval → Generation → Digital Verification
          → Student Download

  [5] Leave Request System                                     [FAC-08 · Medium]
        - Faculty apply for leave; Admin approves/rejects; status tracked

  [6] Grievance Management                                     [STU-08 · Medium]
        - Students raise grievance tickets; assigned to Admin; resolution tracked
        - Ticket states: OPEN → IN_PROGRESS → WAITING → RESOLVED → CLOSED

Milestone — Week 18:
  Fees collected and documents issued.
  Online fee payments verified, receipts downloadable.
  Document requests processed through admin approval.


────────────────────────────────────────────────────────────────────────────────
PHASE 5 — COMMUNICATION & NOTIFICATIONS                       Weeks 19–22 (4 wks)
────────────────────────────────────────────────────────────────────────────────

Modules & Requirements:
  [1] Notification System                                      [ADM-07 · Medium]
        - Event-driven alerts for 14 events:
          Assignment Published, Deadline Approaching, Attendance Warning,
          Exam Registration Open, Hall Ticket Available, Fee Due,
          Fee Payment Successful, Grade Published, Course Registration Open,
          Grievance Updated, Document Approved, Leave Request Updated,
          Academic Flag Created, Institutional Announcement

  [2] Multi-Channel Delivery                                   [ADM-07 · Medium]
        - Channels: IN_APP, EMAIL, SMS, PUSH

  [3] In-Portal Messaging                                        [STU-10 · Low]
        - Direct messaging between Faculty ↔ Students
        - Refs: FAC-06, STU-10

  [4] Discussion Boards                                        [FAC-06 · Medium]
        - Faculty create threaded course discussion boards
        - Students participate per course

  [5] Announcement System                                      [ADM-07 · Medium]
        - Admin broadcasts targeted notices to role groups

  [6] Compliance Tracker                                         [ADM-09 · Low]
        - Accreditation document vault, compliance deadline calendar,
          expiry notifications, audit history, version tracking

Milestone — Week 22:
  Full communication layer active.
  Notifications firing for all 14 event types.
  In-portal messaging, course discussion boards, and announcements operational.


────────────────────────────────────────────────────────────────────────────────
PHASE 6 — ANALYTICS, QA & LAUNCH                              Weeks 23–26 (4 wks)
────────────────────────────────────────────────────────────────────────────────

Modules & Requirements:
  [1] Analytics Hub                                            [ADM-04 · Medium]
        - Institution-wide: enrolment trends, pass rates, fee collection
        - Faculty: assigned course and student insights
        - Refs: ADM-04, STU-07

  [2] Student Performance Dashboard                            [STU-07 · Medium]
        - CGPA trend graphs, attendance %, assignment completion,
          internal marks, final grades, performance trend

  [3] Institution Reports                                      [ADM-04 · Medium]
        - Async report generation; downloadable report links
        - Department performance, semester analysis, pass/fail stats

  [4] Search & Filtering
        - Global search across: Users, Courses, Assignments, Attendance,
          Grades, Fee Records, Grievances, Documents, Notifications
        - Filters: Department, Programme, Semester, Academic Year, Role,
          Status, Date Range, Course, Faculty, Student

  [5] End-to-End Testing
        - Validate all 28 requirements across all three roles

  [6] Production Launch
        - Final deployment, monitoring setup, error tracking, handover docs

Milestone — Week 26:
  NEXORA v1.0 LAUNCH.
  All 28 requirements validated, dashboards populated with real data,
  production deployment complete.


================================================================================
  2. DELIVERABLES BY PHASE
================================================================================

Phase   Deliverables                                       Requirements     Priority
------  -------------------------------------------------  ---------------  --------
Phase 1 Auth system, user CRUD, RBAC, DB schema,          ADM-01,          High
        audit trail                                        BR-01, BR-09

Phase 2 Departments, academic calendar, courses,           ADM-02, ADM-03,  High
        timetable, attendance, materials                   ADM-06, FAC-01,
                                                           FAC-02, STU-01,
                                                           STU-02

Phase 3 Assignments, grading, approval workflows,          FAC-03–05,       High
        examinations, academic flags, course proposals     FAC-09, ADM-08,
                                                           STU-03, STU-04,
                                                           STU-06

Phase 4 Fee management, payment gateway, documents,        ADM-05, FAC-08,  High
        leave requests, grievances                         STU-05, STU-08,
                                                           STU-09

Phase 5 Notifications, messaging, discussion boards,       ADM-07, ADM-09,  Medium
        compliance tracker                                 FAC-06, FAC-07,
                                                           STU-10

Phase 6 Analytics dashboards, global search,               ADM-04, STU-07   Medium
        E2E testing, production launch


================================================================================
  3. RECOMMENDED TECH STACK
================================================================================

Frontend
  - React / Next.js       UI framework
  - TypeScript            Type safety
  - Tailwind CSS          Styling
  - React Query           Data fetching and caching
  - Recharts / Chart.js   Analytics visualisations

Backend
  - Node.js + Express or NestJS
  - REST / GraphQL API
  - JWT + Sessions        Authentication tokens
  - Bull / BullMQ         Job queues (async reports, notifications)
  - Zod / Joi             Input validation

Database & Storage
  - PostgreSQL            Primary relational database
  - Prisma / TypeORM      ORM with migration support
  - Redis                 Caching and session storage
  - S3-compatible storage File uploads (assignments, materials, documents)

Infrastructure
  - Docker + Docker Compose
  - GitHub Actions        CI/CD pipelines
  - AWS / GCP / Azure     Cloud hosting
  - SendGrid / Twilio     Email and SMS delivery
  - Sentry                Error monitoring and alerting


================================================================================
  4. KEY RISKS & MITIGATIONS
================================================================================

[HIGH] RBAC Permission Leaks
  Risk     : Students or faculty accessing data outside their authorised scope.
  Mitigate : Middleware-enforced permission checks at every API route.
             Service-layer authorisation (never frontend-only).
             Integration tests for every protected route.
             Negative authorisation tests per role.

[HIGH] Grade Approval Workflow Integrity
  Risk     : Invalid state transitions exposing unreviewed grades.
  Mitigate : Implement a state-machine pattern (BR-10).
             Enforce all transitions at the service layer.
             Block direct database bypass.
             Add workflow-specific integration tests.

[MED]  Payment Gateway Reliability
  Risk     : Failed transactions leaving fee records in an ambiguous state.
  Mitigate : Idempotent payment requests.
             Payment status verification callback.
             Reconciliation background job.
             Transaction records in audit trail (BR-06).

[MED]  File Storage Scaling
  Risk     : Assignment submissions and course materials growing rapidly.
  Mitigate : Per-upload size limits and file-type validation.
             S3-compatible object storage from Phase 2.
             Secure, time-limited download URLs.

[MED]  Scope Creep
  Risk     : 27 future enhancements disrupting the v1.0 roadmap.
  Mitigate : Strict phase gating.
             Change-control process.
             Freeze v1.0 scope; track future features separately.

[LOW]  Analytics Report Generation Load
  Risk     : Large institution-wide reports slowing the UI.
  Mitigate : Generate reports asynchronously via background jobs.
             Return a downloadable link when ready.
             Cache frequently requested analytics.


================================================================================
  5. TESTING STRATEGY
================================================================================

Layer              Scope                                         Tool
-----------------  --------------------------------------------  ----------------
Unit Tests         BR-01–BR-10, service functions, validators    Jest / Vitest
Integration Tests  API endpoints, RBAC, workflow transitions     Supertest + test DB
E2E Tests          Full journeys: Admin, Faculty, Student        Playwright / Cypress
Security Tests     Auth bypass, IDOR, injection, session issues  OWASP checklist
Performance Tests  Dashboard load, exam registration, bulk       k6 / Artillery
                   attendance
UAT                Representative users validate each phase      Staged environment


================================================================================
  6. IMPLEMENTATION RULES FOR DEVELOPMENT
================================================================================

  1. Build and validate one phase fully before starting the next.
  2. Use this document as the master implementation roadmap for NEXORA v1.0.
  3. Implement Admin, Faculty, and Student permissions separately;
     enforce at API and service level — never only on the frontend.
  4. Every business rule (BR-01 to BR-10) must have automated tests.
  5. Every approval workflow must use explicit states and valid transitions (BR-10).
  6. Store audit records for all sensitive administrative and academic actions (BR-09).
  7. Use database migrations for all schema changes; never alter schema directly.
  8. Store uploaded files in object storage — never directly in the database.
  9. Keep all secrets and credentials in environment variables.
 10. Do not implement future enhancements until v1.0 requirements are complete.
 11. Maintain API documentation throughout development.
 12. Add loading, empty, success, and error states to every major UI.
 13. Use responsive layouts for desktop, tablet, and mobile.
 14. Ensure accessibility for core user workflows.
 15. Add monitoring and error tracking before production launch.


================================================================================
  7. SUGGESTED PROJECT STRUCTURE
================================================================================

NEXORA/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   └── lib/
│   └── api/
│       ├── modules/
│       ├── middleware/
│       ├── services/
│       ├── controllers/
│       └── validators/
├── packages/
│   ├── database/
│   ├── types/
│   ├── auth/
│   └── config/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── security/
├── docs/
├── docker-compose.yml
├── package.json
└── README.md


================================================================================
  8. DEFINITION OF DONE
================================================================================

A requirement is considered complete only when ALL of the following are true:

  [ ] Frontend workflow is implemented
  [ ] Backend API is implemented
  [ ] Database model and migration exist
  [ ] RBAC permissions are enforced
  [ ] Validation and error handling are implemented
  [ ] Unit / integration tests pass
  [ ] E2E workflow passes (where applicable)
  [ ] Audit logging implemented for sensitive actions
  [ ] Loading, empty, success, and error states handled in the UI
  [ ] API documentation is updated
  [ ] Code review is completed
  [ ] Feature is deployed to the staging environment


================================================================================
  9. FINAL v1.0 TARGET
================================================================================

Timeline  : 26 weeks
Target    : Production-ready NEXORA College Management Portal

Roles     : Admin · Faculty · Student

Core capabilities delivered in v1.0:
  - Authentication & RBAC
  - User Management
  - Academic Management
  - Courses & Materials
  - Timetable
  - Attendance
  - Assignments & Quizzes
  - Grades & Approval Workflows
  - Examinations
  - Academic Flags
  - Course Proposals
  - Fees & Payments
  - Documents
  - Leave Requests
  - Grievances
  - Notifications
  - Messaging
  - Discussion Boards
  - Compliance Tracking
  - Analytics
  - Reports
  - Global Search
  - Audit Trail

Release milestone: NEXORA v1.0 production launch — end of Week 26.


================================================================================
  10. AGENT / AI DEVELOPMENT INSTRUCTIONS
================================================================================

Use this document as the primary implementation roadmap.

Before writing any code:
  1. Inspect the existing repository structure.
  2. Identify the current stack and installed dependencies.
  3. Preserve all existing working functionality.
  4. Create a clear implementation backlog from the six phases above.
  5. Start with Phase 1.

During development:
  - Implement incrementally and test each feature before moving on.
  - Do not skip: authentication, RBAC, database migrations, validation,
    audit logging, or automated tests.
  - After completing each phase, verify its milestone criteria
    before proceeding to the next phase.

Keep the application:
  - Production-oriented
  - Modular and maintainable
  - Secure (OWASP best practices)
  - Responsive (desktop, tablet, mobile)
  - Accessible for core workflows

Ask for clarification only when a requirement is genuinely ambiguous.
Otherwise, make a reasonable engineering decision and document it.


================================================================================
  NEXORA · Implementation Plan v1.0 · Requirements Phase Complete
  26-Week Build Roadmap · One Portal. Three Roles. Connected Academic Operations.
================================================================================