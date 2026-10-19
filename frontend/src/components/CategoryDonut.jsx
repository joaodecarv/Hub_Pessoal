import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { CHART_COLORS, OTHER, UNCATEGORIZED } from '../chartTheme.js'

const fmtBRL = (v) => (v / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const TOP = 4  // more slices than this are unreadable; the rest fold into "Outros"

function CategoryDonut({ categories }){
    if (!categories.length) return <p className="note">Nenhuma despesa neste mês.</p>

    // Banco returns slices largest first.
    const slices = categories.map((c) => ({
        name: c.category_name || 'Sem categoria',
        value: c.total_cents,
        uncategorized: c.category_id === null,
    }))
    const data = slices.slice(0, TOP)
    const rest = slices.slice(TOP).reduce((s, d) => s + d.value, 0)
    if (rest > 0) data.push({ name: 'Outros', value: rest, other: true })

    let paletteIdx = 0
    for (const d of data){
        d.color = d.other ? OTHER : d.uncategorized ? UNCATEGORIZED : CHART_COLORS[paletteIdx++]
    }
    const total = data.reduce((s, d) => s + d.value, 0)
    const pct = (v) => Math.round((v / total) * 100)

    return (
        <>
            <div className="chart-box">
                <ResponsiveContainer>
                    <PieChart aria-hidden="true">
                        <Pie data={data} dataKey="value" nameKey="name"
                             innerRadius="62%" outerRadius="84%" paddingAngle={data.length > 1 ? 2 : 0} stroke="none">
                            {data.map((d, i) => <Cell key={i} fill={d.color} />)}
                        </Pie>
                        <Tooltip formatter={(v) => fmtBRL(v)} />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <ul className="legend">
                {data.map((d, i) => (
                    <li className="legend-item" key={i}>
                        <span className="legend-dot" style={{ background: d.color }} />
                        <span className="legend-name">{d.name}</span>
                        <span className="legend-val">{pct(d.value)}% · {fmtBRL(d.value)}</span>
                    </li>
                ))}
            </ul>
        </>
    )
}

export default CategoryDonut
