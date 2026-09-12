import argparse
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.database.session import async_session_factory, engine

DEFAULT_NAME = "Renan"
DEFAULT_EMAIL = "admin@example.com"
DEFAULT_PASSWORD = "123456"
DEFAULT_PHONE_NUMBERS = ["+5585999999999", "+5585988888888"]


async def seed_user_and_phone_numbers(
    email: str,
    name: str,
    password: str,
    phone_numbers: list[str],
) -> tuple[bool, int]:
    user_created = False
    created_phone_numbers = 0

    async with async_session_factory() as session, session.begin():
        user = await session.scalar(select(User).where(User.email == email))

        if user is None:
            user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                is_active=True,
                is_admin=True,
            )
            session.add(user)
            await session.flush()
            user_created = True

        for phone_number in phone_numbers:
            existing_phone_number = await session.scalar(
                select(PhoneNumber).where(PhoneNumber.phone_number == phone_number)
            )

            if existing_phone_number is None:
                session.add(
                    PhoneNumber(
                        user_id=user.id,
                        phone_number=phone_number,
                        name=name,
                        is_active=True,
                    )
                )
                created_phone_numbers += 1
            elif existing_phone_number.user_id != user.id:
                raise ValueError(
                    f"O telefone {phone_number} já pertence a outro usuário."
                )

    return user_created, created_phone_numbers


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cria um usuário de desenvolvimento e seus números autorizados."
    )
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--phone", action="append")
    return parser.parse_args()


async def run() -> None:
    arguments = parse_arguments()

    try:
        user_created, created_phone_numbers = await seed_user_and_phone_numbers(
            email=arguments.email,
            name=arguments.name,
            password=arguments.password,
            phone_numbers=arguments.phone or DEFAULT_PHONE_NUMBERS,
        )
    finally:
        await engine.dispose()

    user_status = "criado" if user_created else "já existente"
    print(
        f"Usuário {user_status}. Números autorizados criados: {created_phone_numbers}."
    )


if __name__ == "__main__":
    asyncio.run(run())
