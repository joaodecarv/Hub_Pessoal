import { useState, useEffect, useCallback } from 'react'
import { getGoalsOverview, getBudgets } from './api.js'
import MonthSelector from './components/MonthSelector.jsx'
import GoalsSection from './components/GoalsSection.jsx'
import BudgetsSection from './components/BudgetsSection.jsx'
import './goalsBudgets.css'

function GoalsBudgets(){
    const now = new Date()
    const [year, setYear] = useState(now.getFullYear())
    const [month, setMonth] = useState(now.getMonth() + 1)
    const [goals, setGoals] = useState(null)
    const [budgets, setBudgets] = useState(null)
    const [error, setError] = useState('')
    const [reloads, setReloads] = useState(0)

    const reload = useCallback(() => setReloads((n) => n + 1), [])

    useEffect(() => {
        let stale = false
        getGoalsOverview()
            .then((g) => { if (!stale) { setGoals(g); setError('') } })
            .catch(() => { if (!stale) setError('Não foi possível carregar as metas.') })
        return () => { stale = true }
    }, [reloads])

    useEffect(() => {
        let stale = false
        getBudgets(year, month)
            .then((b) => { if (!stale) { setBudgets(b); setError('') } })
            .catch(() => { if (!stale) setError('Não foi possível carregar os orçamentos.') })
        return () => { stale = true }
    }, [year, month, reloads])

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Metas &amp; Orçamentos</h1>
                    <p className="page-subtitle">Acompanhe seus objetivos de poupança e os limites de gasto por categoria.</p>
                </div>
            </div>

            {error && <p className="gb-error" role="alert">{error}</p>}

            {goals ? <GoalsSection goals={goals} onChanged={reload} /> : !error && <p className="note">Carregando…</p>}

            <div className="gb-section-head gb-budgets-head">
                <h2 className="gb-section-title">Orçamentos</h2>
                <MonthSelector year={year} month={month} onChange={(y, m) => { setYear(y); setMonth(m) }} />
            </div>
            {budgets && <BudgetsSection rows={budgets} year={year} month={month} onChanged={reload} />}
        </>
    )
}

export default GoalsBudgets
