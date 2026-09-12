from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.business import Business
from app.database.models.business_hours import BusinessHours
from app.database.models.message_log import MessageLog

_WEEKDAY_NAMES = [
    "Segunda",
    "Terça",
    "Quarta",
    "Quinta",
    "Sexta",
    "Sábado",
    "Domingo",
]


async def get_business_by_instance(
    instance_name: str | None,
    session: AsyncSession,
) -> Business | None:
    if not instance_name:
        return None
    return await session.scalar(
        select(Business).where(
            Business.evolution_instance_name == instance_name,
            Business.status == "active",
        ),
    )


async def is_rate_limited(business_id: int, sender: str, session: AsyncSession) -> bool:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=1)
    count = await session.scalar(
        select(func.count())
        .select_from(MessageLog)
        .where(
            MessageLog.business_id == business_id,
            MessageLog.sender == sender,
            MessageLog.direction == "INBOUND",
            MessageLog.created_at >= window_start,
        ),
    )

    return (count or 0) >= settings.rate_limit_per_minute


def _format_hours(hours: list[BusinessHours]) -> str:
    if not hours:
        return "Horário de funcionamento ainda não cadastrado."

    by_weekday = {h.weekday: h for h in hours}
    lines = []
    for weekday, name in enumerate(_WEEKDAY_NAMES):
        entry = by_weekday.get(weekday)
        if (
            entry is None
            or entry.is_closed
            or not entry.opens_at
            or not entry.closes_at
        ):
            lines.append(f"{name}: fechado")
        else:
            lines.append(
                f"{name}: {entry.opens_at.strftime('%Hh%M')} às "
                f"{entry.closes_at.strftime('%Hh%M')}"
            )
    return "\n".join(lines)


async def build_system_prompt(business: Business, session: AsyncSession) -> str:
    parts = [
        f"Você é o assistente de atendimento da {business.name}.",
        "Responda só sobre esse negócio, se não souber a resposta ou for "
        "assunto fora do escopo, diga que vai encaminhar pra um atendente "
        "humano - não invente informação.",
    ]

    if business.business_type == "barbearia":
        hours = await session.scalars(
            select(BusinessHours)
            .where(BusinessHours.business_id == business.id)
            .order_by(BusinessHours.weekday),
        )
        parts.append("\nHorário de funcionamento:\n" + _format_hours(list(hours)))

    return "\n\n".join(parts)
