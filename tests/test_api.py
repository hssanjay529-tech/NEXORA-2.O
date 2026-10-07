import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.core.security import create_access_token, verify_password, get_password_hash
from app.dependencies.auth import get_current_user, get_current_admin, get_current_faculty, get_current_student
from app.models.platform import User, Tenant
from app.models.academic import Department, Faculty, Programme, Student, CourseOffering, Course, Term, AcademicYear, Room
from app.models.workflow import GrievanceTicket


def test_health_check(client: TestClient):
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_root_endpoint(client: TestClient):
    """Verify root endpoint metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "NEXORA" in data["project"]
    assert data["api_v1"] == "/api/v1"


def test_openapi_schema_loaded(client: TestClient):
    """Verify OpenAPI documentation and complete paths registration."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    # Verify core routes from spec
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/admin/users" in paths
    assert "/api/v1/admin/departments" in paths
    assert "/api/v1/admin/academic-years" in paths
    assert "/api/v1/admin/analytics/dashboard" in paths
    assert "/api/v1/faculty/course-materials" in paths
    assert "/api/v1/faculty/attendance/batch-record" in paths
    assert "/api/v1/faculty/assignments" in paths
    assert "/api/v1/student/courses/available" in paths
    assert "/api/v1/student/timetable" in paths
    assert "/api/v1/student/fees/bills" in paths
    assert "/api/v1/files/upload" in paths
    assert "/api/v1/notifications" in paths
    assert "/api/v1/background-jobs/{job_id}" in paths
    assert len(paths) >= 70


def test_password_hashing():
    """Verify password hashing and verification logic."""
    raw = "SecurePassword123!"
    hashed = get_password_hash(raw)
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_unauthorized_endpoints(client: TestClient):
    """Verify secured endpoints reject unauthenticated requests with standard error schema."""
    endpoints = [
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/faculty/timetable/my-schedule"),
        ("GET", "/api/v1/student/timetable"),
        ("GET", "/api/v1/notifications")
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        assert res.status_code == 401
        data = res.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"


def test_validation_error_format(client: TestClient):
    """Verify RequestValidationError produces unified schema."""
    response = client.post("/api/v1/auth/login", json={"email": "invalid-email-format"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_role_authorization_admin(client: TestClient, override_db):
    """Verify Admin routes execute properly with authenticated admin."""
    tenant = Tenant(
        id=uuid.uuid4(),
        slug="test-college",
        name="Test College of Technology",
        status="ACTIVE",
        settings={}
    )
    override_db.add(tenant)
    override_db.flush()

    mock_admin = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="admin@test.edu",
        first_name="Admin",
        last_name="User",
        role="ADMIN",
        status="ACTIVE",
        password_hash="dummy"
    )
    override_db.add(mock_admin)
    override_db.commit()

    fastapi_app.dependency_overrides[get_current_admin] = lambda: mock_admin
    try:
        response = client.get("/api/v1/admin/rooms")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        fastapi_app.dependency_overrides.pop(get_current_admin, None)


def test_faculty_schedule_route(client: TestClient, override_db):
    """Verify Faculty schedule route executes with authenticated faculty."""
    tenant = Tenant(
        id=uuid.uuid4(),
        slug="test-college-fac",
        name="Faculty College",
        status="ACTIVE",
        settings={}
    )
    override_db.add(tenant)
    override_db.flush()

    user_fac = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="fac@test.edu",
        first_name="Prof",
        last_name="Faculty",
        role="FACULTY",
        status="ACTIVE",
        password_hash="dummy"
    )
    override_db.add(user_fac)
    override_db.flush()

    dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Computer Science",
        code="CS"
    )
    override_db.add(dept)
    override_db.flush()

    profile_fac = Faculty(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user_fac.id,
        department_id=dept.id,
        employee_no="EMP-001",
        designation="Assistant Professor"
    )
    override_db.add(profile_fac)
    override_db.commit()

    fastapi_app.dependency_overrides[get_current_faculty] = lambda: user_fac
    try:
        response = client.get("/api/v1/faculty/timetable/my-schedule")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        fastapi_app.dependency_overrides.pop(get_current_faculty, None)


def test_student_grievance_workflow(client: TestClient, override_db):
    """Verify Student grievance ticket creation and listing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        slug="test-college-stu",
        name="Student College",
        status="ACTIVE",
        settings={}
    )
    override_db.add(tenant)
    override_db.flush()

    user_stu = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="stu@test.edu",
        first_name="Student",
        last_name="One",
        role="STUDENT",
        status="ACTIVE",
        password_hash="dummy"
    )
    override_db.add(user_stu)
    override_db.flush()

    dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Engineering",
        code="ENG"
    )
    override_db.add(dept)
    override_db.flush()

    prog = Programme(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        department_id=dept.id,
        name="BTech",
        code="BTECH",
        degree_level="UNDERGRADUATE"
    )
    override_db.add(prog)
    override_db.flush()

    profile_stu = Student(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user_stu.id,
        programme_id=prog.id,
        roll_no="R-001",
        admission_year=2024
    )
    override_db.add(profile_stu)
    override_db.commit()

    fastapi_app.dependency_overrides[get_current_student] = lambda: user_stu
    try:
        post_res = client.post("/api/v1/student/grievances", json={
            "category": "FACILITY",
            "title": "Lab AC malfunction",
            "description": "The air conditioning in Lab 204 is not working.",
            "priority": "HIGH"
        })
        assert post_res.status_code == 201
        data = post_res.json()
        assert data["title"] == "Lab AC malfunction"
        assert data["status"] == "OPEN"

        get_res = client.get("/api/v1/student/grievances")
        assert get_res.status_code == 200
        assert len(get_res.json()) >= 1
    finally:
        fastapi_app.dependency_overrides.pop(get_current_student, None)


def test_file_upload_descriptor(client: TestClient, override_db):
    """Verify direct cloud upload descriptor creation."""
    tenant = Tenant(
        id=uuid.uuid4(),
        slug="test-college-upload",
        name="Test College",
        status="ACTIVE",
        settings={}
    )
    override_db.add(tenant)
    override_db.flush()

    mock_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="test@user.edu",
        first_name="Test",
        last_name="User",
        role="STUDENT",
        status="ACTIVE",
        password_hash="dummy"
    )
    override_db.add(mock_user)
    override_db.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        response = client.post("/api/v1/files/upload", json={
            "filename": "assignment_report.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1048576,
            "kind": "SUBMISSION"
        })
        assert response.status_code == 201
        data = response.json()
        assert "storage_key" in data
        assert "upload_url" in data
        assert "file_id" in data
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)
