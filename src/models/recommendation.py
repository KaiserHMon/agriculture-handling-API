from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .campaign import Plot
    from .user import User


class Recommendation(Base):
    """Recommendation model for advisor suggestions."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    plot_id: Mapped[int] = mapped_column(ForeignKey("plots.id"))
    advisor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    plot: Mapped["Plot"] = relationship("Plot", back_populates="recommendations")
    advisor: Mapped["User"] = relationship(
        "User", back_populates="recommendations", foreign_keys=[advisor_id]
    )
