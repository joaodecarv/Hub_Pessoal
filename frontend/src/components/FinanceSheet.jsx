import { useState } from 'react'
import { num, pct } from '../finance/format.js'
import { shareOfIncome, vsAverage, goalMonthlyNeed } from '../finance/derive.js'
import { MONTHS_PT } from '../months.js'

const last = (x) => x.history_cents[x.history_cents.length - 1]

function UsageBar({ ratio, tone }){
    return (
        <span className={`sheet-bar ${ratio > 1 ? 'is-over' : ''} ${tone ?? ''}`} aria-hidden="true">
            <span style={{ width: `${Math.min(ratio, 1) * 100}%` }} />
        </span>
    )
}

function Mini({ values }){
    const max = Math.max(...values) || 1
    return (
        <span className="sheet-mini" aria-hidden="true">
            {values.map((v, i) => <span key={i} style={{ height: `${Math.max(v / max, 0.04) * 100}%` }} className={i === values.length - 1 ? 'is-cur' : ''} />)}
        </span>
    )
}

function Pill({ cents }){
    const cls = cents < 0 ? 'is-neg' : cents > 0 ? 'is-pos' : 'is-zero'
    return <span className={`pill ${cls}`}>{num(cents, { signed: true })}</span>
}

function VsAvg({ history, goodUp }){
    const v = vsAverage(history)
    if (v === null) return <span className="row-sub">—</span>
    if (Math.abs(v) < 0.5) return <span className="row-sub">0%</span>
    const good = goodUp ? v > 0 : v < 0
    return <span className={good ? 'income' : 'expense'}>{v > 0 ? '+' : ''}{pct(v, 0)}</span>
}

// Month spreadsheet: income, fixed and variable expenses (budget vs actual) and goals
// (monthly need vs this month's contribution), each as a share of income; plus a
// "last 6 months" view of the same rows.
function FinanceSheet({ summary, trend, incomeCategories, expenseCategories, goals }){
    const [view, setView] = useState('month')
    const c = summary.current
    const share = (cents) => <td className="n row-sub">{pct(shareOfIncome(cents, c.income_cents))}</td>
    const fixed = expenseCategories.filter((x) => x.is_fixed), variable = expenseCategories.filter((x) => !x.is_fixed)
    const sum = (list, f) => list.reduce((a, x) => a + (f(x) ?? 0), 0)

    const expenseGroup = (label, list) => {
        const budget = sum(list, (x) => x.budget_cents), spent = sum(list, last)
        return (
            <tbody key={label}>
                <tr className="sheet-group">
                    <td>{label}</td><td className="n">{budget ? num(budget) : '—'}</td><td className="n">{num(spent)}</td>{share(spent)}
                    <td className="n">{budget ? <Pill cents={budget - spent} /> : null}</td><td /><td /><td />
                </tr>
                {list.map((x) => (
                    <tr key={x.category_name}>
                        <td className="sheet-cat">{x.category_name}</td>
                        <td className="n row-sub">{x.budget_cents === null ? '—' : num(x.budget_cents)}</td>
                        <td className="n">{num(last(x))}</td>
                        {share(last(x))}
                        <td className="n">{x.budget_cents === null ? null : <Pill cents={x.budget_cents - last(x)} />}</td>
                        <td>{x.budget_cents ? <UsageBar ratio={last(x) / x.budget_cents} /> : <span className="row-sub">sem orçamento</span>}</td>
                        <td><Mini values={x.history_cents} /></td>
                        <td className="n"><VsAvg history={x.history_cents} /></td>
                    </tr>
                ))}
            </tbody>
        )
    }

    const needs = goals.map(goalMonthlyNeed)
    const month = (
        <table className="sheet">
            <thead><tr>
                <th>Categoria</th><th className="n">Orçado</th><th className="n">Realizado</th><th className="n">% da renda</th>
                <th className="n">Disponível</th><th>Uso</th><th>6 meses</th><th className="n">vs média</th>
            </tr></thead>
            <tbody>
                <tr className="sheet-group"><td>Receitas</td><td className="n">—</td><td className="n income">{num(c.income_cents)}</td>{share(c.income_cents)}<td /><td /><td /><td /></tr>
                {incomeCategories.map((x) => (
                    <tr key={x.category_name}>
                        <td className="sheet-cat">{x.category_name}</td><td className="n row-sub">—</td>
                        <td className="n income">{num(last(x))}</td>{share(last(x))}<td /><td />
                        <td><Mini values={x.history_cents} /></td>
                        <td className="n"><VsAvg history={x.history_cents} goodUp /></td>
                    </tr>
                ))}
            </tbody>
            {expenseGroup('Despesas fixas', fixed)}
            {expenseGroup('Despesas variáveis', variable)}
            {goals.length > 0 && (
                <tbody>
                    <tr className="sheet-group">
                        <td>Metas</td><td className="n">{num(sum(needs, (n) => n))}</td><td className="n savings">{num(c.savings_cents)}</td>{share(c.savings_cents)}
                        <td /><td /><td /><td />
                    </tr>
                    {goals.map((g, i) => (
                        <tr key={g.id}>
                            <td className="sheet-cat">{g.name}<span className="row-sub"> · {g.achieved ? 'concluída' : g.deadline ? `até ${g.deadline.slice(5, 7)}/${g.deadline.slice(2, 4)}` : 'sem prazo'}</span></td>
                            <td className="n row-sub">{needs[i] === null || g.achieved ? '—' : num(needs[i])}</td>
                            <td className="n savings">{num(g.month_contribution_cents)}</td>
                            {share(g.month_contribution_cents)}
                            <td className="n">
                                {g.achieved ? <span className="pill is-pos">Concluída</span>
                                    : needs[i] === null ? null : <Pill cents={g.month_contribution_cents - needs[i]} />}
                            </td>
                            <td><UsageBar ratio={g.saved_cents / g.target_cents} tone={g.achieved ? 'is-income' : g.on_track === false ? 'is-warn' : 'is-save'} /></td>
                            <td className="row-sub">{num(g.saved_cents)} de {num(g.target_cents)}</td>
                            <td />
                        </tr>
                    ))}
                </tbody>
            )}
            <tfoot><tr>
                <td>Resultado do mês</td><td /><td className={`n ${c.net_cents < 0 ? 'expense' : 'income'}`}>{num(c.net_cents)}</td>{share(c.net_cents)}
                <td colSpan="4" className="row-sub">receitas − despesas − guardado</td>
            </tr></tfoot>
        </table>
    )

    const groups = [['Receitas', incomeCategories, 'income'], ['Despesas fixas', fixed], ['Despesas variáveis', variable]]
    const history = (
        <table className="sheet">
            <thead><tr><th>Categoria</th>{trend.map((t) => <th key={`${t.year}-${t.month}`} className="n">{MONTHS_PT[t.month - 1]}</th>)}<th className="n">Média</th></tr></thead>
            {groups.map(([label, list, cls]) => (
                <tbody key={label}>
                    <tr className="sheet-group"><td>{label}</td>{trend.map((_, i) => <td key={i} className="n">{num(sum(list, (x) => x.history_cents[i]))}</td>)}<td /></tr>
                    {list.map((x) => (
                        <tr key={x.category_name}>
                            <td className="sheet-cat">{x.category_name}</td>
                            {x.history_cents.map((v, i) => <td key={i} className={`n ${cls ?? ''} ${i === x.history_cents.length - 1 ? 'is-cur' : ''}`}>{num(v)}</td>)}
                            <td className="n row-sub">{num(Math.round(x.history_cents.reduce((a, b) => a + b, 0) / x.history_cents.length))}</td>
                        </tr>
                    ))}
                </tbody>
            ))}
            <tfoot>
                <tr><td>Guardado</td>{trend.map((t, i) => <td key={i} className="n savings">{num(t.savings_cents)}</td>)}<td /></tr>
                <tr><td>Resultado</td>{trend.map((t, i) => <td key={i} className={`n ${t.net_cents < 0 ? 'expense' : 'income'}`}>{num(t.net_cents)}</td>)}<td /></tr>
            </tfoot>
        </table>
    )

    return (
        <>
            <div className="card-head">
                <h2 className="card-title">Planilha do mês</h2>
                <div className="seg">
                    <button className={view === 'month' ? 'is-on' : ''} aria-pressed={view === 'month'} onClick={() => setView('month')}>Mês</button>
                    <button className={view === 'history' ? 'is-on' : ''} aria-pressed={view === 'history'} onClick={() => setView('history')}>Últimos 6 meses</button>
                </div>
                <span className="card-caption push">Valores em R$</span>
            </div>
            <div className="sheet-scroll">{view === 'month' ? month : history}</div>
        </>
    )
}

export default FinanceSheet
