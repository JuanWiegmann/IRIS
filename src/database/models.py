"""
Database Models
===============

SQLAlchemy ORM models for KIM's 3NF schema.

Maps to tables created in scripts/init_db.sql.
"""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import String, DECIMAL, Text, Boolean, Integer, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


# ═══════════════════════════════════════════════════════════
# BASE
# ═══════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ═══════════════════════════════════════════════════════════
# USER PROFILE (Core table)
# ═══════════════════════════════════════════════════════════

class UserProfileModel(Base):
    """User profile (core attributes only - 3NF compliant)."""

    __tablename__ = "user_profile"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en-US")
    format_preference: Mapped[str] = mapped_column(String(50), nullable=False, default="concise")
    confidence: Mapped[float] = mapped_column(
        DECIMAL(3, 2),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0"),
        nullable=False,
        default=0.00
    )
    recent_context: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationships (normalized tables)
    tones: Mapped[List["UserToneModel"]] = relationship(
        "UserToneModel",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    boundaries: Mapped[List["UserBoundaryModel"]] = relationship(
        "UserBoundaryModel",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    projects: Mapped[List["UserProjectModel"]] = relationship(
        "UserProjectModel",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    outputs: Mapped[List["UserOutputModel"]] = relationship(
        "UserOutputModel",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    memory_entries: Mapped[List["MemoryEntryModel"]] = relationship(
        "MemoryEntryModel",
        back_populates="profile",
        cascade="all, delete-orphan"
    )


# ═══════════════════════════════════════════════════════════
# USER TONE (Normalized)
# ═══════════════════════════════════════════════════════════

class UserToneModel(Base):
    """User tone preferences (normalized from profile array)."""

    __tablename__ = "user_tone"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    tone: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationship
    profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="tones")


# ═══════════════════════════════════════════════════════════
# USER BOUNDARY (Normalized)
# ═══════════════════════════════════════════════════════════

class UserBoundaryModel(Base):
    """User boundaries/constraints (normalized from profile dict)."""

    __tablename__ = "user_boundary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    rule: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationship
    profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="boundaries")


# ═══════════════════════════════════════════════════════════
# USER PROJECT (Normalized)
# ═══════════════════════════════════════════════════════════

class UserProjectModel(Base):
    """User current projects (normalized from profile array)."""

    __tablename__ = "user_project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationship
    profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="projects")


# ═══════════════════════════════════════════════════════════
# USER OUTPUT (Segment 3 - ready for implementation)
# ═══════════════════════════════════════════════════════════

class UserOutputModel(Base):
    """User past outputs (emails, documents, code) - Wu et al. 2024."""

    __tablename__ = "user_output"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(String(500), nullable=True)
    output_type: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    output_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=True)

    # Vector embedding (768 dimensions for text-embedding-3-small)
    embedding: Mapped[List[float]] = mapped_column(Vector(768), nullable=True)

    # Relationship
    profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="outputs")


# ═══════════════════════════════════════════════════════════
# MEMORY ENTRY (Multi-tiered memory)
# ═══════════════════════════════════════════════════════════

class MemoryEntryModel(Base):
    """Multi-tiered memory (STM=24h, LTM=permanent) - Westhaeusser 2025."""

    __tablename__ = "memory_entry"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("type IN ('STM', 'summary', 'LTM')"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float] = mapped_column(
        DECIMAL(3, 2),
        CheckConstraint("importance >= 0.0 AND importance <= 1.0"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)

    # Vector embedding
    embedding: Mapped[List[float]] = mapped_column(Vector(768), nullable=True)

    # Relationship
    profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="memory_entries")


# ═══════════════════════════════════════════════════════════
# ONBOARDING TARGET (GATE - Segment 5)
# ═══════════════════════════════════════════════════════════

class OnboardingTargetModel(Base):
    """GATE onboarding targets with barriers - Li et al. ICLR 2025."""

    __tablename__ = "onboarding_target"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False)
    dimension: Mapped[str] = mapped_column(String(100), nullable=False)
    research_basis: Mapped[str] = mapped_column(Text, nullable=False)
    barrier_type: Mapped[str] = mapped_column(String(50), nullable=False)
    barrier_threshold: Mapped[dict] = mapped_column(JSONB, nullable=True)
    satisfied: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(
        DECIMAL(3, 2),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0"),
        default=0.00
    )
    evidence: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    satisfied_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
