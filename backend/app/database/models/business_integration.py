from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.business import Business


class BusinessIntegration(Base):
    """Credencial de uma API externa (Google Calendar, Outlook, ou genérica)
    que o negócio cadastra pra dar mais contexto ao LLM. Só guarda a
    credencial por enquanto - a chamada de verdade pra API fica pra depois.
    """

    __tablename__ = "business_integrations"
    __table_args__ = (
        UniqueConstraint(
            "business_id", "name", name="uq_business_integrations_business_id_name"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # "google_calendar" | "outlook_calendar" | "generic"
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # senha ou api_key, criptografado (ver core/security.py encrypt_secret) -
    # nunca volta em texto puro pra fora
    encrypted_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship(back_populates="integrations")
