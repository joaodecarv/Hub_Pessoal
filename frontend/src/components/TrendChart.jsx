import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'
import { AXIS, GRID, BAR, BAR_SELECTED } from '../chartTheme.js'
import { MONTHS_PT } from '../months.js'

const fmtBRL = (v) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// The last bar is the selected month (the trend window ends there), so it is the highlighted one.
function TrendChart({ trend }){
    if (!trend.length) return <p className="note">Sem dados.</p>

    const data = trend.map((t) => ({
        label: MONTHS_PT[t.month - 1],
        expense: t.expense_cents / 100,
    }))
    const summary = data.map((d) => `${d.label}: ${fmtBRL(d.expense)}`).join('; ')

    return (
        <div className="chart-box">
            <p className="sr-only">Despesas por mês — {summary}</p>
            <ResponsiveContainer>
                <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }} aria-hidden="true">
                    <CartesianGrid vertical={false} stroke={GRID} />
                    <XAxis dataKey="label" tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis width={48} tick={{ fill: AXIS, fontSize: 11 }} axisLine={false} tickLine={false}
                           tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : v)} />
                    <Tooltip formatter={(v) => [fmtBRL(v), 'Despesas']} cursor={{ fill: 'var(--surface-2)' }} />
                    <Bar dataKey="expense" radius={[4, 4, 0, 0]} maxBarSize={40}>
                        {data.map((_, i) => (
                            <Cell key={i} fill={i === data.length - 1 ? BAR_SELECTED : BAR} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}

export default TrendChart
