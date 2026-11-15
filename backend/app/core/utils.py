"""Small pure helpers shared by services and scripts."""
import re
import unicodedata


def slugify(value: str) -> str:
    """'Bóng đá' -> 'bong-da'. ASCII, lowercase, hyphen separated."""
    value = value.replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def escape_like(value: str) -> str:
    """Escape ``%`` and ``_`` so user input is matched literally (use with ``escape='\\\\'``)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
