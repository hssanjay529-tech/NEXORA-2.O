# NEXORA Database Initialization & Seed Data

This directory contains the database schema initialization and realistic dummy seed scripts conforming to the **57-table multi-tenant architecture** defined in `database_architecture.md`.

---

## 📁 Files

- [`01_init_schema.sql`](file:///c:/Users/DELL/OneDrive/Desktop/NEXORA/db/01_init_schema.sql) — DDL script creating extensions (`uuid-ossp`, `pgcrypto`, `citext`) and all 57 tables (2 global + 55 tenant-scoped) with composite foreign keys, indexes, and constraints.
- [`02_seed_data.sql`](file:///c:/Users/DELL/OneDrive/Desktop/NEXORA/db/02_seed_data.sql) — Comprehensive seed script populating realistic academic data, RBAC personas, courses, offerings, attendance, grades, finance, exams, workflows, and communication records.

---

## 🚀 How to Run / Reset

From your project root in PowerShell:

```powershell
# 1. Apply Schema
Get-Content db/01_init_schema.sql -Raw | docker exec -i nexora_db psql -U nexora_admin -d nexora

# 2. Seed Dummy Data
Get-Content db/02_seed_data.sql -Raw | docker exec -i nexora_db psql -U nexora_admin -d nexora
```

---

## 👥 Seeded Test Credentials

All accounts are pre-configured with the default password: **`Password123!`**

### 1. Platform Operator
| Role | Email | Password |
| :--- | :--- | :--- |
| **Superadmin** | `superadmin@nexoracloud.com` | `Password123!` |

### 2. Tenant: Apex Institute of Technology & Management (`apex-institute`)
| Role | Name | Email | Details |
| :--- | :--- | :--- | :--- |
| **Admin** | Dr. Rajesh Sharma | `admin@apex.edu` | System Administrator |
| **Faculty (HOD)** | Dr. Aris Thorne | `hod.cse@apex.edu` | HOD & Professor, CSE (`FAC-CSE-001`) |
| **Faculty** | Dr. Priya Nair | `prof.priya@apex.edu` | Associate Professor, CSE (`FAC-CSE-002`) |
| **Faculty** | Prof. Vikram Malhotra | `prof.vikram@apex.edu` | Assistant Professor, ECE (`FAC-ECE-001`) |
| **Student** | Aarav Patel | `student.aarav@apex.edu` | B.Tech CSE, Term 5 (`2024CSE001`) |
| **Student** | Ananya Iyer | `student.ananya@apex.edu` | B.Tech CSE, Term 5 (`2024CSE002`) |
| **Student** | Rohan Gupta | `student.rohan@apex.edu` | B.Tech CSE, Term 5 (`2024CSE003`) |
| **Student** | Sneha Verma | `student.sneha@apex.edu` | B.Tech ECE, Term 5 (`2024ECE001`) |
