import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db, set_tenant_context
from app.config import settings
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedException, BadRequestException, NotFoundException
from app.dependencies.auth import get_current_user
from app.models.platform import User, Tenant, UserToken, LoginAttempt
from app.models.academic import Faculty, Student
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest, UserMeResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Session"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """User Authentication & JWT Issuance with failed attempt tracking."""
    client_ip = request.client.host if request.client else "unknown"

    # Identify tenant if slug is provided or fallback
    tenant = None
    if payload.tenant_slug:
        tenant = db.query(Tenant).filter(Tenant.slug == payload.tenant_slug).first()

    query = db.query(User).filter(User.email == payload.email, User.deleted_at.is_(None))
    if tenant:
        query = query.filter(User.tenant_id == tenant.id)
    user = query.first()

    if not user:
        # Record failed login attempt if tenant known
        if tenant:
            attempt = LoginAttempt(
                tenant_id=tenant.id,
                email=payload.email,
                success=False,
                ip_address=client_ip
            )
            db.add(attempt)
            db.commit()
        raise UnauthorizedException("Invalid email or password")

    # Set tenant context
    set_tenant_context(db, user.tenant_id)

    # Check if locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until}. Please try again later."
        )

    # Verify password
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        attempt = LoginAttempt(
            tenant_id=user.tenant_id,
            user_id=user.id,
            email=user.email,
            success=False,
            ip_address=client_ip
        )
        db.add(attempt)
        db.commit()
        raise UnauthorizedException("Invalid email or password")

    # Success: reset failed count and record attempt
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    attempt = LoginAttempt(
        tenant_id=user.tenant_id,
        user_id=user.id,
        email=user.email,
        success=True,
        ip_address=client_ip
    )
    db.add(attempt)

    # Issue JWT tokens
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id)
    }
    access_token = create_access_token(token_claims)
    refresh_token = create_refresh_token(token_claims)

    # Store refresh token hash in user_tokens
    token_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
    user_token_entry = UserToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        purpose="REFRESH",
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(user_token_entry)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "tenant_id": str(user.tenant_id)
        }
    )


@router.post("/refresh", response_model=Dict[str, Any])
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Token Rotation: verifies refresh token and issues a new access token."""
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("purpose") != "REFRESH":
            raise UnauthorizedException("Invalid token type")
        user_id = uuid.UUID(decoded.get("sub"))
    except Exception:
        raise UnauthorizedException("Invalid or expired refresh token")

    token_hash = hashlib.sha256(payload.refresh_token.encode('utf-8')).hexdigest()
    stored_token = db.query(UserToken).filter(
        UserToken.token_hash == token_hash,
        UserToken.user_id == user_id,
        UserToken.revoked_at.is_(None)
    ).first()

    if not stored_token or stored_token.expires_at < datetime.now(timezone.utc):
        raise UnauthorizedException("Refresh token is invalid, expired, or has been revoked")

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user or user.status != "ACTIVE":
        raise UnauthorizedException("User inactive or deleted")

    # Issue new access token
    new_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id)
    }
    new_access_token = create_access_token(new_claims)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout", response_model=Dict[str, Any])
def logout(payload: LogoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Session Invalidation: Revokes refresh token."""
    if payload.refresh_token:
        token_hash = hashlib.sha256(payload.refresh_token.encode('utf-8')).hexdigest()
        stored_token = db.query(UserToken).filter(
            UserToken.token_hash == token_hash,
            UserToken.user_id == current_user.id
        ).first()
        if stored_token:
            stored_token.revoked_at = datetime.now(timezone.utc)
            db.commit()
    else:
        # Revoke all active tokens for this user
        db.query(UserToken).filter(
            UserToken.user_id == current_user.id,
            UserToken.revoked_at.is_(None)
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()

    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Current Session & Permissions."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    profile_data = {}
    if current_user.role == "FACULTY":
        fac = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if fac:
            profile_data = {
                "faculty_id": str(fac.id),
                "employee_no": fac.employee_no,
                "designation": fac.designation,
                "department_id": str(fac.department_id)
            }
    elif current_user.role == "STUDENT":
        stu = db.query(Student).filter(Student.user_id == current_user.id).first()
        if stu:
            profile_data = {
                "student_id": str(stu.id),
                "roll_no": stu.roll_no,
                "programme_id": str(stu.programme_id),
                "current_term_no": stu.current_term_no,
                "admission_year": stu.admission_year
            }

    # Derive role permissions strictly from PRD Section 2
    permissions = []
    if current_user.role == "ADMIN":
        permissions = [
            "users:manage", "calendar:manage", "departments:manage",
            "fee_structures:manage", "rooms:assign", "timetables:manage",
            "announcements:publish", "approvals:manage", "analytics:view", "compliance:manage"
        ]
    elif current_user.role == "FACULTY":
        permissions = [
            "materials:upload", "attendance:record", "assignments:manage",
            "grades:submit", "academic_flags:raise", "discussions:post",
            "leave:apply", "proposals:create"
        ]
    elif current_user.role == "STUDENT":
        permissions = [
            "courses:register", "timetable:view", "attendance:view",
            "assignments:submit", "grades:view", "fees:pay",
            "exams:register", "documents:request", "grievances:raise"
        ]

    return UserMeResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        avatar_url=current_user.avatar_url,
        status=current_user.status,
        last_login_at=current_user.last_login_at,
        tenant_settings=tenant.settings if tenant else None,
        profile=profile_data,
        permissions=permissions
    )
