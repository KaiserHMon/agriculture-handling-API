from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .campaign import Campaign, Plot
    from .user import User


class Event(Base):
    """Event model for tracking agricultural activities."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[datetime] = mapped_column(DateTime)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plot_id: Mapped[int] = mapped_column(ForeignKey("plots.id"))
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))

    # Relationships
    plot: Mapped["Plot"] = relationship("Plot", back_populates="events")
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="events")
    created_by: Mapped["User"] = relationship("User", back_populates="events")

    # Constraints
    __table_args__ = (
        CheckConstraint("event_date >= CURRENT_TIMESTAMP", name="check_event_date_future"),
    )
