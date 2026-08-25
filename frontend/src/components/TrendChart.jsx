import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'
import { AXIS, GRID, BAR } from '../chartTheme.js'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function TrendChart({ trend }){
    if (!trend.length) return <p className="note">No data.</p>

    const data = trend.map((t) => ({
        label: MONTHS[t.month - 1],
        expense: t.expense_cents / 100,
    }))
    const fmt = (v) => 'R$ ' + v.toLocaleString('pt-BR')

    return (
        <div className="chart-box">
            <ResponsiveContainer>
                <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                    <CartesianGrid vertical={false} stroke={GRID} />
                    <XAxis dataKey="label" tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis width={48} tick={{ fill: AXIS, fontSize: 11 }} axisLine={false} tickLine={false}
                           tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : v)} />
                    <Tooltip formatter={(v) => fmt(v)} cursor={{ fill: 'rgba(197,112,74,.15)' }} />
                    <Bar dataKey="expense" fill={BAR} radius={[6, 6, 0, 0]} maxBarSize={46} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}

export default TrendChart
