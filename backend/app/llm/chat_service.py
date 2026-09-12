from app.company.service import get_system_prompt
from app.llm.ollama_client import chat

DEFAULT_IMAGE_PROMPT = "Descreva o que há nessa imagem e responda de forma útil."


async def ask(text: str | None, image_base64: str | None = None) -> str:
    prompt = text or DEFAULT_IMAGE_PROMPT
    return await chat(get_system_prompt(), prompt, image_base64)
