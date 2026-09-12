import httpx

from app.core.config import settings


async def chat(
    system_prompt: str,
    user_text: str,
    image_base64: str | None = None,
) -> str:
    user_message: dict[str, object] = {"role": "user", "content": user_text}

    if image_base64:
        user_message["images"] = [image_base64]

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    user_message,
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
