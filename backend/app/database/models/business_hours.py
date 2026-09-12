from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.business import Business


class BusinessHours(Base):
    """Horário de funcionamento por dia da semana - dado dinâmico do
    vertical "barbearia" (agenda/horário), consultado na hora de responder.
    """

    __tablename__ = "business_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    weekday: Mapped[int] = mapped_column(nullable=False)  # 0=segunda .. 6=domingo
    opens_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    closes_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    business: Mapped["Business"] = relationship(back_populates="hours")
