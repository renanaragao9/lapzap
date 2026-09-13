from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.business import Business


class BusinessInfo(Base):
    """Texto livre em markdown que o próprio negócio preenche - vira contexto
    extra pro LLM (build_system_prompt) além do que já é gerado automático
    (nome, tipo, horário). 1 negócio = 1 registro.
    """

    __tablename__ = "business_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship(back_populates="info")
