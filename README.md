# 🔗 linkshort

[![CI](https://github.com/talhaarshadqa/linkshort/actions/workflows/ci.yml/badge.svg)](https://github.com/talhaarshadqa/linkshort/actions)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)

A URL shortener REST API with click analytics, custom aliases and expiring links.
Built with **FastAPI** and **SQLite**, fully tested, and ready to run in Docker.

## ✨ Features

- `POST` a long URL, get back a short one
- **Custom aliases** like `/promo-2026`, with conflict detection (409)
- **Expiring links**: expired links return `410 Gone`
- **Click analytics**: total clicks and last-click time per link
- Secure random **base62 codes** (`secrets` module) with automatic retry on collision
- Atomic, thread-safe click counting
- Input validation with **Pydantic v2**
- Interactive API docs at `/docs` (Swagger) and `/redoc`
- **Dockerfile**, plus CI on GitHub Actions (tests, lint, Docker build)

## 🚀 Quick start

```bash
git clone https://github.com/talhaarshadqa/linkshort.git
cd linkshort
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs to try the API.

### With Docker

```bash
docker build -t linkshort .
docker run -p 8000:8000 -v linkshort-data:/data linkshort
```

## 📡 API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/links` | Create a short link |
| `GET` | `/api/links` | List links (`?limit=&offset=`) |
| `GET` | `/api/links/{code}` | Link details and click stats |
| `DELETE` | `/api/links/{code}` | Delete a link |
| `GET` | `/{code}` | Redirect to the target URL (307) |
| `GET` | `/health` | Health check |

### Example

```bash
curl -X POST localhost:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/talhaarshadqa", "alias": "talha", "expires_in_hours": 72}'
```

```json
{
  "code": "talha",
  "short_url": "http://localhost:8000/talha",
  "target_url": "https://github.com/talhaarshadqa",
  "created_at": "2026-11-16T19:10:00+00:00",
  "expires_at": "2026-11-19T19:10:00+00:00",
  "clicks": 0,
  "last_click": null
}
```

## 🏗️ Project structure

```
app/
├── main.py      # FastAPI app factory and routes
├── schemas.py   # Pydantic request/response models
├── store.py     # SQLite storage layer
└── codes.py     # short-code generation and alias rules
tests/
├── test_store.py  # storage and validation unit tests
└── test_api.py    # end-to-end API tests
```

The storage layer is kept separate from the web layer, so it can be tested on its own
and swapped for PostgreSQL later without touching the routes.

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=app
```

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `LINKSHORT_DB` | `linkshort.db` | Path to the SQLite database file |

## 📄 License

MIT
