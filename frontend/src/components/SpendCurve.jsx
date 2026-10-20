import { useState } from 'react'
import { brl, pct } from '../finance/format.js'
import { cumulative } from '../finance/derive.js'

const W = 760, H = 280, L = 64, R = 12, T = 12, B = 26

// Round the axis top up to 1, 2, 2.5 or 5 × 10^k so the gridlines land on readable values.
function niceMax(v){
    if (v <= 0) return 100000
    const step = v / 3, mag = 10 ** Math.floor(Math.log10(step))
    const nice = [1, 2, 2.5, 5, 10].find((n) => n * mag >= step)
    return nice * mag * 3
}
const axisLabel = (cents) => (cents === 0 ? '0' : `${(cents / 100000).toLocaleString('pt-BR')} mil`)

// Month-to-date spending: this month (to `lastIndex`), the previous month dashed, and the
// month's total budget as a reference line when there is one.
function SpendCurve({ daily, prevDaily, lastIndex, budgetCents, monthLabel, prevLabel }){
    const [hover, setHover] = useState(null)
    const cur = cumulative(daily.map((d) => d.expense_cents)).slice(0, lastIndex + 1)
    const prev = cumulative(prevDaily.map((d) => d.expense_cents))
    const span = Math.max(daily.length, prevDaily.length) - 1
    const max = niceMax(Math.max(cur[cur.length - 1] ?? 0, prev[prev.length - 1] ?? 0, budgetCents))
    const x = (i) => L + (i / span) * (W - L - R)
    const y = (v) => T + (1 - v / max) * (H - T - B)
    const path = (arr) => arr.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('')
    const i = hover ?? lastIndex
    const diff = prev[i] === undefined ? null : cur[i] - prev[i]

    function onMove(e){
        const r = e.currentTarget.getBoundingClientRect()
        const d = Math.round(((((e.clientX - r.left) / r.width) * W - L) / (W - L - R)) * span)
        setHover(Math.max(0, Math.min(lastIndex, d)))
    }

    return (
        <>
            <div className="curve-readout">
                <div><small>{i + 1} de {monthLabel}</small><b>{brl(cur[i])}</b></div>
                {diff !== null && (
                    <div><small>{prevLabel} no mesmo dia</small>
                        <span>{brl(prev[i])} <em className={diff > 0 ? 'expense' : 'income'}>{brl(diff, { signed: true })}</em></span></div>
                )}
                {budgetCents > 0 && (
                    <div><small>Do orçamento</small><span>{pct((cur[i] / budgetCents) * 100, 0)} usado · dia {i + 1} de {daily.length}</span></div>
                )}
            </div>
            <svg viewBox={`0 0 ${W} ${H}`} className="curve" onPointerMove={onMove} onPointerLeave={() => setHover(null)}
                 role="img" aria-label={`Gasto acumulado até o dia ${lastIndex + 1}: ${brl(cur[lastIndex])}${prev[lastIndex] !== undefined ? `; ${prevLabel} no mesmo dia: ${brl(prev[lastIndex])}` : ''}${budgetCents > 0 ? `; orçamento ${brl(budgetCents)}` : ''}.`}>
                {[0, 1, 2, 3].map((k) => {
                    const v = (max / 3) * k
                    return (
                        <g key={k}><line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="curve-grid" />
                            <text x={L - 8} y={y(v)} textAnchor="end" dominantBaseline="middle">{axisLabel(v)}</text></g>
                    )
                })}
                {[1, 5, 10, 15, 20, 25, daily.length].map((d) => <text key={d} x={x(d - 1)} y={H - 6} textAnchor="middle">{d}</text>)}
                {budgetCents > 0 && (
                    <>
                        <line x1={L} x2={W - R} y1={y(budgetCents)} y2={y(budgetCents)} className="curve-budget" />
                        <text x={W - R} y={y(budgetCents) - 6} textAnchor="end" className="curve-budget-t">Orçamento {brl(budgetCents)}</text>
                    </>
                )}
                <path d={`${path(cur)}L${x(cur.length - 1)},${y(0)}L${x(0)},${y(0)}Z`} className="curve-area" />
                <path d={path(prev)} className="curve-prev" />
                <path d={path(cur)} className="curve-cur" />
                <line x1={x(i)} x2={x(i)} y1={T} y2={H - B} className="curve-cursor" />
                <circle cx={x(i)} cy={y(cur[i])} r="4.5" className="curve-dot" />
            </svg>
            <div className="curve-legend">
                <span><i className="k-cur" />{monthLabel}</span><span><i className="k-prev" />{prevLabel}</span>
                {budgetCents > 0 && <span><i className="k-budget" />Orçamento</span>}
            </div>
        </>
    )
}

export default SpendCurve
