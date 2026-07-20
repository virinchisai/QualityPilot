"""SQLAlchemy engine, sessions, and shared persistence models."""

from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from qualitypilot.config import get_settings


class Base(DeclarativeBase):
    pass


def utc_now_naive() -> datetime:
    """Return naive UTC for database portability with the MVP schema."""

    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="user")
    display_name: Mapped[str] = mapped_column(String(100), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    jti_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    family_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    replaced_by_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


class TestExecution(Base):
    __tablename__ = "test_executions"
    id: Mapped[int] = mapped_column(primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    test_id: Mapped[str] = mapped_column(String(100), index=True)
    commit_sha: Mapped[str] = mapped_column(String(64), default="local")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)
    status: Mapped[str] = mapped_column(String(20))
    duration_seconds: Mapped[float] = mapped_column(Float, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str] = mapped_column(String(50), default="local")
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    test_data_version: Mapped[str] = mapped_column(String(50), default="v1")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)


class DefectRecord(Base):
    __tablename__ = "defect_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    defect_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    report_json: Mapped[dict] = mapped_column(JSON)
    markdown_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)


def build_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    kwargs = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=kwargs)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
