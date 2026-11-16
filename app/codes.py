"""Short-code generation."""

from __future__ import annotations

import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # base62
RESERVED = {"api", "docs", "redoc", "health", "openapi.json", "static"}


def random_code(length: int = 7) -> str:
    """Return a cryptographically random base62 code.

    62**7 is about 3.5 trillion combinations, so collisions are rare,
    and the store retries if one happens.
    """
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def is_valid_alias(alias: str) -> bool:
    allowed = set(ALPHABET + "-_")
    return 3 <= len(alias) <= 32 and set(alias) <= allowed and alias.lower() not in RESERVED
