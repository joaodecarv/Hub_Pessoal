# Personal AI + Finance Hub — Build Plan

> **Status:** Milestone 1 (Banco read-only view) **DONE** — verified end-to-end (incl.
> shared-DB proof + responsive nav), cleaned up, and committed (git `main`, first commit
> `c9c59b5`). Next: **Milestone 2** (RSS + Claude digest engine — needs an Anthropic API key).
> See `CONTEXT.md` for exactly where we stopped and how to resume.
> This is a **learning project** — João writes the code; Claude explains each line.

## What we're building

A personal hub, running on João's own PC, that brings three things into one place:

1. **His finances** — a read-only web view of the existing **Banco** desktop app
   (`/home/joao/Workspaces_VSCODE/Meus_Projetos/Banco`, a Python/PySide6 + SQLite app).
2. **Brazilian financial-market news** — curated RSS feeds summarized by Claude.
3. **AI-industry news** — curated RSS feeds summarized by Claude.

## Locked-in decisions

| Decision | Choice |
|---|---|
| Backend | **Python + FastAPI**, serving JSON (reuses Banco's Python code as a library) |
| Frontend | **React + Vite** (separate app that calls the API) |
| First milestone | **Banco read-only view only** — no API keys, fastest visible result |
| Digest language | Match the source: **AI = English, Finance = Portuguese** |
| Devices | Responsive for **phone + desktop**; **Tailscale** for iPhone access |
| Teaching style | João is new to web dev — explain every line, one small step at a time |

## Architecture (the core idea)

Two separate programs talking over HTTP:

```
  Browser (phone or desktop)
        │
        ▼
  React app  (Vite dev server, port 5173)   ← the "frontend": what you see
        │  fetch() calls, asking for data as JSON
        ▼
  FastAPI app  (Uvicorn, port 8000)          ← the "backend": the data + logic
        │  read-only
        ▼
  Banco's repositories/services  →  banco.db (shared SQLite file)
```

The frontend never touches the database directly — it *asks the backend* and gets back
**JSON**. The desktop `bank.py` is **never modified**; it keeps full read/write access to
the same SQLite file. The hub only ever reads.

## Project structure (target)

```
HubPessoal/
├── PLAN.md                     this file
├── CONTEXT.md                  current status + how to resume
├── backend/
│   ├── .venv/                  Python virtual environment (not committed)
│   ├── requirements.txt        fastapi, uvicorn[standard], python-dotenv
│   │                           (later: feedparser, anthropic)
│   ├── .env                    BANCO_DB_PATH (later: ANTHROPIC_API_KEY) — not committed
│   └── app/
│       ├── __init__.py         empty — marks "app" as an importable package
│       ├── main.py             FastAPI app: creates app, (later) CORS + includes routers
│       ├── config.py           reads .env, holds the Banco DB path + Banco source path
│       └── banco_view/
│           ├── __init__.py
│           ├── adapter.py      adds Banco to sys.path; read-only functions over its repos/services
│           └── router.py       the /api/banco/* endpoints
└── frontend/                   created by Vite (React)
    ├── package.json
    ├── vite.config.js          dev-server proxy: /api → http://localhost:8000
    ├── index.html
    └── src/
        ├── main.jsx            React entry point
        ├── App.jsx             top-level layout + simple page switching
        ├── api.js              tiny fetch helper (one place that knows the API URLs)
        ├── pages/
        │   ├── BancoDashboard.jsx     balances + month summary + per-category spend
        │   └── BancoTransactions.jsx  recent transactions list
        ├── components/         small reusable pieces (Money, HRule, Nav, etc.)
        └── style.css           CSS mirroring Banco's editorial theme
```

### Reused from Banco **unchanged** (imported as a library, never edited)

`banco/repositories.py`, `banco/services.py`, `banco/models.py`, `banco/db.py`,
`banco/config.py`, `banco/ui/format.py` (`money_br`, `date_br`), and `banco/ui/theme.py`
(read only, to copy exact colors into our CSS).

**Do not touch:** `bank.py`, `banco/ui/*` (except reading `format.py`/`theme.py`).

## Milestone 1 — Banco read-only view (current)

Goal: open a browser and see real account balances, this month's income/expense, and recent
transactions, served by our own API.

### Part A — Backend (FastAPI)
1. ✅ Python project + virtual environment (`backend/.venv`).
2. ✅ Install FastAPI + Uvicorn; first app with `GET /api/health`; `/docs` page.
3. ✅ `.env` + `config.py` pointing at the real DB (`~/.local/share/banco/banco.db`);
   temporary `/api/_debug/config` confirms `db_exists: true`.
4. ✅ `banco_view/adapter.py` — adds Banco to `sys.path`, imports its repos/services, opens a
   read-only connection, exposes plain functions: `list_accounts()` (accounts-only — Banco has
   no per-account balance), `month_summary(year, month)`, `recent_transactions(limit, offset)`,
   `categories_with_totals(year, month)`.
5. ✅ `banco_view/router.py` — `APIRouter` with `GET /api/banco/accounts`, `/summary`,
   `/transactions`, `/categories`; included in `main.py`. All four verified in browser/`/docs`.
6. ✅ Enabled `CORSMiddleware` allowing `http://localhost:5173`.

### Part B — Frontend (React + Vite)
7. ✅ Scaffolded with `npm create vite@latest frontend -- --template react`; `npm install` done
   (Node 24 via nvm).
8. ✅ Proxy `/api` → `http://localhost:8000` in `vite.config.js` (`changeOrigin: true`).
9. ✅ `src/api.js` — small `fetch` helper (private `getJSON`; exports `getAccounts`,
   `getSummary`, `getTransactions`, `getCategories`). Lives in `src/`.
10. ✅ `BancoDashboard.jsx` — first component using `useState`/`useEffect` to load
    `/api/banco/summary` (current month); wired into `App.jsx`. Verified in browser — month
    + income/expense/savings/net match `bank.py`.
11. ✅ `Money` component (`components/Money.jsx`, cents → `R$ x.xxx,xx`, optional `className`);
    per-category spend in `BancoDashboard` (`getCategories` + `.map`); `BancoTransactions.jsx`
    page (`getTransactions` + `.map`).
12. ✅ State-based navigation in `App.jsx` (`useState('dashboard')` + buttons + ternary render).
13. ✅ `style.css` mirroring Banco's theme (palette copied from `banco/ui/theme.py`): dark page,
    gradient cards, flexbox ledger rows, green/red money; `@media (max-width:600px)` turns the
    nav into a fixed bottom tab bar. Wired via `main.jsx` import (replaced starter `index.css`).

**Done when:** the React app shows balances/transactions matching `bank.py`; editing a
transaction in the desktop app and refreshing the web page reflects the change.
**✅ DONE (2026-06-17):** verification checklist passed — all four endpoints return real JSON,
dashboard numbers match `bank.py`, shared-DB proof confirmed (edit in `bank.py` → refresh →
change appears), and the nav drops to a bottom tab bar under 600px. Cleanup done: removed
`/api/_debug/config` (and its now-unused `config` import) from `main.py`; added root
`.gitignore` (`.venv/`, `.env`, `node_modules/`, `__pycache__/`, `*.pyc`, `backend/Banco/`);
`git init` + first commit `c9c59b5` on `main`.

## Later milestones (sketched)

- **M2 — RSS + Claude digest engine (backend).** `feedparser` + `anthropic`. `feeds/sources.py`
  (12 curated feeds), `feeds/fetcher.py` (fetch/dedupe/cap), `feeds/digest.py` (prompt with
  caching on static parts, Haiku 4.5, returns Markdown). Cache last digest in SQLite.
  `POST /api/digest/refresh?topic=ai|finance`. AI in English, finance in Portuguese.
  *Requires an Anthropic API key.*
- **M3 — Digest pages (frontend).** `AiNews.jsx`/`FinanceNews.jsx`: show cached digest
  instantly, "Refresh" button calls API and swaps in new summary, render Markdown. Greyscale.
- **M4 — Hub landing + nav polish.** Home page with three entries + last-updated timestamps;
  responsive bottom nav.
- **M5 — iPhone access via Tailscale.** Reach the hub at `https://<host>.<tailnet>.ts.net`.
  For production, build React (`npm run build`) and serve it as static files from FastAPI
  (one server/port). Optional: `systemd --user` auto-start, PWA "Add to Home Screen."

## Token-efficiency tactics (from M2 on)

Prompt caching on static prompt parts; Haiku 4.5 default (~$0.01–0.03/refresh); on-demand
only (no cron); truncate RSS summaries (~300 chars) and cap articles (~40); skip the API
call if nothing new. The Banco view makes **zero** AI calls.

## Verification (Milestone 1)

1. Backend: open `http://localhost:8000/docs`, call each `/api/banco/*` endpoint, confirm
   real JSON.
2. Frontend: `npm run dev` → `http://localhost:5173`, confirm balances/summary/categories/
   transactions render and match `bank.py`.
3. Shared-DB proof: edit a transaction in `bank.py`, refresh the web page, see the change.
4. Responsive: shrink the browser to phone width; confirm layout + bottom nav adapt.

## Out of scope (for now)

Writing to Banco from the web (read-only only); authentication (Tailscale gates access);
scheduled/automatic digest refreshes; push notifications; a settings UI to manage feeds.

---
*Previous server-rendered (Jinja + HTMX) design was superseded on 2026-06-02 when João chose
a FastAPI-JSON + React split and a learning-by-doing approach.*
