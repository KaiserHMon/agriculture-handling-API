from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .campaign_model import Campaign
    from .event_model import Event
    from .recommendation_model import Recommendation
    from .user_model import User


class Plot(Base):
    """Plot model for managing land parcels."""

    __tablename__ = "plots"

    name: Mapped[str] = mapped_column(String(255))
    area: Mapped[float] = mapped_column(Float)  # hectares
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="plots")
    user: Mapped["User"] = relationship("User", back_populates="plots")
    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="plot", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="plot", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (CheckConstraint("area > 0", name="check_positive_area"),)
