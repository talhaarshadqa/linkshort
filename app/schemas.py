"""Request and response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from .codes import is_valid_alias


class LinkCreate(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, description="Optional custom short code")
    expires_in_hours: int | None = Field(default=None, ge=1, le=24 * 365)

    @field_validator("alias")
    @classmethod
    def check_alias(cls, v: str | None) -> str | None:
        if v is not None and not is_valid_alias(v):
            raise ValueError("alias must be 3-32 chars of letters, digits, '-' or '_'")
        return v


class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
    clicks: int
    last_click: datetime | None
