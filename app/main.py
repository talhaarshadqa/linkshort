"""FastAPI application."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from . import __version__
from .schemas import LinkCreate, LinkOut
from .store import AliasTaken, Link, LinkStore, _now


def create_app(db_path: str | None = None) -> FastAPI:
    db_path = db_path or os.getenv("LINKSHORT_DB", "linkshort.db")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.store = LinkStore(db_path)
        yield
        app.state.store.close()

    app = FastAPI(
        title="linkshort",
        version=__version__,
        description="A small URL shortener with click analytics.",
        lifespan=lifespan,
    )

    def store(request: Request) -> LinkStore:
        return request.app.state.store

    def to_out(request: Request, link: Link) -> LinkOut:
        base = str(request.base_url).rstrip("/")
        return LinkOut(short_url=f"{base}/{link.code}", **link.__dict__)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.post("/api/links", response_model=LinkOut, status_code=status.HTTP_201_CREATED, tags=["links"])
    def create_link(payload: LinkCreate, request: Request) -> LinkOut:
        expires = _now() + timedelta(hours=payload.expires_in_hours) if payload.expires_in_hours else None
        try:
            link = store(request).create(str(payload.url), alias=payload.alias, expires_at=expires)
        except AliasTaken:
            raise HTTPException(status.HTTP_409_CONFLICT, f"alias '{payload.alias}' is already taken")
        return to_out(request, link)

    @app.get("/api/links", response_model=list[LinkOut], tags=["links"])
    def list_links(
        request: Request,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ) -> list[LinkOut]:
        return [to_out(request, link) for link in store(request).list(limit=limit, offset=offset)]

    @app.get("/api/links/{code}", response_model=LinkOut, tags=["links"])
    def get_link(code: str, request: Request) -> LinkOut:
        link = store(request).get(code)
        if link is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")
        return to_out(request, link)

    @app.delete("/api/links/{code}", status_code=status.HTTP_204_NO_CONTENT, tags=["links"])
    def delete_link(code: str, request: Request) -> None:
        if not store(request).delete(code):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")

    @app.get("/{code}", tags=["redirect"], include_in_schema=False)
    def follow(code: str, request: Request) -> RedirectResponse:
        link = store(request).resolve(code)
        if link is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")
        if link.is_expired:
            raise HTTPException(status.HTTP_410_GONE, "link has expired")
        return RedirectResponse(link.target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    return app


app = create_app()
