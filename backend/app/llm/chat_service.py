from app.company.service import get_system_prompt
from app.llm.ollama_client import chat

DEFAULT_IMAGE_PROMPT = "Descreva o que há nessa imagem e responda de forma útil."

# Modelo pequeno (7B) às vezes mistura idioma - reforça no topo do prompt,
# onde o modelo dá mais atenção, em vez de só no rodapé do company/info.md.
LANGUAGE_INSTRUCTION = (
    "Responda SEMPRE em português do Brasil, nunca em espanhol, inglês ou "
    "qualquer outro idioma, mesmo que a pergunta venha em outro idioma.\n\n"
)


async def ask(text: str | None, image_base64: str | None = None) -> str:
    prompt = text or DEFAULT_IMAGE_PROMPT
    system_prompt = LANGUAGE_INSTRUCTION + get_system_prompt()
    return await chat(system_prompt, prompt, image_base64)
