from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .campaign_model import Campaign
    from .event_model import Event
    from .notification_model import Notification
    from .plot_model import Plot
    from .recommendation_model import Recommendation


class UserRole(str, Enum):
    FARMER = "farmer"
    ADVISOR = "advisor"


class User(Base):
    """User model."""

    __tablename__ = "users"

    # Auth0 fields
    auth0_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    full_name: Mapped[str] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(10), nullable=True)
    auth0_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Application specific fields
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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
