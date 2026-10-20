import { useState, useEffect } from 'react'
import { getSummary, getTrends, getBalances, getGoals, getTopExpenses,
         getDailyExpenses, getCategoryHistory } from './api.js'
import MonthSelector from './components/MonthSelector.jsx'
import KpiStrip from './components/KpiStrip.jsx'
import SpendCurve from './components/SpendCurve.jsx'
import IncomeShare from './components/IncomeShare.jsx'
import MoneyFlow from './components/MoneyFlow.jsx'
import FinanceSheet from './components/FinanceSheet.jsx'
import TopExpenses from './components/TopExpenses.jsx'
import AccountBalances from './components/AccountBalances.jsx'
import Goals from './components/Goals.jsx'
import RecentActivity from './components/RecentActivity.jsx'

const MONTHS_LONG = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
    'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
const prevOf = (y, m) => (m === 1 ? [y - 1, 12] : [y, m - 1])

function BancoDashboard(){
    const now = new Date()
    const [year, setYear] = useState(now.getFullYear())
    const [month, setMonth] = useState(now.getMonth() + 1)
    const [data, setData] = useState(null)
    const [balances, setBalances] = useState([])

    useEffect(() => {
        const [py, pm] = prevOf(year, month)
        Promise.all([
            getSummary(year, month), getTrends(year, month, 6),
            getCategoryHistory(year, month, 6, 'expense'), getCategoryHistory(year, month, 6, 'income'),
            getDailyExpenses(year, month), getDailyExpenses(py, pm),
            getGoals(year, month), getTopExpenses(year, month, 5),
        ]).then(([summary, trend, expenseCategories, incomeCategories, daily, prevDaily, goals, topExpenses]) =>
            setData({ summary, trend, expenseCategories, incomeCategories, daily, prevDaily, goals, topExpenses }))
    }, [year, month])

    // Balances don't depend on the selected month.
    useEffect(() => { getBalances().then(setBalances) }, [])

    const monthLabel = MONTHS_LONG[month - 1]
    const prevLabel = MONTHS_LONG[prevOf(year, month)[1] - 1]
    const isCurrentMonth = year === now.getFullYear() && month === now.getMonth() + 1
    const budgetCents = data ? data.expenseCategories.reduce((a, x) => a + (x.budget_cents ?? 0), 0) : 0

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

            {!data ? <p className="note">Carregando…</p> : (
                <>
                    <KpiStrip summary={data.summary} trend={data.trend} prevLabel={prevLabel} />

                    <div className="dash">
                        <section className="card span-8">
                            <div className="card-head"><h2 className="card-title">Gasto acumulado no mês</h2>
                                <span className="card-caption">Passe o mouse para ver cada dia</span></div>
                            <SpendCurve daily={data.daily} prevDaily={data.prevDaily} budgetCents={budgetCents}
                                        lastIndex={isCurrentMonth ? now.getDate() - 1 : data.daily.length - 1}
                                        monthLabel={monthLabel} prevLabel={prevLabel} />
                        </section>
                        <div className="span-4 stack">
                            <section className="card">
                                <h2 className="card-title">Metas</h2>
                                <Goals goals={data.goals} />
                            </section>
                            <section className="card">
                                <div className="card-head">
                                    <h2 className="card-title">Saldo por conta</h2>
                                    <span className="card-caption">Soma de todas as transações</span>
                                </div>
                                <AccountBalances accounts={balances} />
                            </section>
                        </div>

                        <section className="card span-12">
                            <div className="card-head"><h2 className="card-title">Destino da renda</h2>
                                <span className="card-caption">De cada R$ 100 recebidos em {monthLabel}</span></div>
                            <IncomeShare summary={data.summary} categories={data.expenseCategories} prevLabel={prevLabel} />
                        </section>

                        <section className="card span-12">
                            <div className="card-head"><h2 className="card-title">Para onde foi cada real</h2>
                                <span className="card-caption">Passe o mouse num fluxo para destacá-lo</span></div>
                            <MoneyFlow summary={data.summary} incomeCategories={data.incomeCategories}
                                       expenseCategories={data.expenseCategories} />
                        </section>

                        <section className="card span-12">
                            <FinanceSheet summary={data.summary} trend={data.trend} goals={data.goals}
                                          incomeCategories={data.incomeCategories} expenseCategories={data.expenseCategories} />
                        </section>

                        <section className="card span-7">
                            <h2 className="card-title">Atividade recente</h2>
                            <RecentActivity limit={10} />
                        </section>
                        <section className="card span-5">
                            <h2 className="card-title">Maiores despesas do mês</h2>
                            <TopExpenses items={data.topExpenses} />
                        </section>
                    </div>
                </>
            )}
        </>
    )
}

export default BancoDashboard
