import base64
import re
from pathlib import Path

MEDIA_DIR = Path(__file__).parent.parent.parent / "media"

_EXTENSION_BY_MIMETYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def save_image(
    external_message_id: str,
    image_base64: str,
    mimetype: str | None = None,
) -> str:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    extension = _EXTENSION_BY_MIMETYPE.get(mimetype or "", "jpg")
    safe_id = _UNSAFE_FILENAME_CHARS.sub("_", external_message_id) or "unknown"
    path = MEDIA_DIR / f"{safe_id}.{extension}"
    path.write_bytes(base64.b64decode(image_base64))
    return str(path.relative_to(MEDIA_DIR.parent))
