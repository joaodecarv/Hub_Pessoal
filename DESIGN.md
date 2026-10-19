# Design Direction: HubPessoal — Monochrome Finance (Minimalism + Dark UI)

Decided 2026-10-18 (graphic-designer + grilling session). Replaces the "Midnight Sepia" theme.
Reference products: XP / Rico. Personality: precise, calm, trustworthy.

**Core rule:** the interface is black, white and gray. Color appears only where it encodes
data: green = money in, red = money out, blue = savings, amber = warning (over budget /
goal off track). Buttons, the active nav item and the selected month use the text color,
never a hue — so a colored pixel always means something about the money.

Two themes, light and dark, switched **only by a manual button** in the sidebar footer
(sun/moon icon). The choice is saved in `localStorage` (`hub-theme`) and applied as
`<html data-theme="light|dark">`. Default on first visit: dark. No `prefers-color-scheme`.

## Palette

All values below were checked for WCAG contrast (ratios against the listed surfaces).

### Neutrals

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#F5F5F4` | `#0F0F10` | Page background |
| `--surface` | `#FFFFFF` | `#18181A` | Cards, sidebar, glossary panel |
| `--surface-2` | `#F0F0EE` | `#222225` | Row hover, table header, pressed button, skeletons |
| `--border` | `#E4E4E2` | `#2A2A2D` | Card edges, dividers (decorative, no contrast requirement) |
| `--border-strong` | `#8E8E88` | `#6A6A70` | Input and select borders (≥3:1 vs bg) |
| `--text` | `#111111` | `#EDEDED` | Primary text, KPI numbers, primary button fill |
| `--text-2` | `#55554F` | `#A1A1A6` | Secondary text, labels, news summary (≥6:1) |
| `--text-3` | `#6E6E68` | `#8A8A90` | Captions, timestamps, axis labels (≥4.5:1 on every surface) |
| `--on-text` | `#FFFFFF` | `#0F0F10` | Text on a `--text`-filled button |

### Data colors (only for money and status)

| Token | Light | Dark | Meaning |
|---|---|---|---|
| `--income` | `#12733A` | `#3DD68C` | Receitas, positive deltas, account balance > 0 |
| `--expense` | `#B91C1C` | `#F87171` | Despesas, negative deltas, balance < 0 |
| `--savings` | `#1D4ED8` | `#60A5FA` | Poupança, goal progress |
| `--warning` | `#8A5A06` | `#FBBF24` | Goal behind schedule, budget over limit |

Each has a tint for backgrounds behind small badges: `color-mix(in srgb, var(--income) 12%, transparent)`.
Text on a tint uses the solid token itself.

### Chart categorical palette (donut only)

Never red or green, so categories are not read as gain/loss. These hues exist only inside
the donut and its legend (slot 3 shares its dark value with `--warning`, which never appears
in the donut, so the two never sit side by side). Show the **top 4 categories +
"Outros"** (5 slices max); more slices are unreadable in a donut.

| Slot | Light | Dark |
|---|---|---|
| 1 | `#7C3AED` violet | `#A78BFA` |
| 2 | `#0E7490` cyan | `#22D3EE` |
| 3 | `#B45309` amber | `#FBBF24` |
| 4 | `#BE185D` pink | `#F472B6` |
| Outros / Sem categoria | `--text-3` | `--text-3` |

### Trend chart

The 6-month expense bars are neutral (`--border-strong`); the **selected month** bar is `--text`.
The bars aren't red because the chart is about comparing months, not about how alarming spending is.

## Typography

- **Family:** Inter (Google Fonts, weights 400/500/600), fallback `system-ui, sans-serif`.
- **Numbers:** every money value, percentage and date uses `font-variant-numeric: tabular-nums`
  so columns line up. Negative values use a real minus sign `−` (U+2212), not a hyphen.
- On dark, body weight stays 400 but add `letter-spacing: 0.01em` (light-on-dark text looks heavier).

| Role | Size / line-height | Weight | Use |
|---|---|---|---|
| Display | 32px / 1.15 | 600 | Main KPI value (Saldo do mês) |
| KPI | 24px / 1.2 | 600 | Other KPI values, account balances |
| H1 | 24px / 1.25 | 600 | Page title |
| H2 | 16px / 1.3 | 600 | Card title, glossary group |
| Body | 15px / 1.55 | 400 | Default text, news header (500) |
| Small | 13px / 1.45 | 400 | News summary, table cells, deltas |
| Caption | 12px / 1.35 | 500 | Labels above numbers, timestamps, badges |

Labels stay in sentence case ("Despesas do mês"). No uppercase-with-tracking labels.

## Spacing & layout

- **Base unit 4px.** Scale: 4, 8, 12, 16, 24, 32, 48.
- **Radius:** 8px for controls (buttons, inputs, badges, images), 12px for cards. Nothing else.
- **Shadows:** none. Light theme: cards are separated by `1px solid var(--border)` on `--bg`.
  Dark theme: the lighter surface plus the same border expresses elevation.
- **Shell:** sidebar 232px (unchanged); content `max-width: 1200px`, padding 32px (desktop) /
  16px (phone). Under 768px the sidebar becomes the existing bottom tab bar.
- **Grid:** 12 columns, gap 16px. Cards span 3 (KPI), 6 (half) or 12 (full); every card is
  12 columns under 768px.

### Dashboard order

1. KPI row (4 × span 3): Saldo do mês · Receitas · Despesas · Taxa de poupança, each with
   delta vs the previous month.
2. Tendência de 6 meses (span 7) · Despesas por categoria donut (span 5).
3. Fixo vs variável (span 5) · Maiores despesas do mês, top 5 (span 7).
4. Saldo por conta (span 6) · Metas (span 6).
5. Atividade recente (span 12).

The month selector sits top-right in the page header and drives every per-month card.

### News page

Two columns on desktop: the article list (single column, `max-width: 760px`) and a
glossary column (260px, `position: sticky; top: 24px`). Under 1024px the glossary moves to an
"Índice" button in the page header that opens a bottom sheet.

## Component treatment

### Buttons

| Variant | Rest | Hover | Active | Focus | Disabled |
|---|---|---|---|---|---|
| Primary (one per view, e.g. "Atualizar") | bg `--text`, text `--on-text` | bg `--text` at 88% (`color-mix` with `--bg`) | `transform: scale(0.98)` | focus ring | avoid — show a spinner + "Atualizando…" instead |
| Secondary | bg transparent, `1px solid var(--border-strong)`, text `--text` | bg `--surface-2` | scale(0.98) | focus ring | — |
| Ghost (icon buttons, theme toggle) | transparent, text `--text-2` | bg `--surface-2`, text `--text` | scale(0.98) | focus ring | — |

Height 36px, padding 0 14px, radius 8px, 14px/500. Transitions `150ms ease` on
background/transform only.

**Focus ring (everything focusable):** `outline: 2px solid var(--text); outline-offset: 2px;`
on `:focus-visible`. Never `outline: none` without this.

### Cards

`background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;`
Header: H2 title left, optional caption/actions right, 16px below. No colored headers, no icons in
titles.

### KPI card

Caption label (`--text-2`) → value (Display/KPI, `--text`) → delta line (Small): `▲ R$ 420,00 vs set`
colored by meaning, not direction. For Despesas, a rise is `--expense` and a fall is `--income`.
Zero change is `--text-3`.

### Tables / lists (transactions, top expenses, recent activity)

No card-per-row. Rows 44px, `border-bottom: 1px solid var(--border)`, hover `--surface-2`.
Amount column right-aligned, tabular, colored by `--income`/`--expense`. Date in `--text-3`.

### Goals

Name + "R$ 1.200 de R$ 5.000" (Small, `--text-2`) + progress bar 6px tall, track `--surface-2`,
fill `--savings`, or `--warning` when `on_track` is false, or `--income` when achieved.
Caption: days remaining.

### Account balances

One row per account: kind icon (Lucide `landmark`, `piggy-bank`, `credit-card`, `wallet`) in
`--text-2`, name, balance right-aligned and colored by sign. A total row at the bottom.
Caption under the card title: "Soma de todas as transações" (balance is computed — see
`PLAN.md`, "Future: desktop app").

### Inputs / selects (month selector)

Height 36px, bg `--surface`, `1px solid var(--border-strong)`, radius 8px, text `--text`.
Hover: border `--text-2`. Focus: focus ring.

### Navigation (sidebar + bottom tab bar)

Sidebar bg `--surface`, right border `--border`. Item: 36px, radius 8px, Lucide icon 18px + label,
`--text-2`. Hover: bg `--surface-2`. Active: bg `--surface-2`, text `--text`, weight 500, and a
2px `--text` bar on the left edge (square corners). Theme toggle sits in the sidebar footer (in the
tab bar on phones it moves into the page header as a ghost icon button).

### News card

```
┌──────────┬──────────────────────────────────────────────┐
│  image   │ [icon] Fusões e aquisições                   │  ← badge
│ 120×80   │ Header da notícia em 15px/500, até 2 linhas  │
│          │ Resumo de 1–2 frases em 13px --text-2        │
│          │                          Ler no Brazil Journal ↗ │
└──────────┴──────────────────────────────────────────────┘
```

- Container: card style, padding 16px, `display: grid; grid-template-columns: 120px 1fr; gap: 16px`.
  `scroll-margin-top: 24px` so glossary jumps don't hide the top edge. `id="n-<index>"`.
- Image: 120×80, radius 8px, `object-fit: cover`, `loading="lazy"`, `alt=""` (decorative — the
  header carries the meaning). Dark theme: `filter: brightness(0.9)`. On load error, swap to the
  icon fallback.
- Icon fallback: same 120×80 box, bg `--surface-2`, the category's Lucide icon 28px in `--text-3`.
- Badge: Caption, `--text-2`, bg `--surface-2`, radius 8px, padding 2px 8px, with the 14px
  category icon. Neutral — categories are not data colors.
- Link: last line, right-aligned, Small/500, `--text`, underline on hover, text names the
  destination ("Ler no <fonte>"), `target="_blank" rel="noopener noreferrer"`.
- Phone (<640px): image goes full-width on top (16:9, max-height 160px), text below.

Category icons (Lucide):

| Topic | Category | Icon |
|---|---|---|
| Finance | Mercado e macro | `trending-up` |
| Finance | Negócios corporativos | `handshake` |
| Finance | Cripto | `bitcoin` |
| Finance | Finanças pessoais | `wallet` |
| AI | Tecnologia | `cpu` |
| AI | Negócios de AI | `briefcase` |

### Glossary

- Panel: card style, padding 16px. Groups in the same order as the page; group title = H2 with the
  category icon; under it the headers of that group's news as links (Small, `--text-2`, 2-line clamp).
- Click: `element.scrollIntoView({ behavior: 'smooth', block: 'start' })` and move focus to the
  card (`tabindex="-1"`) so keyboard and screen-reader users land there too.
- Current item: an `IntersectionObserver` marks the news card in view; its glossary link gets
  `--text`, weight 500 and a 2px left bar (same as the active nav item), plus `aria-current="true"`.
- Respect `prefers-reduced-motion: reduce` → `behavior: 'auto'` (instant jump).
- Phone: "Índice" secondary button → bottom sheet (max-height 70vh, internal scroll); picking
  an item closes the sheet, then scrolls.

## Dos & Don'ts

- Do keep every non-data element neutral. If a new component "needs some color", it doesn't.
- Do color deltas by meaning (good/bad for you), not by arrow direction.
- Do right-align and tabular-align every money column; `R$ 1.234,56` via the existing `Money` component.
- Don't put more than one primary (filled) button on a screen.
- Don't add shadows, gradients or blur — borders and surface steps only.
- Don't exceed 5 donut slices; group the rest into "Outros".

## Accessibility notes

- Verified: `--text-3` ≥ 4.5:1 and all data colors ≥ 5.1:1 on every surface in both themes
  (light `--income` was darkened from `#15803D`, and `--warning` from `#A16207`, to pass on `--surface-2`).
- Input borders (`--border-strong`) ≥ 3:1 against the page in both themes.
- Green/red must never be the only cue: deltas carry ▲/▼ and a sign, amounts carry `+`/`−`,
  goal states carry text ("No ritmo", "Atrasada", "Concluída").
- Charts: Recharts tooltips use `--surface` / `--text`; each chart also gets a visually hidden
  text summary (e.g. "Despesas de mai a out: …").
- Theme toggle: `aria-label="Mudar para tema claro|escuro"`, `aria-pressed` reflects dark mode.
- Glossary links and nav are reachable by keyboard; focus ring visible on every surface.
