# users/validators.py
import re

_ALLOWED_KEY_RE = re.compile(r"^[A-Za-z0-9/_\-.]+$")  # folders, letters, digits, dash, underscore, dot
_ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}

def normalize_key(key: str) -> str:
    key = (key or "").strip()
    # strip any leading slash; S3 keys are not absolute paths
    while key.startswith("/"):
        key = key[1:]
    return key

def validate_user_avatar_key(user_id: int, key: str) -> str:
    key = normalize_key(key)

    # must start with this per-user prefix
    prefix = f"avatars/user_{user_id}/"
    if not key.startswith(prefix):
        raise ValueError(f"Key must start with '{prefix}'")

    # no traversal or directory targets
    if ".." in key:
        raise ValueError("Key must not contain '..'")
    if key.endswith("/"):
        raise ValueError("Key must point to a file, not a directory")

    # allowed characters & length
    if len(key) > 512:
        raise ValueError("Key too long (max 512)")
    if not _ALLOWED_KEY_RE.match(key):
        raise ValueError("Key contains illegal characters")

    # extension check
    from os.path import splitext
    _, ext = splitext(key)
    if ext.lower() not in _ALLOWED_EXTS:
        raise ValueError(f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(_ALLOWED_EXTS))}")

    return key
