from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .campaign_model import Plot
    from .user_model import User


class Recommendation(Base):
    """Recommendation model for advisor suggestions."""

    __tablename__ = "recommendations"

    content: Mapped[str] = mapped_column(Text)
    plot_id: Mapped[int] = mapped_column(ForeignKey("plots.id"))
    advisor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    plot: Mapped["Plot"] = relationship("Plot", back_populates="recommendations")
    advisor: Mapped["User"] = relationship(
        "User", back_populates="recommendations", foreign_keys=[advisor_id]
    )
