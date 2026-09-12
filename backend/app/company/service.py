from functools import lru_cache
from pathlib import Path

INFO_FILE = Path(__file__).parent / "info.md"


@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """Info fixa da empresa, usada como system prompt do chatbot.

    ponytail: arquivo estático em vez de tabela/RAG — só migra pra isso se a
    base de conhecimento crescer (múltiplos documentos, catálogo grande).
    """
    return INFO_FILE.read_text(encoding="utf-8")
