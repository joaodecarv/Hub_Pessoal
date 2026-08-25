# PRD — Hub UI Overhaul + Finish (M3–M4)

> **Status:** ✅ **BUILT (2026-06-20, uncommitted).** All slices below are implemented; backend
> endpoints are covered by 8 passing tests. Supersedes the sketches for M3 (digest pages) and M4
> (hub landing + nav polish) in `PLAN.md`. Captured from a grill-me design session on 2026-06-20.
> **Working-mode change:** the learning/teaching constraint is paused for this phase —
> Claude writes the code directly. `PLAN.md` / `CONTEXT.md` stay the source of truth and get
> updated as work lands.
>
> **⚠️ Theme update (post-design):** this PRD specifies a *light* "warm paper" theme, but during
> the build João asked for a low-eye-strain theme for early-morning/late-night use. **Shipped
> theme = "Midnight Sepia" (warm dark)** — same warm/clay character, dark surfaces. Everything
> else below is as built. A day/night auto-switch (light by day, this dark theme at night)
> remains an open option. See `CONTEXT.md` for the final palette.

## Problem Statement

João has a working personal hub — a read-only web view of his **Banco** finances plus an
RSS + Gemini news-digest engine — but the frontend stops short of being usable and pleasant:

- The **finance dashboard is bare**: four numbers and a flat category list. There are no
  charts, so he can't see *how his expenses move month to month* or *which class of
  transactions dominates his spending* — the two questions he actually opens the app to answer.
- The **news pages are broken and unstyled**: the Refresh handler calls an undefined
  `newDigest` instead of `setDigest`, and the Markdown wrapper uses a CSS class
  (`news-digest`) that no rule targets, so digests render as unstyled text and refreshing
  throws.
- The **whole UI looks like a developer scaffold**: top-button navigation, English-default
  scaffold styling, and the old dark Banco navy palette. It doesn't feel like the polished,
  professional product his desktop Banco app already is.

He wants to finish the project and remake the UI into something professional and simple,
themed like the Claude interface, with cards and charts on the dashboard.

## Solution

Remake the Hub frontend around a **light "warm paper" theme** (true Claude.ai look: cream
background, dark brown text, clay/terracotta accent), with a **persistent left sidebar that
collapses to a bottom tab bar on phones**. Add the two charts he asked for to a real
**dashboard**, finish and restyle the **news pages**, and add a **hub home** overview.

Concretely:

- A **Hub Home** landing page (default on open) with three entry cards: a finance snapshot
  and the "last updated" timestamps for the AI and Finance digests.
- A **Dashboard** with: month-summary cards (Income / Expenses / Savings / Net) showing
  vs-previous-month deltas; a **category-share donut**; a **6-month expense-trend bar
  chart**; and a **Fixed-vs-Variable split with a recent-activity list**. A **month
  selector** (top-right) drives the per-month cards/donut/split; the trend always shows the
  last ~6 months ending at the selected month.
- **Transactions** and **News (AI / Finance)** pages restyled to the new theme; the news
  pages fixed so Refresh works and digests render as styled Markdown with an `updated_at`
  stamp.
- Charts rendered with **Recharts**.

**Deferred (documented, not built here):** M5 — iPhone access via Tailscale and the
single-port production build (`npm run build` served by FastAPI).

## User Stories

1. As João, I want the hub to open on a **home overview**, so that I see the state of all
   three areas (finances + both news digests) at a glance before drilling in.
2. As João, I want each home card to show a **"last updated" timestamp** for the AI and
   Finance digests, so that I know whether a digest is stale before I open it.
3. As João, I want a home card with a **finance snapshot** (e.g. current-month net/balance),
   so that I get the headline number without opening the full dashboard.
4. As João, I want a **persistent left sidebar** on desktop listing Home, Dashboard,
   Transactions, AI News, and Finance News, so that I can jump between sections in one click.
5. As João, I want the sidebar to **collapse into a fixed bottom tab bar on my phone**, so
   that navigation stays reachable with a thumb on a small screen.
6. As João, I want the whole UI in a **light warm-paper theme** like Claude's, so that the
   hub looks professional and calm instead of like a dev scaffold.
7. As João, I want the dashboard to show **Income, Expenses, Savings, and Net as cards**, so
   that the month's headline figures are scannable.
8. As João, I want each summary card to show a **delta vs the previous month** (direction +
   amount), so that I can tell whether I did better or worse than last month.
9. As João, I want a **donut chart of expenses by category**, so that I can see which class
   of transactions occupies what percentage of my spending.
10. As João, I want uncategorized spending shown as **"Sem categoria"** in the donut and
    lists, so that nothing silently disappears from the totals.
11. As João, I want a **bar chart of total expenses across the last ~6 months**, so that I
    can compare my spending month to month and spot trends.
12. As João, I want a **Fixed-vs-Variable split** for the selected month, so that I can see
    how much of my spending is committed vs discretionary.
13. As João, I want a **short recent-activity list** on the dashboard, so that I see my
    latest transactions without leaving the page.
14. As João, I want a **month selector** in the top-right, so that I can browse past months
    instead of only the current one.
15. As João, I want the **summary cards, donut, and fixed/variable split to follow the
    selected month**, so that the whole per-month view stays consistent.
16. As João, I want the **trend chart to show the last ~6 months ending at the selected
    month**, so that the comparison context updates as I browse.
17. As João, I want **charts with readable tooltips and legends** in the theme's palette, so
    that I can read exact values on hover.
18. As João, I want a full **Transactions page** restyled to the new theme, so that I can
    scan my recent transactions with Brazilian date and currency formatting.
19. As João, I want the **AI News page** to show the cached digest instantly on open, so that
    I don't wait for a network call to read what I already fetched.
20. As João, I want a **Refresh button** on each news page that rebuilds the digest and swaps
    in the new summary, so that I can pull the latest news on demand.
21. As João, I want the **Refresh button to actually work** (no crash) and show a loading
    state while building, so that I get feedback and a correct result.
22. As João, I want **digests rendered as styled Markdown** (headings, lists, links) in the
    light theme, so that they're readable rather than a wall of raw text.
23. As João, I want each news page to show the digest's **`updated_at` timestamp** in a
    friendly format, so that I know how fresh the summary is.
24. As João, I want the **AI digest in English and the Finance digest in Portuguese**
    (already handled by the backend), so that each matches its sources.
25. As João, I want all money shown as **`R$ x.xxx,xx`** and dates as **dd/mm/yyyy**, so that
    the figures read naturally for Brazil.
26. As João, I want the layout to **stay responsive** between phone and desktop, so that the
    hub is comfortable on both.
27. As João, I want the **trend and fixed/variable data served by the backend**, so that the
    frontend stays a thin view over the API.
28. As João (developer), I want the **new backend endpoints covered by automated tests**, so
    that the month-range math doesn't silently break later.

## Implementation Decisions

### Theme & layout
- **Theme:** light "warm paper" — cream/off-white background, dark brown text, a single
  clay/terracotta accent, soft shadows on cards. Replaces the dark Banco navy palette in
  `style.css` wholesale. CSS custom properties hold the palette (one source of truth).
- **Navigation:** an app shell with a persistent **left sidebar** (desktop) that becomes a
  **fixed bottom tab bar** under the existing responsive breakpoint. Five entries: Home,
  Dashboard, Transactions, AI News, Finance News. Replaces the current top-button `<nav>` in
  `App.jsx`. Page switching stays the existing `useState`-based approach (no router added).
- **Default page:** Hub Home.
- **UI label language:** **English** (Income / Expenses / Savings / Net / Fixed / Variable /
  Recent Activity). Money and dates remain Brazilian-formatted via the existing `Money` and
  `DateBR` components.

### Dashboard
- **Charts library:** **Recharts** (new frontend dependency). Donut = `PieChart`/`Pie`;
  trend = `BarChart`/`Bar`; both wrapped in `ResponsiveContainer`, themed to the palette,
  with tooltips/legends.
- **Month selector:** top-right control bound to a `{year, month}` state, defaulting to the
  current month. Drives `getSummary`, `getCategories`, and the new fixed/variable fetch; the
  trend fetch requests the last 6 months ending at the selected month.
- **Cards:** reuse `/api/banco/summary` (`current` + `previous`); compute and render deltas
  from the two totals blocks.
- **Donut:** reuse `/api/banco/categories`; "Sem categoria" for `null` category names.

### Backend additions (adapter + router, read-only, never writes)
- **New adapter function `monthly_trends(year, month, months=6)`** — loops Banco's
  `ReportService.monthly_totals` backward from the selected month, returning a
  chronological list of `{year, month, expense_cents, income_cents}` (at minimum
  `expense_cents`). Money stays in **cents**.
- **New adapter function `fixed_vs_variable(year, month)`** — wraps Banco's
  `ReportService.fixed_vs_variable`, returning `{fixed_cents, variable_cents}`.
- **New endpoints** on the existing `/api/banco` router:
  - `GET /api/banco/trends?year=&month=&months=` → list described above; defaults to current
    month and 6 months when params are omitted (mirrors how `summary`/`categories` default).
  - `GET /api/banco/fixed-variable?year=&month=` → `{fixed_cents, variable_cents}`; same
    defaulting.
- All new endpoints follow the existing conventions: cents for money, ISO strings for dates,
  read-only `mode=ro` connections, current-month defaults.

### Frontend API helpers (`api.js`)
- Add `getTrends(year, month, months)` and `getFixedVariable(year, month)` following the
  existing `getSummary`/`getCategories` query-string pattern (params omitted → backend
  defaults).

### News pages (finish M3)
- **Fix the Refresh bug:** `refreshDigest(topic).then(setDigest)` (currently the undefined
  `newDigest`).
- **Fix the CSS class mismatch:** the Markdown wrapper and the stylesheet must agree on one
  class for digest content (consolidate on the existing `.digest` rules).
- **Restyle** digest Markdown for the light theme (headings, lists, links, readable line
  length); show `updated_at` via a friendly formatter.
- Keep **on-demand refresh only** (no auto-refresh, no cron) — consistent with the project's
  token-efficiency stance. Show a loading state while a refresh is in flight.

### Hub Home
- A landing page composing three entry cards: a finance snapshot (from `/api/banco/summary`)
  and the AI + Finance digest `updated_at` values (from `/api/digest?topic=`, which already
  returns the cached dict or `null`). Clicking a card navigates to that section.

## Testing Decisions

- **What makes a good test here:** assert **external behavior through the HTTP boundary** —
  the JSON shape and values an endpoint returns for a known database — not internal function
  wiring. Tests must not depend on the live `banco.db`; they run against a **temporary
  SQLite seeded with Banco's schema and a few fixture transactions** across multiple months.
- **Highest seam = the FastAPI app via `TestClient`.** This is the project's first automated
  test suite (today everything is verified by hand in `/docs`). Cover:
  - `GET /api/banco/trends` — returns the expected number of months in chronological order,
    correct `expense_cents` per month, correct handling of months with no transactions
    (zeros, not gaps), and correct default behavior when params are omitted.
  - `GET /api/banco/fixed-variable` — `fixed_cents` + `variable_cents` match the seeded data
    and sum to the month's expense total.
  - A light regression check on the existing `/api/banco/summary` and `/api/banco/categories`
    contracts (shape unchanged) since the dashboard now leans on them harder.
- **Prior art:** none in-repo yet; the manual `python -c` checks recorded in `CONTEXT.md`
  (e.g. "May 2026 category totals R$140 + R$120 match summary expense R$260") encode the kind
  of arithmetic the automated tests should now assert.
- **Frontend:** verified manually (the project's existing norm) — theme, responsive
  sidebar→bottom-tab behavior, chart rendering, month-selector wiring, and the news Refresh
  flow are eyeball-checked. **Optional/nice-to-have:** Vitest unit tests on `api.js`
  URL-building (param-omission cases). No component/visual test infrastructure is introduced
  in this PRD.

## Out of Scope

- **M5 — Tailscale iPhone access and the single-port production build** (`npm run build`
  served by FastAPI). Documented as the next step; not built here.
- **Writing to Banco from the web** — the hub stays strictly read-only.
- **Authentication** — deferred to Tailscale (M5).
- **Scheduled/automatic digest refreshes**, push notifications, and a settings UI to manage
  feeds — unchanged from the original out-of-scope list.
- **A client-side router** — page switching stays `useState`-based.
- **New digest/news features** beyond fixing and restyling the existing pages (e.g. per-source
  article lists, search) — not in this pass.
- **Backfilling historical finance data** — the trend chart shows whatever months exist in
  `banco.db`; it will look sparse until more months accrue (acknowledged, not addressed here).

## Further Notes

- **Data richness caveat:** the 6-month trend is only as informative as the history in
  `banco.db`. With just a couple of months of data it will render sparse; this is expected and
  self-resolves as months accrue.
- **Dependencies:** `react-markdown` is already installed; **`recharts` must be added** to
  `frontend/package.json`.
- **Reuse, don't fork:** new backend work wraps Banco's existing `ReportService`
  (`monthly_totals`, `fixed_vs_variable`) through the adapter — Banco itself is never
  modified, consistent with the locked architecture.
- **Docs:** on completion, update `PLAN.md` (mark M3/M4 done, fold the UI overhaul in) and
  `CONTEXT.md` (new endpoints, theme switch, where we stopped).
- **No issue tracker:** this repo has no git remote / GitHub project, so this PRD is published
  as `PRD.md` at the repo root alongside `PLAN.md` and `CONTEXT.md`, matching the project's
  existing documentation convention. (The `ready-for-agent` triage step from the to-prd
  workflow does not apply without a tracker.)
