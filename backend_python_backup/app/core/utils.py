"""Small pure helpers shared by services and scripts."""
import re
import secrets
import unicodedata

# No 0/O/1/I: booking codes get read out over the phone and typed by hand.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def slugify(value: str) -> str:
    """'Bóng đá' -> 'bong-da'. ASCII, lowercase, hyphen separated."""
    value = value.replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def escape_like(value: str) -> str:
    """Escape ``%`` and ``_`` so user input is matched literally (use with ``escape='\\\\'``)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def generate_booking_code() -> str:
    """Human-readable booking reference, e.g. ``BK-7QX2M9TD`` (unique index is the safety net)."""
    return "BK-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
