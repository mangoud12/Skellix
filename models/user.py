# models/user.py
# ─────────────────────────────────────────────────────────────────────────────
# User model — MVP uses session-based identity (UUID), not full auth.
# A "user" is created automatically when a new assessment session begins.
# The session_id is stored in localStorage on the frontend (Adam's side).
# ─────────────────────────────────────────────────────────────────────────────

from uuid import uuid4
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)

    # session_id is the public-facing identifier — a UUID4 string.
    # This is what the frontend stores and sends with every request.
    # Example: "550e8400-e29b-41d4-a716-446655440000"
    # Retained for compatibility with existing anonymous assessment records.
    session_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid4()))

    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Timestamps — server-generated, not client-provided
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    assessments = relationship(
        "Assessment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}'>"
