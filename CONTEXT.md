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

## ✅ Where we are right now (as of 2026-06-05)

**Milestone 1 is FEATURE-COMPLETE (Steps 1–13).** Backend serves all four endpoints; the React
app shows a styled, navigable, responsive view of the finances — dashboard (month summary +
per-category spend) and a transactions page, switchable via a nav, themed to match Banco, with
a phone bottom tab bar. **Verified visually end-to-end** (numbers match `bank.py`). Only the
formal verification checklist + two cleanup TODOs remain before we call M1 "done."

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

## ▶️ Next step when we resume (close out Milestone 1)

All 13 build steps are done; what's left is to **verify** and **clean up**, then M1 is finished.

1. **Run the M1 verification checklist** (see "Verification (Milestone 1)" in `PLAN.md`):
   - Backend `/docs`: call each `/api/banco/*`, confirm real JSON.
   - Frontend at `:5173`: dashboard summary + categories and the transactions page match
     `bank.py`.
   - **Shared-DB proof (the important one):** edit a transaction in the desktop `bank.py`,
     refresh the web page, confirm the change shows up — proves we read the live DB.
   - **Responsive:** shrink the browser under 600px; confirm the nav drops to a bottom tab bar.
2. **Cleanup TODOs (see the section below):** remove the temporary `GET /api/_debug/config`
   endpoint from `backend/app/main.py`; set up git + a `.gitignore` for `.venv/`, `.env`,
   `node_modules/`.
3. **Optional polish (nice-to-have, not blocking):** prettify `tx.date` (`2026-05-28` →
   Brazilian format, mirroring Banco's `format_date_br` in `banco/ui/format.py`) the same way
   `Money` handles money; handle the blank "Sem categoria" name (a `null` `category_name`/
   `category_id`); consider a 2-column dashboard on wide screens (summary | categories).

Then we're clear to start **Milestone 2** (RSS + Claude digest engine — needs an Anthropic API
key; see `PLAN.md`).

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

## Cleanup TODOs (don't forget)

- Remove the temporary `GET /api/_debug/config` endpoint before "finishing" Milestone 1.
- When git is set up: add a `.gitignore` for `.venv/`, `.env`, and `node_modules/`.
