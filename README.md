# Anchor

A proof of concept for an AI-driven coaching conversation: enter a display name,
pick a role and generated role tier, answer 3–10 adaptive questions, and get a verdict with a rationale and a concrete,
encouraging next step — not a graded exam, a check-in aimed at growth.

Main reason for this project is to learn Agentic AI Engineering

- **Backend:** FastAPI + SQLModel + Postgres (`backend/`)
- **Frontend:** React + TypeScript + Vite + Tailwind (`frontend/`)
- **AI provider:** a deterministic mock by default (`backend/app/ai/mock.py`), or the
  real Claude API (`backend/app/ai/anthropic_provider.py`) or OpenAI Responses API
  (`backend/app/ai/openai_provider.py`) — all implement the same interface, injected via a FastAPI dependency (`app.ai.get_ai_provider`), and are
  switched with the `AI_PROVIDER` setting (see step 2).

## Prerequisites

- Docker Desktop (for the Postgres container)
- Python 3.11+
- Node.js 20+

## 1. Start Postgres

From the repository root:

```bash
docker compose up -d
```

This runs `postgres:16` on `localhost:5432` with user/password `postgres/postgres` and
the database `employee_eval`.

## 2. Backend

From `backend/`:

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

The API listens on `http://localhost:8000` (`GET /health` returns `{"status":"ok"}`).
Tables are created automatically on startup. Existing PostgreSQL databases receive
an automatic additive upgrade for profiles, role ladders, session snapshots,
adaptive decisions, and usage records; existing assessment data is preserved. The
retired employee identity table and its now-unused columns are dropped
automatically as part of the same startup migration.

The database URL can be overridden with the `DATABASE_URL` environment variable; it
defaults to `postgresql+psycopg://postgres:postgres@localhost:5432/employee_eval`.

### Using a real AI provider instead of the mock

By default the app uses a free, deterministic mock AI provider - no API key needed.
To use real Claude- or OpenAI-generated questions and evaluations instead:

```bash
cp .env.example .env
```

Then edit `backend/.env` for Claude:

```
ANTHROPIC_API_KEY=sk-ant-...   # from https://console.anthropic.com
AI_PROVIDER=anthropic
```

Or for OpenAI (the default model is `gpt-5.6-terra`):

```
OPENAI_API_KEY=sk-...
AI_PROVIDER=openai
OPENAI_MODEL=gpt-5.6-terra
```

`backend/.env` is gitignored and read automatically on startup - restart `uvicorn`
after editing it. Real API calls cost money per request; leave `AI_PROVIDER=mock` (or
omit the file entirely) to keep using the free mock.

## 3. Frontend

From `frontend/`, in a second terminal:

```bash
npm install
npm run dev
```

The dev server listens on `http://localhost:5173`. It calls the backend at
`http://localhost:8000` by default; override with `VITE_API_BASE_URL`.

## 4. Use the app

Open <http://localhost:5173> and enter a display name to create or reuse a prototype
profile. Its home screen shows completed assessment history. Enter a role, review
its suggested ladder, select the tier whose expectations you want to explore, and
confirm the ladder fits your assessment. AI suggestions are not verified industry
standards or employer-approved frameworks. If the suggestion does not fit, go back
and change the role; importing HR/manager-defined ladders remains future work.
Each session saves its role title, rubric version, selected and next tier names/IDs, and their
expectations as an immutable snapshot, so later ladder changes do not alter its
assessment context.

Assessment prompts restrict role and level references to the saved names. Older
sessions without a saved next-tier name use neutral next-level wording instead of
guessing a title. This is a model instruction, not a guarantee that generated prose
cannot hallucinate; role-ladder quality still requires human review.

The conversation adapts to your answers and completes after 3–10 questions. The
terminal adaptive provider call returns the evaluation directly, with no separate
evaluation request. Results describe how you meet the selected tier and suggest a
concrete next step. This release uses conversational questions only; practical
exercises are not executed.

Display-name reuse is local prototype identity, **not authentication**. People who
enter the same name can reuse the profile. This is not suitable for a multi-user
deployment containing sensitive employee information. Browser storage remembers
the profile; completed history is restored from the API. In-progress conversation
recovery after a reload is not implemented.

Every session requires a resolved profile, role, and selected tier. The earlier
title-only session-creation flow and its separate employee identity have been
removed; there is no prior deployment or external caller to keep compatible with.

Provider setup remains controlled by environment variables as above. Each adaptive
provider operation records its model and input/output token counts in `AIUsage`,
alongside role/session identifiers and a timestamp. Usage records do not contain
prompts or answers. Token counts can support cost measurement with the applicable
provider prices; this project does not claim a measured cents-per-session benchmark.

## Running the tests

### Backend unit/API tests

Postgres must be running. From `backend/`:

```bash
pytest tests/ -v
```

These require a dedicated `employee_eval_test` database (created automatically on
first run using the configured Postgres connection). Tests create and drop its
tables; never point a development server at that database. The dev database is
not reset. Provider tests use the deterministic mock or fake SDK clients, so the
suite does not make paid AI calls.

### End-to-end tests

Playwright drives the real stack. Use a dedicated E2E database and explicitly select
the mock provider. For example, create `anchor_adaptive_e2e` once in Postgres, then
start a task-owned backend on port 18000. These PowerShell commands run from the
repository root and `backend/`, respectively:

```powershell
docker compose exec db createdb -U postgres anchor_adaptive_e2e
```

```powershell
$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/anchor_adaptive_e2e'
$env:AI_PROVIDER='mock'
python -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

In a separate terminal, from `frontend/`:

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:18000'
npm run dev
```

In the test terminal, also from `frontend/`, set `E2E_API_BASE_URL` to the **same**
backend URL as `VITE_API_BASE_URL`. Restart Vite if its URL setting changes.
Neither backend nor frontend is started automatically by Playwright.

```powershell
$env:E2E_API_BASE_URL='http://127.0.0.1:18000'
npx playwright install chromium   # first run only
npm run test:e2e -- --workers=1
npm run build
npm run lint
```

Keep this stack on `AI_PROVIDER=mock`: real-stack tests create profiles and sessions
and must never make paid API calls. The E2E suite adds records to its dedicated
database; it does not reset the user development database. Both API URL settings
default to `http://localhost:8000` if omitted, so set them explicitly for isolation.

If Windows cannot execute the npm/npx shims, the installed entry points are
equivalent: `node node_modules/@playwright/test/cli.js test --workers=1`,
`node node_modules/typescript/bin/tsc -b`,
`node node_modules/vite/bin/vite.js build`, and
`node node_modules/oxlint/bin/oxlint`.
