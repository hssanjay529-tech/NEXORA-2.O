NEXORA — College Management Portal

Implementation Plan v1.0

A phased build plan covering Admin, Faculty, and Student roles from authentication through analytics, delivered across six structured phases.

Project Snapshot

Phases: 6

Requirements: 28

Modules: 24

Estimated Duration: ~26 weeks

User Roles: Admin, Faculty, Student

Core Data Entities: 16

Approval Workflows: 5

Business Rules: 10

High-Priority Requirements: 17

Notification Channels: 4

1. Build Phases

Phase 1 — Foundation & Authentication

Weeks 1–3 · 3 weeks

Modules & Requirements

Project Setup: Repository, CI/CD, development/staging/production environments

Authentication System: Login, sessions, RBAC

User Management: ADM-01 — Create/deactivate accounts

Role-Based Access Control: Permission matrix enforcement — BR-01

Database Schema: Model all 16 core entities

Audit Trail: Core action logging — BR-09

Milestone — Week 3

Phase 1 Complete: All three roles can authenticate and log in. RBAC is enforced, the database schema is live, and the audit trail records sensitive operations.

Phase 2 — Academic Core

Weeks 4–9 · 6 weeks

Modules & Requirements

Department Management: ADM-03 — Heads, budgets

Academic Calendar: ADM-02 — Semesters, holidays

Course Management: STU-01 — Register and browse courses

Course Materials: FAC-01 — Upload notes and slides

Timetable: ADM-06, STU-02, FAC-07

Attendance: FAC-02, STU-02, BR-05

Milestone — Week 9

Phase 2 Complete: Core academic operations are functional. Departments, courses, timetable, and attendance are live. Faculty can record attendance and students can view their schedules.

Phase 3 — Assessments & Grading

Weeks 10–14 · 5 weeks

Modules & Requirements

Assignments & Quizzes: FAC-03, STU-03 — Create and submit

Grade Management: FAC-04, STU-04, BR-04

Grade Approval Workflow: Faculty → Admin → Publish — BR-04

Examination Management: STU-06 — Register, hall tickets

Academic Flags: FAC-05 — Admin intervention

Course Proposals: FAC-09, ADM-08 — Workflow

Milestone — Week 14

Phase 3 Complete: Assessments and grade workflows run end-to-end. Faculty create assignments, students submit, grades pass through approval, and results are published to students.

Phase 4 — Finance & Documents

Weeks 15–18 · 4 weeks

Modules & Requirements

Fee Management: ADM-05, STU-05, BR-06

Payment Integration: Online gateway and receipts — BR-06

Document Management: STU-09 — Bonafide and transcripts

Document Approval Workflow: Request → Verify → Generate → Download — BR-08

Leave Request System: FAC-08 — Apply and track status

Grievance Management: STU-08 — Tickets and resolution

Milestone — Week 18

Phase 4 Complete: Fees can be collected and documents issued. Online fee payments are verified, receipts are downloadable, and document requests are processed through admin approval.

Phase 5 — Communication & Notifications

Weeks 19–22 · 4 weeks

Modules & Requirements

Notification System: ADM-07 — Event-driven alerts

Email / SMS / Push: Multi-channel delivery

In-Portal Messaging: FAC-06, STU-10 — Direct messaging

Discussion Boards: FAC-06 — Course threads

Announcement System: ADM-07 — Broadcast to role groups

Compliance Tracker: ADM-09 — Deadlines and documents

Milestone — Week 22

Phase 5 Complete: The communication layer is active. Notifications, in-portal messaging, course discussion boards, and announcements are operational.

Phase 6 — Analytics, QA & Launch

Weeks 23–26 · 4 weeks

Modules & Requirements

Analytics Hub: ADM-04, STU-07 — Dashboards

CGPA Trend Graphs: STU-07 — Performance analytics

Institution Reports: ADM-04 — Enrolment, pass rates, fees

Search & Filtering: Global search across entities

End-to-End Testing: Validate all 28 requirements

Production Launch: Deployment, monitoring, handover

Milestone — Week 26

NEXORA v1.0 Launch: All 28 requirements validated, dashboards populated with real data, and production deployment completed.

2. Deliverables by Phase

Phase

Deliverables

Requirements

Priority

Phase 1

Auth system, user CRUD, RBAC, DB schema, audit trail

ADM-01, BR-01, BR-09

High

Phase 2

Departments, academic calendar, courses, timetable, attendance, materials

ADM-02, ADM-03, ADM-06, FAC-01, FAC-02, STU-01, STU-02

High

Phase 3

Assignments, grading, approval workflows, examinations, flags, proposals

FAC-03–05, FAC-09, ADM-08, STU-03, STU-04, STU-06

High

Phase 4

Fee management, payment gateway, documents, leave requests, grievances

ADM-05, FAC-08, STU-05, STU-08, STU-09

High

Phase 5

Notifications, messaging, discussion boards, compliance tracker

ADM-07, ADM-09, FAC-06, FAC-07, STU-10

Medium

Phase 6

Analytics dashboards, global search, E2E testing, production launch

ADM-04, STU-07

Medium

3. Recommended Tech Stack

Frontend

React / Next.js — UI framework

TypeScript — Type safety

Tailwind CSS — Styling

React Query — Data fetching and caching

Recharts / Chart.js — Analytics

Backend

Node.js + Express or NestJS

REST / GraphQL API

JWT + Sessions

Bull / BullMQ — Job queues

Zod / Joi — Validation

Database & Storage

PostgreSQL — Primary database

Prisma / TypeORM — ORM

Redis — Caching and sessions

S3-compatible object storage — File storage

Versioned database migrations

Infrastructure

Docker + Docker Compose

GitHub Actions — CI/CD

AWS / GCP / Azure — Cloud hosting

SendGrid / Twilio — Email / SMS

Sentry — Error monitoring

4. Key Risks & Mitigations

High Risk — RBAC Permission Leaks

Students or faculty must never access data outside their authorized scope.

Mitigation:

Middleware-enforced permission checks

Service-layer authorization

Integration tests for every protected route

Negative authorization tests

High Risk — Grade Approval Workflow Integrity

Invalid state transitions must not expose unreviewed grades.

Mitigation:

Implement a state-machine pattern

Enforce transitions at the service layer

Prevent direct database bypass

Add workflow integration tests

Medium Risk — Payment Gateway Reliability

Failed transactions may leave fees in an ambiguous state.

Mitigation:

Idempotent payment requests

Payment status verification

Reconciliation background job

Transaction audit records

Medium Risk — File Storage Scaling

Assignment submissions and course materials may grow rapidly.

Mitigation:

Per-upload size limits

File-type validation

S3-compatible object storage from Phase 2

Secure download URLs

Medium Risk — Scope Creep

Future enhancements must not disrupt the v1.0 roadmap.

Mitigation:

Strict phase gating

Change-control process

Freeze v1.0 scope

Track future features separately

Low Risk — Analytics Report Load

Large institution-wide reports may affect UI performance.

Mitigation:

Generate reports asynchronously

Use background jobs

Return downloadable report links

Cache frequently requested analytics

5. Testing Strategy

Test Layer

Scope

Tool / Approach

Unit Tests

BR-01–BR-10, service functions, validators

Jest / Vitest

Integration Tests

API endpoints, RBAC, workflow transitions

Supertest + test DB

E2E Tests

Full journeys for Admin, Faculty, Student

Playwright / Cypress

Security Tests

Auth bypass, IDOR, injection, session fixation

OWASP checklist + manual testing

Performance Tests

Dashboard load, exam registration, bulk attendance

k6 / Artillery

UAT

Representative users validate each phase

Staged environment

6. Implementation Rules for Development

Build and validate one phase before starting the next.

Treat this document as the master implementation roadmap for NEXORA v1.0.

Implement Admin, Faculty, and Student permissions separately and enforce them at API/service level.

Never rely only on frontend route protection for authorization.

Every important business rule must have automated tests.

Every approval workflow must use explicit states and valid transitions.

Store audit records for sensitive administrative and academic actions.

Use migrations for all database schema changes.

Store uploaded files in object storage rather than directly in the database.

Keep secrets and credentials in environment variables.

Do not implement future enhancements until v1.0 requirements are complete.

Maintain API documentation throughout development.

Add loading, empty, success, and error states to every major UI.

Use responsive layouts for desktop, tablet, and mobile.

Ensure accessibility for core user workflows.

Add monitoring and error tracking before production launch.

7. Suggested Project Structure

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

8. Definition of Done

A requirement is considered complete only when:

Frontend workflow is implemented.

Backend API is implemented.

Database model and migration exist.

RBAC permissions are enforced.

Validation and error handling are implemented.

Unit/integration tests pass.

E2E workflow passes where applicable.

Audit logging is implemented for sensitive actions.

Loading, empty, success, and error states are handled.

API documentation is updated.

Code review is completed.

The feature is deployed to the staging environment.

9. Final v1.0 Target

Timeline: 26 weeks

Target: Production-ready NEXORA College Management Portal

Roles:

Admin

Faculty

Student

Core capabilities:

Authentication & RBAC

User management

Academic management

Courses & materials

Timetable

Attendance

Assignments & quizzes

Grades & approval workflows

Examinations

Academic flags

Course proposals

Fees & payments

Documents

Leave requests

Grievances

Notifications

Messaging

Discussion boards

Compliance tracking

Analytics

Reports

Global search

Audit trail

Release milestone: NEXORA v1.0 production launch at the end of Week 26.

Antigravity Development Instruction

Use this document as the primary implementation roadmap.

Before writing code:

Inspect the existing repository.

Identify the current stack and installed dependencies.

Preserve existing working functionality.

Create a clear implementation backlog from the six phases.

Start with Phase 1.

Implement incrementally and test each feature.

Do not skip authentication, RBAC, database migrations, validation, audit logging, or automated tests.

After completing each phase, verify its milestone criteria before proceeding.

Keep the application production-oriented, modular, secure, responsive, and maintainable.

Ask for clarification only when a requirement is genuinely ambiguous; otherwise make a reasonable engineering decision and document it.

NEXORA · Implementation Plan v1.0 · Requirements Phase Complete · 26-week build roadmap