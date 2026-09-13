import re
import unicodedata
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.business import Business
from app.database.models.business_hours import BusinessHours
from app.database.models.business_info import BusinessInfo
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


def _slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "negocio"


async def create_evolution_instance(
    business: Business, session: AsyncSession
) -> dict[str, str]:
    instance_name = f"{_slugify(business.name)}-{business.id}"

    async with httpx.AsyncClient(timeout=30) as client:
        create_response = await client.post(
            f"{settings.evolution_api_url}/instance/create",
            headers={"apikey": settings.evolution_api_key},
            json={
                "instanceName": instance_name,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS",
            },
        )
        create_response.raise_for_status()
        qrcode_base64 = create_response.json().get("qrcode", {}).get("base64", "")

        webhook_response = await client.post(
            f"{settings.evolution_api_url}/webhook/set/{instance_name}",
            headers={"apikey": settings.evolution_api_key},
            json={
                "webhook": {
                    "enabled": True,
                    "url": f"{settings.lapzap_webhook_base_url}/api/v1/webhooks/whatsapp",
                    "byEvents": False,
                    "base64": True,
                    "events": ["MESSAGES_UPSERT"],
                }
            },
        )
        webhook_response.raise_for_status()

    # não marca "active" aqui - dono ainda precisa escanear o QR code, e o
    # negócio só passa a responder de verdade depois que o admin aprovar
    # (ver activate em business/router.py)
    business.evolution_instance_name = instance_name
    await session.commit()

    return {"evolution_instance_name": instance_name, "qrcode_base64": qrcode_base64}


async def build_system_prompt(business: Business, session: AsyncSession) -> str:
    parts = [
        f"Você é o assistente de atendimento da {business.name}.",
        (
            "Responda só sobre esse negócio, se não souber a resposta ou for "
            "assunto fora do escopo, diga que vai encaminhar pra um atendente "
            "humano - não invente informação."
        ),
    ]

    if business.business_type == "barbearia":
        hours = await session.scalars(
            select(BusinessHours)
            .where(BusinessHours.business_id == business.id)
            .order_by(BusinessHours.weekday),
        )
        parts.append("\nHorário de funcionamento:\n" + _format_hours(list(hours)))

    info = await session.scalar(
        select(BusinessInfo).where(BusinessInfo.business_id == business.id)
    )
    if info is not None:
        parts.append("\nInformações do negócio:\n" + info.content)

    return "\n\n".join(parts)
