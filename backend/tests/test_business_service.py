import asyncio
from datetime import time

from conftest import create_business, session_factory

from app.business.service import (
    build_system_prompt,
    get_business_by_instance,
    is_rate_limited,
)
from app.database.models.business_hours import BusinessHours
from app.database.models.message_log import MessageLog


def test_get_business_by_instance_ignores_pending_setup() -> None:
    async def scenario() -> None:
        await create_business(
            evolution_instance_name="pending-biz", status="pending_setup"
        )

        async with session_factory() as session:
            found = await get_business_by_instance("pending-biz", session)
            assert found is None

    asyncio.run(scenario())


def test_get_business_by_instance_finds_active() -> None:
    async def scenario() -> None:
        business = await create_business(
            evolution_instance_name="active-biz", status="active"
        )

        async with session_factory() as session:
            found = await get_business_by_instance("active-biz", session)
            assert found is not None
            assert found.id == business.id

    asyncio.run(scenario())


def test_get_business_by_instance_returns_none_for_empty_name() -> None:
    async def scenario() -> None:
        async with session_factory() as session:
            assert await get_business_by_instance(None, session) is None
            assert await get_business_by_instance("", session) is None

    asyncio.run(scenario())


def test_build_system_prompt_includes_hours_for_barbearia() -> None:
    async def scenario() -> None:
        business = await create_business(
            evolution_instance_name="barbearia-biz",
            name="Barbearia Teste",
            business_type="barbearia",
        )

        async with session_factory() as session:
            session.add(
                BusinessHours(
                    business_id=business.id,
                    weekday=5,  # sábado
                    opens_at=time(9, 0),
                    closes_at=time(13, 0),
                    is_closed=False,
                )
            )
            session.add(
                BusinessHours(
                    business_id=business.id,
                    weekday=6,  # domingo
                    is_closed=True,
                )
            )
            await session.commit()

            prompt = await build_system_prompt(business, session)

        assert "Barbearia Teste" in prompt
        assert "Sábado: 09h00 às 13h00" in prompt
        assert "Domingo: fechado" in prompt

    asyncio.run(scenario())


def test_build_system_prompt_generico_has_no_hours_section() -> None:
    async def scenario() -> None:
        business = await create_business(
            evolution_instance_name="loja-biz",
            name="Loja Teste",
            business_type="loja",
        )

        async with session_factory() as session:
            prompt = await build_system_prompt(business, session)

        assert "Loja Teste" in prompt
        assert "Horário de funcionamento" not in prompt

    asyncio.run(scenario())


def test_is_rate_limited_false_under_threshold() -> None:
    async def scenario() -> None:
        business = await create_business(evolution_instance_name="rl-biz-1")

        async with session_factory() as session:
            assert await is_rate_limited(business.id, "5585999999999", session) is False

    asyncio.run(scenario())


def test_is_rate_limited_true_over_threshold() -> None:
    async def scenario() -> None:
        business = await create_business(evolution_instance_name="rl-biz-2")

        async with session_factory() as session:
            for i in range(10):  # RATE_LIMIT_PER_MINUTE=10 no .env de teste
                session.add(
                    MessageLog(
                        business_id=business.id,
                        sender="5585999999999",
                        external_message_id=f"seed-{i}",
                        message_type="TEXT",
                        direction="INBOUND",
                        payload={},
                        processed=True,
                        blocked=False,
                    )
                )
            await session.commit()

            assert await is_rate_limited(business.id, "5585999999999", session) is True
            # outro sender no mesmo negócio não é afetado
            assert await is_rate_limited(business.id, "5585988888888", session) is False

    asyncio.run(scenario())
