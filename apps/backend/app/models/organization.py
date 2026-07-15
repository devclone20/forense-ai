import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    number_format: Mapped[str] = mapped_column(
        String(100), nullable=False, default="FOR-{YYYY}-{NNNNN}"
    )
    number_counter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    invite_expiry_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("7"))

    users: Mapped[list["User"]] = relationship(back_populates="organization")  # type: ignore[name-defined]
    cases: Mapped[list["Case"]] = relationship(back_populates="organization")  # type: ignore[name-defined]
