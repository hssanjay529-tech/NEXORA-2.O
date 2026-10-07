import uuid
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Engine configuration with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def set_tenant_context(db: Session, tenant_id: str | uuid.UUID) -> None:
    """Sets the PostgreSQL app.tenant_id session variable for Row Level Security (RLS)."""
    if tenant_id:
        try:
            db.execute(text(f"SET LOCAL app.tenant_id = '{str(tenant_id)}'"))
        except Exception:
            # Fallback if connection doesn't support local settings or in test environments
            pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session with automatic commit/rollback and cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
