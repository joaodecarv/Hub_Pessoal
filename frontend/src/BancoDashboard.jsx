import { useState, useEffect } from 'react'
import { getSummary, getCategories, getTrends, getFixedVariable } from './api.js'
import MonthSelector from './components/MonthSelector.jsx'
import StatCard from './components/StatCard.jsx'
import CategoryDonut from './components/CategoryDonut.jsx'
import TrendChart from './components/TrendChart.jsx'
import FixedVariableBar from './components/FixedVariableBar.jsx'
import RecentActivity from './components/RecentActivity.jsx'

function BancoDashboard(){
    const now = new Date()
    const [year, setYear] = useState(now.getFullYear())
    const [month, setMonth] = useState(now.getMonth() + 1)

    const [summary, setSummary] = useState(null)
    const [categories, setCategories] = useState([])
    const [trend, setTrend] = useState([])
    const [fixedVar, setFixedVar] = useState(null)

    useEffect(() => {
        getSummary(year, month).then(setSummary)
        getCategories(year, month).then(setCategories)
        getTrends(year, month, 6).then(setTrend)
        getFixedVariable(year, month).then(setFixedVar)
    }, [year, month])

    const c = summary?.current
    const p = summary?.previous

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Minhas Finanças</h1>
                    <p className="page-subtitle">Read-only view of your Banco data</p>
                </div>
                <MonthSelector year={year} month={month}
                               onChange={(y, m) => { setYear(y); setMonth(m) }} />
            </div>

            {!summary ? <p className="note">Loading…</p> : (
                <div className="stack">
                    <div className="grid stat-grid">
                        <StatCard label="Income" cents={c.income_cents} valueClass="value-income"
                                  deltaCents={c.income_cents - p.income_cents} />
                        <StatCard label="Expenses" cents={c.expense_cents} valueClass="value-expense"
                                  deltaCents={c.expense_cents - p.expense_cents} invertDelta />
                        <StatCard label="Savings" cents={c.savings_cents} valueClass="value-savings"
                                  deltaCents={c.savings_cents - p.savings_cents} />
                        <StatCard label="Net" cents={c.net_cents}
                                  deltaCents={c.net_cents - p.net_cents} />
                    </div>

                    <div className="grid dash-grid">
                        <section className="card">
                            <h2 className="card-title">Expenses — last 6 months</h2>
                            <TrendChart trend={trend} />
                        </section>
                        <section className="card">
                            <h2 className="card-title">Expenses by category</h2>
                            <CategoryDonut categories={categories} />
                        </section>
                    </div>

                    <div className="grid dash-grid">
                        <section className="card">
                            <h2 className="card-title">Fixed vs Variable</h2>
                            {fixedVar ? <FixedVariableBar data={fixedVar} /> : <p className="note">—</p>}
                        </section>
                        <section className="card">
                            <h2 className="card-title">Recent activity</h2>
                            <RecentActivity />
                        </section>
                    </div>
                </div>
            )}
        </>
    )
}

export default BancoDashboard
