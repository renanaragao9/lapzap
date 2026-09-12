from app.company.service import get_system_prompt
from app.llm.ollama_client import chat

DEFAULT_IMAGE_PROMPT = "Descreva o que há nessa imagem e responda de forma útil."

# Modelo pequeno (7B) às vezes mistura idioma - reforça no topo do prompt,
# onde o modelo dá mais atenção, em vez de só no rodapé do company/info.md.
LANGUAGE_INSTRUCTION = (
    "Responda SEMPRE em português do Brasil, nunca em espanhol, inglês ou "
    "qualquer outro idioma, mesmo que a pergunta venha em outro idioma.\n\n"
)


# O system prompt da empresa manda "responda só sobre a empresa, se não
# souber diga que vai encaminhar pra atendente" - isso faz o modelo recusar
# descrever imagem (que não é "sobre a empresa"). Ler imagem é feature própria
# do serviço, não deve herdar essa restrição de escopo.
IMAGE_SYSTEM_PROMPT = LANGUAGE_INSTRUCTION + (
    "Você é o assistente de atendimento do LapZap. Um dos recursos do serviço "
    "é ler imagens e documentos enviados pelo usuário. Descreva o conteúdo da "
    "imagem (texto, objetos, cena) de forma clara e direta - não recuse "
    "descrever a imagem por não ser sobre a empresa, essa é a função aqui."
)


async def ask(text: str | None, image_base64: str | None = None) -> str:
    if image_base64:
        prompt = text or DEFAULT_IMAGE_PROMPT
        return await chat(IMAGE_SYSTEM_PROMPT, prompt, image_base64)

    system_prompt = LANGUAGE_INSTRUCTION + get_system_prompt()
    return await chat(system_prompt, text or "", None)
