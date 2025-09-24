from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .campaign import Campaign
    from .event import Event
    from .notification import Notification
    from .plot import Plot
    from .recommendation import Recommendation


class UserRole(str, Enum):
    FARMER = "farmer"
    ADVISOR = "advisor"
    ADMIN = "admin"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    campaigns: Mapped[list["Campaign"]] = relationship("Campaign", back_populates="user")
    plots: Mapped[list["Plot"]] = relationship("Plot", back_populates="user")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="advisor", foreign_keys="Recommendation.advisor_id"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user"
    )
    events: Mapped[list["Event"]] = relationship("Event", back_populates="created_by")
