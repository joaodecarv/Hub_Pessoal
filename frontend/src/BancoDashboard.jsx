import { useState, useEffect } from 'react'
import { getSummary, getCategories, getTrends, getFixedVariable,
         getBalances, getGoals, getTopExpenses } from './api.js'
import { MONTHS_PT } from './months.js'
import MonthSelector from './components/MonthSelector.jsx'
import StatCard from './components/StatCard.jsx'
import CategoryDonut from './components/CategoryDonut.jsx'
import TrendChart from './components/TrendChart.jsx'
import FixedVariableBar from './components/FixedVariableBar.jsx'
import TopExpenses from './components/TopExpenses.jsx'
import AccountBalances from './components/AccountBalances.jsx'
import Goals from './components/Goals.jsx'
import RecentActivity from './components/RecentActivity.jsx'

const fmtBRL = (cents) => {
    const s = (Math.abs(cents) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    return cents < 0 ? `−${s}` : s
}
// Savings rate in percent of income; null when there was no income to save from.
const savingsRate = (t) => (t.income_cents ? (t.savings_cents / t.income_cents) * 100 : null)
const fmtPct = (v) => (v === null ? '—' : `${v.toFixed(1).replace('.', ',')}%`)
const fmtPts = (v) => `${v.toFixed(1).replace('.', ',')} p.p.`

function BancoDashboard(){
    const now = new Date()
    const [year, setYear] = useState(now.getFullYear())
    const [month, setMonth] = useState(now.getMonth() + 1)

    const [summary, setSummary] = useState(null)
    const [categories, setCategories] = useState([])
    const [trend, setTrend] = useState([])
    const [fixedVar, setFixedVar] = useState(null)
    const [topExpenses, setTopExpenses] = useState([])
    const [balances, setBalances] = useState([])
    const [goals, setGoals] = useState([])

    useEffect(() => {
        getSummary(year, month).then(setSummary)
        getCategories(year, month).then(setCategories)
        getTrends(year, month, 6).then(setTrend)
        getFixedVariable(year, month).then(setFixedVar)
        getTopExpenses(year, month, 5).then(setTopExpenses)
    }, [year, month])

    // Balances and goals don't depend on the selected month.
    useEffect(() => {
        getBalances().then(setBalances)
        getGoals().then(setGoals)
    }, [])

    const c = summary?.current
    const p = summary?.previous
    const prevLabel = MONTHS_PT[(month + 10) % 12].toLowerCase()
    const rate = c && savingsRate(c)
    const prevRate = p && savingsRate(p)

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Minhas finanças</h1>
                    <p className="page-subtitle">Visão somente leitura dos dados do Banco</p>
                </div>
                <MonthSelector year={year} month={month}
                               onChange={(y, m) => { setYear(y); setMonth(m) }} />
            </div>

            {!summary ? <p className="note">Carregando…</p> : (
                <div className="dash">
                    <div className="span-3 span-md-6">
                        <StatCard label="Saldo do mês" value={c.net_cents} format={fmtBRL} large
                                  delta={c.net_cents - p.net_cents} prevLabel={prevLabel} />
                    </div>
                    <div className="span-3 span-md-6">
                        <StatCard label="Receitas" value={c.income_cents} format={fmtBRL} valueClass="income"
                                  delta={c.income_cents - p.income_cents} prevLabel={prevLabel} />
                    </div>
                    <div className="span-3 span-md-6">
                        <StatCard label="Despesas" value={c.expense_cents} format={fmtBRL} valueClass="expense"
                                  delta={c.expense_cents - p.expense_cents} invertDelta prevLabel={prevLabel} />
                    </div>
                    <div className="span-3 span-md-6">
                        <StatCard label="Taxa de poupança" value={rate} format={fmtPct} formatDelta={fmtPts}
                                  delta={rate !== null && prevRate !== null ? rate - prevRate : null}
                                  prevLabel={prevLabel} />
                    </div>

                    <section className="card span-7">
                        <h2 className="card-title">Despesas nos últimos 6 meses</h2>
                        <TrendChart trend={trend} />
                    </section>
                    <section className="card span-5">
                        <h2 className="card-title">Despesas por categoria</h2>
                        <CategoryDonut categories={categories} />
                    </section>

                    <section className="card span-5">
                        <h2 className="card-title">Fixas vs variáveis</h2>
                        {fixedVar ? <FixedVariableBar data={fixedVar} /> : <p className="note">—</p>}
                    </section>
                    <section className="card span-7">
                        <h2 className="card-title">Maiores despesas do mês</h2>
                        <TopExpenses items={topExpenses} />
                    </section>

                    <section className="card span-6">
                        <div className="card-head">
                            <h2 className="card-title">Saldo por conta</h2>
                            <span className="card-caption">Soma de todas as transações</span>
                        </div>
                        <AccountBalances accounts={balances} />
                    </section>
                    <section className="card span-6">
                        <h2 className="card-title">Metas</h2>
                        <Goals goals={goals} />
                    </section>

                    <section className="card span-12">
                        <h2 className="card-title">Atividade recente</h2>
                        <RecentActivity />
                    </section>
                </div>
            )}
        </>
    )
}

export default BancoDashboard
