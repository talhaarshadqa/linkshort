"""SQLite-backed storage. Uses only the standard library."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from .codes import random_code

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    code        TEXT PRIMARY KEY,
    target_url  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT,
    clicks      INTEGER NOT NULL DEFAULT 0,
    last_click  TEXT
);
CREATE INDEX IF NOT EXISTS idx_links_created ON links(created_at);
"""


class AliasTaken(Exception):
    pass


@dataclass
class Link:
    code: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
    clicks: int
    last_click: datetime | None

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class LinkStore:
    def __init__(self, path: str = "linkshort.db") -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_link(row: sqlite3.Row) -> Link:
        return Link(
            code=row["code"],
            target_url=row["target_url"],
            created_at=_parse(row["created_at"]),
            expires_at=_parse(row["expires_at"]),
            clicks=row["clicks"],
            last_click=_parse(row["last_click"]),
        )

    def create(
        self,
        target_url: str,
        *,
        alias: str | None = None,
        expires_at: datetime | None = None,
        max_attempts: int = 5,
    ) -> Link:
        created = _now()
        candidates = [alias] if alias else [random_code() for _ in range(max_attempts)]
        for code in candidates:
            try:
                with self._lock, self._conn:
                    self._conn.execute(
                        "INSERT INTO links (code, target_url, created_at, expires_at) "
                        "VALUES (?, ?, ?, ?)",
                        (
                            code,
                            target_url,
                            created.isoformat(),
                            expires_at.isoformat() if expires_at else None,
                        ),
                    )
                return Link(code, target_url, created, expires_at, 0, None)
            except sqlite3.IntegrityError:
                if alias:
                    raise AliasTaken(alias) from None
        raise RuntimeError("could not generate a unique code")

    def get(self, code: str) -> Link | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
        return self._row_to_link(row) if row else None

    def resolve(self, code: str) -> Link | None:
        """Look up a link for redirecting and record the click atomically."""
        with self._lock, self._conn:
            row = self._conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
            if row is None:
                return None
            link = self._row_to_link(row)
            if link.is_expired:
                return link
            now = _now()
            self._conn.execute(
                "UPDATE links SET clicks = clicks + 1, last_click = ? WHERE code = ?",
                (now.isoformat(), code),
            )
        link.clicks += 1
        link.last_click = now
        return link

    def list(self, *, limit: int = 50, offset: int = 0) -> list[Link]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM links ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._row_to_link(r) for r in rows]

    def delete(self, code: str) -> bool:
        with self._lock, self._conn:
            cur = self._conn.execute("DELETE FROM links WHERE code = ?", (code,))
        return cur.rowcount > 0
