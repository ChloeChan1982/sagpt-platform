from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings


ALLOWED_ATTACHMENT_TYPES = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
}


def validate_attachment(filename: str, content_type: str, size_bytes: int) -> None:
    settings = get_settings()
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_ATTACHMENT_TYPES:
        raise ValueError("Unsupported attachment type")
    if content_type not in ALLOWED_ATTACHMENT_TYPES[suffix]:
        raise ValueError("Unsupported attachment type")
    if size_bytes > settings.MAX_ATTACHMENT_BYTES:
        raise ValueError("Attachment is too large")


def storage_name_for(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    return f"{uuid4().hex}{suffix}"


def safe_storage_path(upload_dir: str, stored_name: str) -> Path:
    root = Path(upload_dir).resolve()
    path = (root / stored_name).resolve()
    if root != path and root not in path.parents:
        raise ValueError("Invalid storage path")
    return path
