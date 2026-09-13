from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.business_hours import BusinessHours
    from app.database.models.business_info import BusinessInfo
    from app.database.models.business_integration import BusinessIntegration
    from app.database.models.user import User


class Business(Base):
    """Um tenant: 1 negócio = 1 instância WhatsApp (Evolution API) própria.

    Fluxo de criação: cliente preenche form público (nome, tipo, telefone de
    contato, plano, e-mail/senha) -> nasce com status "pending_setup", sem
    instância ligada, já com a conta de login criada e vinculada. Conectar a
    instância WhatsApp de verdade (criar no Evolution API, escanear QR) é
    passo manual do admin - depois disso ele preenche
    `evolution_instance_name` e marca status "active".
    """

    __tablename__ = "businesses"
    __table_args__ = (
        UniqueConstraint(
            "evolution_instance_name", name="uq_businesses_evolution_instance_name"
        ),
        UniqueConstraint(
            "contact_phone_number", name="uq_businesses_contact_phone_number"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # nullable só por causa de negócios criados antes desse fluxo exigir
    # conta - todo cadastro novo já nasce vinculado (ver signup em business/router.py)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # "barbearia" | "loja" | "generico" - define qual dado dinâmico o
    # chatbot usa pra montar o system prompt (ver app/business/service.py)
    business_type: Mapped[str] = mapped_column(String(30), nullable=False)
    contact_phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    plan: Mapped[str] = mapped_column(String(30), nullable=False)
    # "pending_setup" (aguardando admin conectar instância) | "active"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending_setup"
    )
    # "public" (qualquer número recebe resposta) | "private" (só número
    # cadastrado em PhoneNumber.business_id recebe - ver whatsapp/service.py)
    visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, default="public"
    )
    # nulo até o admin conectar a instância manualmente
    evolution_instance_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User | None"] = relationship()
    hours: Mapped[list["BusinessHours"]] = relationship(
        back_populates="business", order_by="BusinessHours.weekday"
    )
    info: Mapped["BusinessInfo | None"] = relationship(
        back_populates="business", uselist=False, cascade="all, delete-orphan"
    )
    integrations: Mapped[list["BusinessIntegration"]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
        order_by="BusinessIntegration.name",
    )
