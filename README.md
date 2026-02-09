# ShinGan

Nano Banana Pro (Gemini 3 Pro Image) 画像生成エージェント

## Features

| Feature | Description |
|---|---|
| **Prompt Catalog** | 20 prompts / 10 categories |
| **Prompt Builder** | Interactive step-by-step prompt construction |
| **Batch Generation** | Category-wide or custom batch processing |
| **Reference Images** | Group-based reference image management (up to 14) |
| **Image Attach** | Dashboard-driven image attachment workflow |
| **Web Dashboard** | Full UI with catalog, builder, batch, references, history |
| **REST API** | 24 endpoints (FastAPI + Swagger docs) |
| **Session Management** | Exponential backoff retry + auto-recovery |

## Quick Start

```bash
pip install -e .

# Dashboard
shingan serve
# → http://localhost:8080

# CLI
shingan list                        # Prompt catalog
shingan show char-pixel-mascot      # Prompt details
shingan build                       # Interactive builder
shingan batch -c character          # Batch generate
shingan gen "A cute robot" -r 4K    # Free prompt
```

## Architecture

```
shingan/
├── agent.py          # Core agent (stub image gen, batch, references)
├── builder.py        # Prompt builder with presets
├── cli.py            # CLI (list/show/gen/batch/build/chat/serve)
├── config.py         # Settings (.env support)
├── server.py         # FastAPI REST API (24 endpoints)
├── session.py        # Session manager with retry
├── prompts/
│   └── catalog.py    # 20 prompts across 10 categories
└── static/
    ├── index.html    # Dashboard
    ├── style.css
    └── app.js
```

## API Endpoints

```
GET  /api/health              GET  /api/prompts
GET  /api/prompts/{id}        GET  /api/categories
POST /api/generate            POST /api/generate/{id}
POST /api/batch               POST /api/batch/category
GET  /api/references          POST /api/references/{group}
DELETE /api/references/{group} POST /api/attach/{result_id}
GET  /api/builder/presets     POST /api/builder/compile
GET  /api/history             GET  /api/history/export
GET  /api/history/{id}        POST /api/session
POST /api/session/chat        GET  /api/session/state
DELETE /api/session           GET  /api/images/{file}
```

## Configuration

Copy `.env.example` to `.env`:

```bash
GOOGLE_API_KEY=your-key-here
SHINGAN_MODEL=gemini-3-pro-image-preview
SHINGAN_RESOLUTION=2K
SHINGAN_PORT=8080
```

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v  # 54 tests
```
