import base64

from app.whatsapp.media_storage import MEDIA_DIR, save_image

_PIXEL = base64.b64encode(b"fake-image-bytes").decode()


def test_save_image_sanitizes_path_traversal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.whatsapp.media_storage.MEDIA_DIR", tmp_path / "media")

    relative_path = save_image("../../etc/evil", _PIXEL, "image/jpeg")

    saved_file = tmp_path / relative_path
    assert saved_file.is_relative_to(tmp_path / "media")
    assert saved_file.exists()
    assert ".." not in saved_file.name


def test_save_image_keeps_safe_id() -> None:
    relative_path = save_image("ABC123-normal_id", _PIXEL, "image/png")
    saved_file = MEDIA_DIR.parent / relative_path
    assert saved_file.name == "ABC123-normal_id.png"
    saved_file.unlink()
