import base64
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()

# credenciais de integração (senha/api_key) precisam voltar em texto puro pra
# uso futuro (chamar a API externa), então é criptografia reversível, não
# hash - chave derivada do jwt_secret_key que já existe, sem novo env var.
_fernet = Fernet(
    base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret_key.encode()).digest())
)


def encrypt_secret(plain: str) -> str:
    return _fernet.encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
