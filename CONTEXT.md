# CONTEXT — Personal AI + Finance Hub

> A running notebook of *what this project is, how it works, and exactly where we stopped*,
> so we (João + Claude) can pick up cleanly in a later session.
> See `PLAN.md` for the full roadmap.

---

## What this project is

A personal **hub website** that runs on João's own PC and gathers three things:

1. **My finances** — a read-only web view of the existing **Banco** desktop app
   (`/home/joao/Workspaces_VSCODE/Meus_Projetos/Banco`).
2. **Brazilian financial-market news** — RSS feeds summarized by Claude (later).
3. **AI-industry news** — RSS feeds summarized by Claude (later).

**This is a learning project.** João is new to web development. The working style is:
Claude explains each line and concept; **João types the code himself** and runs it, one
small runnable step at a time. Don't dump whole files to generate — teach and let João build.

## How it works (architecture)

Two separate programs that talk over HTTP:

```
Browser ──► React app (Vite, port 5173) ──fetch JSON──► FastAPI (Uvicorn, port 8000)
                                                              │ read-only
                                                              ▼
                                              Banco's Python repos/services
                                                              │
                                                              ▼
                                              ~/.local/share/banco/banco.db
                                              (the desktop app's real DB)
```

- **Backend** (`backend/`): Python + FastAPI. Imports Banco's own modules as a library to
  read finance data and returns it as **JSON**. Never writes to the DB.
- **Frontend** (`frontend/`, not created yet): React + Vite. Calls the backend's `/api/*`
  endpoints and renders the data. This is "what you see."
- The desktop `bank.py` is **never modified** and keeps full read/write access to the same
  SQLite file. The hub only reads.

## Tech stack

- Backend: **Python 3.12**, **FastAPI**, **Uvicorn**, **python-dotenv**.
- Frontend: **React + Vite** (plain JS, `.jsx`), **Node 24** via **nvm** (`~/.nvm`, no venv).
- Data: shared **SQLite** at `~/.local/share/banco/banco.db`.
- Phone access (later): **Tailscale**.

---

## ✅ Where we are right now (as of 2026-06-20)

**UI overhaul + M3 + M4 are DONE (uncommitted).** The hub now has a fully restyled
(Claude-style) React frontend and two new tested backend endpoints. See `PRD.md` for the spec
that drove this work, and the "2026-06-20 UI overhaul" section below for the file-by-file detail.

**Final theme = "Midnight Sepia" (warm dark), chosen for low-light early-morning/late-night use.**
We started from the PRD's light "warm paper" palette, then João asked for a dark, low-eye-strain
theme that doesn't look "AI-made" (no purple/neon/gradients). The shipped palette lives in
`frontend/src/style.css` `:root` (warm near-black `--bg:#211E1A`, card `#2A2621`, text `#EAE2D4`,
muted clay accent `#C5704A`, muted money colors) with the sidebar a darker `#1B1815`; chart
colors mirror it in `frontend/src/chartTheme.js`. To revisit: a day/night auto-switch (light
"warm paper" by day, this dark theme at night) was offered and is still on the table.

**Working mode note:** this was originally a learning project (João types the code, Claude
explains). For this overhaul João decided he'd "learned enough" and asked Claude to write it
directly. Default back to the type-it-yourself style for genuinely new learning.

**What's new this session (all written by Claude, then verified):**
- **Backend (test-first):** `adapter.monthly_trends(year, month, months=6)` and
  `adapter.fixed_vs_variable(year, month)` (thin wrappers over Banco's `ReportService`, still
  read-only); `GET /api/banco/trends` + `GET /api/banco/fixed-variable` in `banco_view/router.py`
  (current-month defaults like the others). First automated test suite in the project:
  `backend/tests/` — `conftest.py` builds a temp SQLite from Banco's `SCHEMA`, seeds known
  rows, monkeypatches `config.BANCO_DB_PATH`, yields a `TestClient`; **8 tests pass**. Dev deps
  in `backend/requirements-dev.txt` (`pytest`, `httpx`). Smoke-tested against the real DB — the
  numbers match `bank.py` (June expense R$478,55; fixed R$260,00 / variable R$218,55).
- **Frontend (dark theme + charts):** `style.css` fully rewritten — app shell + the Midnight
  Sepia palette described above (single source of truth in `:root`). New `App.jsx` shell
  (sidebar → bottom-tab at ≤820px, 5 nav entries, default Home). `HubHome.jsx` (3 entry cards).
  `BancoDashboard.jsx` rebuilt: `MonthSelector`, `StatCard` (×4 with deltas), `CategoryDonut` +
  `TrendChart` (Recharts), `FixedVariableBar`, `RecentActivity`. `BancoTransactions.jsx`
  restyled. `NewsPage.jsx` fixed (`setDigest` + `.digest`) and restyled. New `chartTheme.js`,
  `components/Timestamp.jsx`. `recharts` added to `package.json`. `npm run build` + `eslint`
  both clean.
- **Remaining:** João to eyeball the theme in the browser; then commit (currently uncommitted).
  Optional: day/night auto-switch. M5 (Tailscale + single-port prod build) still deferred.

---

### (historical) Milestone 2 BACKEND done (2026-06-18)

The full RSS + **Gemini** digest engine works end-to-end and is verified in `/docs`. (M1 — the
Banco read-only view, dashboard + transactions, responsive — was finished earlier.)

**Big decision this session:** João uses **Gemini instead of Anthropic** (free tier, no billing
setup). Package `google-genai` (install `google-genai`, import `from google import genai`), model
`gemini-2.5-flash`, key in `backend/.env` as `GEMINI_API_KEY=` (gitignored). Only `feeds/digest.py`
is AI-specific — everything else is provider-agnostic. Prompt caching skipped for now.

**What M2 added (all typed by João, learning-style):**
- `backend/requirements.txt` — added `feedparser`, `google-genai`.
- `backend/app/feeds/` (new package): `sources.py` (8 curated, **verified** feeds — finance:
  Money Times, Brazil Journal, Seu Dinheiro, Estadão E-Investidor; AI: TechCrunch, VentureBeat,
  Ars Technica, Hugging Face — `feeds_for(topic)` filters by topic), `fetcher.py`
  (`fetch_topic(topic)`: loops feeds, cleans each entry to `{source,title,link,published,summary}`,
  dedupes by link via a set, truncates summary to 300 chars, caps at 40), `digest.py`
  (`build_digest(topic)`: fetch → format numbered article block → one prompt → Gemini → Markdown;
  `TOPIC_LANGUAGE` map gives AI=English, finance=Brazilian Portuguese), `digest_store.py`
  (SQLite cache in a **separate writable** `hub.db`: `init_db`/`save_digest`/`load_digest`,
  `INSERT OR REPLACE` upsert keyed by topic), `router.py` (`GET /api/digest?topic=` → cached
  dict or `null`; `POST /api/digest/refresh?topic=ai|finance` → build+cache+return; 400 on bad
  topic). `__init__.py` marks the package.
- `backend/app/config.py` — added `GEMINI_API_KEY` and `HUB_DB_PATH` (`backend/hub.db`).
- `backend/app/main.py` — imports + `app.include_router(digest_router)`.
- `.gitignore` — added `hub.db` (local digest cache, not committed).

**Lessons worth remembering (teaching notes):**
- A feed returning HTTP **200 is not proof it's valid RSS** — measure `len(feed.entries)`, not the
  status. Two InfoMoney category feeds (`/mercados/feed/`, `/economia/feed/`) returned 0 entries
  and were dropped; the homepage `/feed/` works but mixes in sports (firehose) — avoid it.
- Gemini ignored a language instruction buried mid-prompt and replied in English; moving the
  rule to **line 1 and making it emphatic** (and adding "output ONLY the digest, no preamble")
  fixed it. Position + emphasis matter.
- `python -c "..."` breaks on pasted **indentation** — use a single line with `;` separators.

**▶️ First thing next session:** (1) run the app and eyeball the new theme (`uvicorn` +
`npm run dev`); tweak palette/spacing to taste. (2) Commit the overhaul (still uncommitted) —
add `recharts`/`react-markdown` are in `package.json`; `backend/requirements-dev.txt` is new.
(3) Then **M5** — Tailscale iPhone access + single-port prod build (`npm run build` served by
FastAPI). The historical M2/M3 pointers below are kept for reference.

**M1 closed out this session (2026-06-17):**
- **Verification checklist passed:** all four `/api/banco/*` endpoints return real JSON;
  dashboard numbers match `bank.py`; **shared-DB proof confirmed** (edited a transaction in the
  desktop `bank.py`, refreshed the web page, change appeared — proves we read the live DB);
  responsive nav drops to a bottom tab bar under 600px.
- **Cleanup done:** removed the temporary `/api/_debug/config` endpoint from `main.py` (and its
  now-unused `from app import config` import); `main.py` now holds only the FastAPI/CORS/router
  setup + `/api/health`.
- **Git set up:** root `.gitignore` ignores `.venv/`, `.env`, `node_modules/`, `__pycache__/`,
  `*.pyc`, and `backend/Banco/` (a leftover copy of Banco the app doesn't use — `config.py`'s
  `BANCO_SRC_PATH` points at the real Banco at `/home/joao/Workspaces_VSCODE/Meus_Projetos/Banco`).
  `git init`, branch renamed `master`→`main`, first commit `c9c59b5` (31 source files, no secrets).

**Next: Milestone 2** (RSS + Claude digest engine — needs an Anthropic API key). See below.

### (historical) earlier feature-complete note (2026-06-05)

New since last session (Steps 11–13, all typed by João):

- `frontend/src/components/Money.jsx` — first reusable component. `function Money({ cents,
  className })` → `(cents/100).toLocaleString('pt-BR', { style:'currency', currency:'BRL' })`
  → `<span className={className}>{formatted}</span>`. The optional `className` (added in Step
  13) lets callers tint amounts; omitting it just renders a plain span. Mirrors Banco's
  `format_brl`.
- `frontend/src/BancoDashboard.jsx` — now loads **two** things. Added `getCategories` to the
  import and a second state `const [categories, setCategories] = useState([])`. Both fetches
  live in **one** `useEffect(..., [])` (João merged them — fine). Summary now uses
  `<Money cents={...} />` (raw `/100` removed); income/expense carry `className="income"`/
  `"expense"`. Renders the categories list with `categories.map(cat => <li key={cat.category_id}>
  {cat.category_name}: <Money cents={cat.total_cents}/></li>)` under an `<h3>`.
- `frontend/src/BancoTransactions.jsx` — new page (lives in `src/`, not `components/`). Same
  shape as the dashboard's list code: `useState([])` + one-time `getTransactions().then(...)`,
  then `transactions.map(tx => <li key={tx.id}>{tx.date} - {tx.description} (<Money
  cents={tx.amount_cents}/>)</li>)`. `export default BancoTransactions`.
- `frontend/src/App.jsx` — real navigation. `const [page, setPage] = useState('dashboard')`;
  a `<nav>` with two buttons (`onClick={() => setPage('dashboard'|'transactions')}`); renders
  `{page === 'dashboard' ? <BancoDashboard/> : <BancoTransactions/>}`. (Teaching note: hit a
  sneaky typo bug — comparing against `'dashbboard'` (double-b) made the ternary always pick
  Transactions; fixed.)
- `frontend/src/style.css` — **new**, replaces the Vite starter `index.css`. `main.jsx` now
  `import './style.css'`. `:root` holds Banco's palette copied verbatim from `banco/ui/theme.py`
  (`--bg:#0b0c10`, `--card:#14161c`, `--card-border:#23262f`, `--fg:#fff`, `--fg-muted:#aab1c2`,
  `--income:#9ECE6A`, `--expense:#F7768E`, `--savings:#7AA2F7`, Manrope font stack). `section` =
  gradient card (1px border, `border-radius:16px`, padding). `ul`/`li` = bulletless flexbox
  rows (`justify-content: space-between` → label left, money right; hairline `border-bottom`,
  none on `:last-child`). `section p` uses the same flex trick for the summary rows. `.income`/
  `.expense`/`.savings` color classes. `nav` = flex tabs (`button{flex:1}`); inside
  `@media (max-width:600px)` the nav becomes `position:fixed; bottom:0` full-width tab bar
  (the `96px` bottom padding on `main` leaves room for it).

What's built and working:

- `backend/.venv/` — Python virtual environment.
- `backend/requirements.txt` — `fastapi`, `uvicorn[standard]`, `python-dotenv`.
- `backend/.env` — `BANCO_DB_PATH=/home/joao/.local/share/banco/banco.db`.
- `backend/app/__init__.py` — empty (marks `app` as a package).
- `backend/app/config.py` — loads `.env`; exposes `BANCO_DB_PATH` and `BANCO_SRC_PATH`.
  (Note: uses `from pathlib import Path` — *not* `import pathlib as Path`.)
- `backend/app/main.py` — FastAPI app with:
  - `GET /api/health` → `{"status": "ok"}`
  - `GET /api/_debug/config` → reports the DB path and `db_exists` (**temporary**, delete later)
- `backend/app/banco_view/__init__.py` — empty (marks `banco_view` as a package).
- `backend/app/banco_view/adapter.py` — the bridge into Banco:
  - puts `config.BANCO_SRC_PATH` on `sys.path`, imports `banco.repositories` / `banco.services`
    / `banco.models` (`TransactionKind`, `SortBy`) — Banco is never modified.
  - `_connect()` opens the same `banco.db` **read-only** (`file:...?mode=ro`, `uri=True`),
    `row_factory = sqlite3.Row`. Every function opens/closes its own short-lived connection.
  - Functions (all return JSON-ready dicts; money stays in **cents**, dates as ISO strings):
    - `list_accounts()` → `id / name / kind` (accounts-only by decision — Banco has no
      per-account balance; money totals come from `month_summary`).
    - `month_summary(year, month)` → `{year, month, current, previous}`, each totals dict has
      `income_cents / expense_cents / savings_cents / net_cents`
      (reuses `ReportService.monthly_summary` — note the method is `monthly_summary`).
    - `recent_transactions(limit=50, offset=0)` → newest-first list
      (reuses `TransactionRepository.list(sort=SortBy.DATE_DESC, ...)`; `*`-only kwargs).
    - `categories_with_totals(year, month)` → donut slices, largest first
      (reuses `ReportService.category_breakdown`, `kind=EXPENSE`; `category_id=None` = "Sem categoria").

**Verified (via `python -c`):** all four functions return correct data; May 2026 category
totals (R$ 140 + R$ 120) match `month_summary` expense (R$ 260).

`backend/app/banco_view/router.py` — `APIRouter(prefix="/api/banco", tags=["banco"])` with
`get_accounts` / `get_summary` / `get_transactions` / `get_categories`. `summary` and
`categories` default to the current month via `year or today.year`. Included in `main.py` with
`app.include_router(banco_router)`. All four verified in the browser.

> Editor note: Pylance shows an unresolved-import squiggle on `from banco import ...` in
> `adapter.py` — cosmetic only (the path is added at runtime via `sys.path.insert`). Optional
> fix: `.vscode/settings.json` → `python.analysis.extraPaths` pointing at the Banco root.

## ▶️ Next step when we resume (start Milestone 2)

M1 is finished. Next is **Milestone 2 — RSS + Claude digest engine (backend)**. See `PLAN.md`
"M2" for the shape: `feeds/sources.py` (~12 curated feeds), `feeds/fetcher.py`
(fetch/dedupe/cap with `feedparser`), `feeds/digest.py` (Claude summary, prompt caching on
static parts, Haiku 4.5, returns Markdown), cache the last digest in SQLite, and
`POST /api/digest/refresh?topic=ai|finance` (AI in English, finance in Portuguese).

**Before starting M2:** João needs an **Anthropic API key** in `backend/.env` as
`ANTHROPIC_API_KEY=...` (already `.gitignore`d). Add `feedparser` and `anthropic` to
`requirements.txt` and `pip install` them. Keep the learning style: one small runnable step,
explain each line. (When wiring the Claude call, check the `claude-api` skill for current model
ids/pricing/caching — don't answer from memory.)

**M1 polish — ✅ all done (2026-06-18):**
- **Brazilian dates:** new `frontend/src/components/DateBR.jsx` (twin of `Money`) renders ISO
  dates as `dd/mm/yyyy` via `toLocaleDateString('pt-BR')`, with a `+'T00:00:00'` suffix to dodge
  the UTC off-by-one-day trap; used in `BancoTransactions.jsx`.
- **"Sem categoria":** dashboard category name now `{cat.category_name || "Sem categoria"}`.
- **2-column dashboard:** dashboard split into two `<section>` cards (summary | categories)
  wrapped in `<div className="dashboard-grid">`; mobile-first CSS grid in `style.css` stacks on
  phones, `grid-template-columns: 1fr 1fr` at `min-width:700px`. Also fixed a typo'd selector
  (`sction h3` → `section h3`).
- **Starter CSS removed:** deleted `App.css` (dead) and `index.css` (was still imported by
  `main.jsx` and styling `#root`); ported the one wanted rule (`#root { text-align: center; }`)
  into `style.css`, now the single source of truth.

Remaining nice-to-haves (not done, not blocking): a 2-column layout could also apply elsewhere;
otherwise nothing pending — M1 + polish are complete.

> Teaching reminders: `${}` interpolation needs **backticks**, not quotes. Default import
> (`import X from`) for `export default`; named import (`import { x } from`) must match the name.
> `useEffect(fn, [])` runs once; forgetting `[]` + calling `setState` inside = infinite loop.
> Component files in `src/`, used as `<Capitalized />` tags.

> Endpoint shapes (all money in **cents**, dates ISO): `/api/banco/accounts` → `[{id,name,kind}]`;
> `/api/banco/summary` → `{year,month,current,previous}` each `{income_cents,expense_cents,savings_cents,net_cents}`;
> `/api/banco/transactions?limit=&offset=` → `[{id,date,amount_cents,kind,description,account_id,category_id,notes}]`;
> `/api/banco/categories?year=&month=` → `[{category_id,category_name,color,is_fixed,total_cents}]`.
> `summary`/`categories` default to the current month if no params. Reuse Banco's
> `format_brl`/`format_date_br` logic (in `banco/ui/format.py`) for display formatting.

## How to start the dev environment

**Easiest: `./start.sh` from the project root** launches both modules in one terminal
(backend Uvicorn :8000 + frontend Vite :5173, logs prefixed `[hub]`); Ctrl+C once stops both
cleanly. It loads nvm for the frontend automatically and fails early with a hint if `.venv` or
`node_modules` are missing. Variants: `./start.sh backend` / `./start.sh frontend` for just one.

To start the two modules **manually** instead:

```bash
# Backend
cd /home/joao/Workspaces_VSCODE/Meus_Projetos/HubPessoal/backend
source .venv/bin/activate          # prompt shows (.venv)
uvicorn app.main:app --reload --port 8000
# → open http://localhost:8000/docs

# Frontend (in a SECOND terminal — Node via nvm, no venv)
cd /home/joao/Workspaces_VSCODE/Meus_Projetos/HubPessoal/frontend
npm run dev
# → open http://localhost:5173  (proxies /api → :8000, so keep the backend running too)
```

## Cleanup TODOs — ✅ all done (2026-06-17)

- ~~Remove the temporary `GET /api/_debug/config` endpoint.~~ Done (and its unused import).
- ~~Set up git + a `.gitignore` for `.venv/`, `.env`, `node_modules/`.~~ Done (first commit `c9c59b5`).
