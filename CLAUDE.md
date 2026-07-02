# brain-ad-scorer — project context

Loaded at the start of every Claude Code session in this folder.

## What this project is

Ad-scoring engine: Claude grades ads on 12 expert dimensions, sklearn/XGBoost models
predict overall impact from those dimensions, a local analysis layer (text + image)
runs deterministic checks, and a profitability engine does break-even math.
See README.md for the full architecture.

## Layout

- `app/` — FastAPI backend (`main.py`) + SQLite persistence (`db.py`)
- `analysis/` — deterministic local engines: `text_features.py`, `image_features.py`
- `scripts/` — data labeling and model training
- `prompts/` — the expert persona system prompt and scoring rubric
- `frontend/` — React + Vite app, GitHub-dark style
- `tests/` — pytest suite; Claude calls are mocked, DB is redirected via `SCORER_DB`

## Conventions

- Commit after every completed unit of work, imperative messages, push regularly.
- Never commit `.env`, `venv/`, `node_modules/`, or `data/scorer.db` (see `.gitignore`).
- `ruff check .` and `pytest` must pass before pushing — CI enforces both.
- Cache invalidation is automatic: cache keys include a hash of `prompts/hormozi_brain.md`,
  so editing the prompt is safe.

## Commands

```bash
.\venv\Scripts\activate            # Windows
uvicorn app.main:app --reload      # backend on :8000
pytest                             # 33 tests, no API key needed
python scripts/train_model.py      # retrain + regenerate metrics/charts
cd frontend && npm run dev         # frontend on :5173
```

## Deploy

- Backend → Fly.io (`fly.toml`, Dockerfile)
- Frontend → Netlify (`netlify.toml`), `VITE_API_URL` points at the Fly app
