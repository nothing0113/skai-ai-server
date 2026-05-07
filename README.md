# skai-ai-server

## 1. What this repo is
Stateless FastAPI AI server dedicated to skAI. Spring backend calls this service over HTTP.

## 2. Architecture
- Spring Server -> HTTP -> `skai-ai-server` -> OpenRouter (default)
- Optional local-only provider: OMLX
- No server-side session/state persistence

## 3. Quick Start
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[test]
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 4. Environment variables
- `LLM_PROVIDER`: `openrouter` (default) or `omlx`
- `LLM_BASE_URL`: default `https://openrouter.ai/api/v1`
- `OPENROUTER_API_KEY` or `LLM_API_KEY`: required for OpenRouter
- `LLM_MODEL`: default `google/gemma-4-26b-it`
- Optional aliases: `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`

## 5. API contract
- `GET /health`
- `GET /v1/models` (compat endpoint)
- `POST /v1/embeddings`
- `POST /v1/llm/chat`
- `POST /v1/grading/score`

Example:
```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/v1/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"안녕"}]}'
```

## 6. Spring integration
- Configure Spring to call this server base URL (for example `http://skai-ai-server:8000` in compose network).
- Keep request/response JSON shape unchanged for grading/chat/embeddings.

## 7. For Claude Code / AI coding agents
- This repo is a dedicated external AI server for skAI.
- Spring calls this server over HTTP.
- Default provider is OpenRouter.
- OMLX is optional and local-test only.
- Do not arbitrarily change API shape.
- Keep server stateless.
- No silent fallback on provider/model errors.
- Keep grading semantics: dense/sparse/keyword/SM-2 structure.

## 8. Non-negotiable contracts
- Preserve endpoints: `/health`, `/v1/embeddings`, `/v1/llm/chat`, `/v1/grading/score`.
- Keep stateless behavior.
- Do not implement silent fallback (fail explicitly with 5xx).
- Keep grading score semantics and evidence fields stable.

## 9. Deployment
- Local build:
```bash
docker build -t skai-ai-server:local .
```
- Local run:
```bash
docker compose up -d --build
```
- CI publish: `.github/workflows/docker-publish.yml` pushes to GHCR on `main`.
