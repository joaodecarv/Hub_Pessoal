import { useState } from 'react'
import { brl, pct } from '../finance/format.js'
import { shareOfIncome } from '../finance/derive.js'

const SW = 1000, SH = 400, NODE = 12, GAP = 10
const X = [0, 260, 540, 820]

// Sankey of the month: income sources → renda → fixas / variáveis / guardado / sobra →
// expense categories. When spending exceeds income, the gap enters as a "Déficit" source
// so every flow still balances. Fixed/variable here follows each category's flag.
function MoneyFlow({ summary, incomeCategories, expenseCategories }){
    const [hl, setHl] = useState(null)
    const c = summary.current
    const last = (x) => x.history_cents[x.history_cents.length - 1]
    const deficit = Math.max(0, -c.net_cents)
    const total = c.income_cents + deficit
    if (!total) return <p className="note">Sem movimentação neste mês.</p>

    const k = (SH - GAP * 6) / total
    const stack = (list, x, y0 = 0, gap = GAP) => {
        let y = y0
        return list.filter((n) => n.v > 0).map((n) => { const h = Math.max(n.v * k, 2); const o = { ...n, x, y, h }; y += h + gap; return o })
    }
    const spent = expenseCategories.filter((x) => last(x) > 0)
    const fixed = spent.filter((x) => x.is_fixed), variable = spent.filter((x) => !x.is_fixed)
    const sum = (list) => list.reduce((a, x) => a + last(x), 0)

    const sources = stack([
        ...incomeCategories.map((x) => ({ id: 'in-' + x.category_name, label: x.category_name, v: last(x) })),
        { id: 'deficit', label: 'Déficit', v: deficit, tone: 'bad' },
    ], X[0], 30)
    const renda = stack([{ id: 'renda', label: 'Renda', v: total }], X[1], 20)
    const mid = stack([
        { id: 'fix', label: 'Fixas', v: sum(fixed) },
        { id: 'var', label: 'Variáveis', v: sum(variable) },
        { id: 'sav', label: 'Guardado', v: c.savings_cents, tone: 'save' },
        { id: 'net', label: 'Sobra', v: Math.max(0, c.net_cents), tone: 'good' },
    ], X[2], 0, 20)
    const leaves = stack([...fixed, ...variable].map((x) => ({ id: x.category_name, label: x.category_name, v: last(x), parent: x.is_fixed ? 'fix' : 'var' })), X[3], 0, 13)

    const links = [], used = {}
    const take = (n, h, side) => { const key = n.id + side; const y = n.y + (used[key] ?? 0); used[key] = (used[key] ?? 0) + h; return y }
    const link = (a, b, v, tone, group) => {
        const h = v * k, y0 = take(a, h, 'o'), y1 = take(b, h, 'i'), x0 = a.x + NODE, x1 = b.x, xm = (x0 + x1) / 2
        links.push({ d: `M${x0},${y0}C${xm},${y0} ${xm},${y1} ${x1},${y1}L${x1},${y1 + h}C${xm},${y1 + h} ${xm},${y0 + h} ${x0},${y0 + h}Z`, tone, group })
    }
    sources.forEach((s) => link(s, renda[0], s.v, s.tone, 'in'))
    mid.forEach((m) => link(renda[0], m, m.v, m.tone, m.id))
    leaves.forEach((l) => link(mid.find((m) => m.id === l.parent), l, l.v, '', l.parent))

    const label = (n, right) => {
        const share = shareOfIncome(n.v, c.income_cents)
        return (
            <text key={'t' + n.id} x={right ? n.x + NODE + 8 : n.x - 8} y={n.y + n.h / 2} textAnchor={right ? 'start' : 'end'} dominantBaseline="middle">
                <tspan>{n.label}</tspan>
                <tspan className="flow-v" dx="8">{brl(n.v)}{n.id !== 'renda' && share !== null && ` · ${pct(share)}`}</tspan>
            </text>
        )
    }
    return (
        <svg viewBox={`-240 -6 ${SW + 440} ${SH + 12}`} className="flow" role="img"
             aria-label={`Renda de ${brl(c.income_cents)}: ${brl(c.expense_cents)} em despesas, ${brl(c.savings_cents)} guardados, ${c.net_cents < 0 ? `déficit de ${brl(deficit)}` : `${brl(c.net_cents)} de sobra`}.`}>
            {links.map((l, i) => (
                <path key={i} d={l.d} className={`flow-link ${l.tone ? 'flow-' + l.tone : ''} ${hl && hl !== l.group ? 'is-dim' : ''}`}
                      onMouseEnter={() => setHl(l.group)} onMouseLeave={() => setHl(null)} />
            ))}
            {[...sources, ...renda, ...mid, ...leaves].map((n) => (
                <rect key={n.id} x={n.x} y={n.y} width={NODE} height={n.h} className={`flow-node ${n.tone ? 'flow-' + n.tone + '-n' : ''}`} />
            ))}
            {sources.map((n) => label(n, false))}
            {[...renda, ...mid, ...leaves].map((n) => label(n, true))}
        </svg>
    )
}

export default MoneyFlow
