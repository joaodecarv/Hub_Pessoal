import { brl, pct, pp } from '../finance/format.js'
import { shareOfIncome } from '../finance/derive.js'

// Six-month line with the selected month marked by a dot.
function Spark({ values }){
    const w = 72, h = 22
    const max = Math.max(...values), min = Math.min(...values)
    const x = (i) => (i / Math.max(values.length - 1, 1)) * (w - 4) + 2
    const y = (v) => h - 3 - ((v - min) / (max - min || 1)) * (h - 6)
    const last = values.length - 1
    return (
        <svg width={w} height={h} className="kpi-spark" aria-hidden="true">
            <path d={values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('')} />
            <circle cx={x(last)} cy={y(values[last])} r="2.5" />
        </svg>
    )
}

function Delta({ value, invert, format, prevLabel }){
    if (value === null) return <span className="kpi-delta">—</span>
    if (Math.abs(value) < 0.005) return <span className="kpi-delta">sem variação vs {prevLabel}</span>
    const good = invert ? value < 0 : value > 0
    return (
        <span className={`kpi-delta ${good ? 'income' : 'expense'}`}>
            {value > 0 ? '▲' : '▼'} {format(Math.abs(value))} <span className="row-sub">vs {prevLabel}</span>
        </span>
    )
}

// Saldo, receitas, despesas and savings rate for the month, each against the previous month.
function KpiStrip({ summary, trend, prevLabel }){
    const c = summary.current, p = summary.previous
    const rate = (t) => shareOfIncome(t.savings_cents, t.income_cents)
    const rateDelta = rate(c) !== null && rate(p) !== null ? rate(c) - rate(p) : null
    const items = [
        { label: 'Saldo do mês', value: brl(c.net_cents), delta: c.net_cents - p.net_cents, format: brl, series: trend.map((t) => t.net_cents) },
        { label: 'Receitas', value: brl(c.income_cents), delta: c.income_cents - p.income_cents, format: brl, series: trend.map((t) => t.income_cents) },
        { label: 'Despesas', value: brl(c.expense_cents), delta: c.expense_cents - p.expense_cents, format: brl, invert: true, series: trend.map((t) => t.expense_cents) },
        { label: 'Taxa de poupança', value: pct(rate(c)), delta: rateDelta, format: pp, series: trend.map((t) => rate(t) ?? 0) },
    ]
    return (
        <div className="kpis">
            {items.map((k) => (
                <div key={k.label} className="kpi">
                    <div className="kpi-label">{k.label}</div>
                    <div className="kpi-row"><span className="kpi-value">{k.value}</span><Spark values={k.series} /></div>
                    <Delta value={k.delta} invert={k.invert} format={k.format} prevLabel={prevLabel} />
                </div>
            ))}
        </div>
    )
}

export default KpiStrip
