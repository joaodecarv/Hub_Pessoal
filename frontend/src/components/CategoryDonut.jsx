import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { CHART_COLORS } from '../chartTheme.js'

const fmtBRL = (v) => (v / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

function CategoryDonut({ categories }){
    if (!categories.length) return <p className="note">No expenses this month.</p>

    const data = categories.map((c) => ({
        name: c.category_name || 'Sem categoria',
        value: c.total_cents,
    }))
    const total = data.reduce((s, d) => s + d.value, 0)

    return (
        <>
            <div className="chart-box">
                <ResponsiveContainer>
                    <PieChart>
                        <Pie data={data} dataKey="value" nameKey="name"
                             innerRadius="58%" outerRadius="82%" paddingAngle={2} stroke="none">
                            {data.map((_, i) => (
                                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip formatter={(v) => fmtBRL(v)} />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <div className="legend">
                {data.map((d, i) => (
                    <span className="legend-item" key={i}>
                        <span className="legend-dot" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                        {d.name} · {Math.round((d.value / total) * 100)}%
                    </span>
                ))}
            </div>
        </>
    )
}

export default CategoryDonut
