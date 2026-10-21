import { useState } from 'react'
import { setBudget, removeBudget } from '../api.js'
import { parseMoneyToCents, centsToInput } from '../finance/moneyInput.js'
import { MONTHS_PT } from '../months.js'
import Money from './Money.jsx'

function BudgetRow({ row, year, month, onChanged }){
    const [mode, setMode] = useState('view')   // 'view' | 'edit' | 'remove'
    const [text, setText] = useState('')
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)

    const hasBudget = row.budget_cents != null
    const over = hasBudget && row.spent_cents > row.budget_cents
    const pct = hasBudget ? Math.round((row.spent_cents / row.budget_cents) * 100) : 0

    async function run(action){
        setBusy(true)
        setError('')
        try {
            await action()
            setMode('view')
            onChanged()
        } catch (e) {
            setError(e.message)
        }
        setBusy(false)
    }

    function startEdit(){
        setText(hasBudget ? centsToInput(row.budget_cents) : '')
        setError('')
        setMode('edit')
    }

    function save(e){
        e.preventDefault()
        const cents = parseMoneyToCents(text)
        if (!cents) { setError('Informe um limite maior que zero, por exemplo 800,00'); return }
        run(() => setBudget(row.category_id, year, month, cents))
    }

    return (
        <>
        <tr className={over ? 'gb-over' : ''}>
            <td>{row.category_name}</td>
            <td className="n">
                {mode === 'edit' ? (
                    <form className="gb-inline" onSubmit={save}>
                        <input className="tx-input gb-limit-input" inputMode="decimal" placeholder="0,00"
                               aria-label={`Limite de ${row.category_name}`} value={text} autoFocus
                               onChange={(e) => setText(e.target.value)}
                               onKeyDown={(e) => { if (e.key === 'Escape') setMode('view') }} />
                        <button type="submit" className="btn btn-accent" disabled={busy}>Salvar</button>
                        <button type="button" className="btn" onClick={() => setMode('view')}>Cancelar</button>
                    </form>
                ) : (
                    <button className="gb-limit" onClick={startEdit}
                            aria-label={`Editar limite de ${row.category_name}`}>
                        {hasBudget ? <Money cents={row.budget_cents} /> : <span className="gb-set">Definir limite</span>}
                    </button>
                )}
                {error && <p className="tx-error" role="alert">{error}</p>}
            </td>
            <td className="n"><Money cents={row.spent_cents} /></td>
            <td className="gb-use">
                {hasBudget && (
                    <div className="gb-use-cell">
                        <div className="gb-bar" role="progressbar" aria-valuenow={Math.min(pct, 100)}
                             aria-valuemin={0} aria-valuemax={100} aria-label={`${row.category_name}: ${pct}% do limite`}>
                            <div style={{ width: `${Math.min(pct, 100)}%` }} />
                        </div>
                        <span className="gb-pct">{pct}%</span>
                    </div>
                )}
            </td>
            <td className="n gb-avail">
                {hasBudget && (over
                    ? <span className="gb-over-text">Estourou <Money cents={row.spent_cents - row.budget_cents} /></span>
                    : <Money cents={row.budget_cents - row.spent_cents} />)}
            </td>
            <td className="gb-row-actions">
                {hasBudget && mode === 'view' && (
                    <button className="gb-link" onClick={() => setMode('remove')}>Remover</button>
                )}
            </td>
        </tr>
        {mode === 'remove' && (
            <tr className="gb-remove-row">
                <td colSpan={6} role="alertdialog" aria-label="Confirmar remoção">
                    Remover o orçamento de {row.category_name} a partir de {MONTHS_PT[month - 1]}/{year}?
                    <span className="gb-remove-btns">
                        <button className="gb-link tx-danger-text" disabled={busy}
                                onClick={() => run(() => removeBudget(row.category_id, year, month))}>Remover</button>
                        <button className="gb-link" onClick={() => setMode('view')}>Manter</button>
                    </span>
                </td>
            </tr>
        )}
        </>
    )
}

function BudgetsSection({ rows, year, month, onChanged }){
    const budgeted = rows.filter((r) => r.budget_cents != null)
    const totalLimit = budgeted.reduce((sum, r) => sum + r.budget_cents, 0)
    const totalSpent = budgeted.reduce((sum, r) => sum + r.spent_cents, 0)

    return (
        <section className="card gb-budgets">
            <table className="tx-table gb-table">
                <thead>
                    <tr>
                        <th>Categoria</th><th className="n">Limite</th><th className="n">Gasto</th>
                        <th>Uso</th><th className="n">Disponível</th><th><span className="gb-sr">Ações</span></th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((r) => (
                        <BudgetRow key={r.category_id} row={r} year={year} month={month} onChanged={onChanged} />
                    ))}
                </tbody>
                {budgeted.length > 0 && (
                    <tfoot>
                        <tr>
                            <td>Total orçado</td>
                            <td className="n"><Money cents={totalLimit} /></td>
                            <td className="n"><Money cents={totalSpent} /></td>
                            <td />
                            <td className="n">
                                {totalSpent > totalLimit
                                    ? <span className="gb-over-text">Estourou <Money cents={totalSpent - totalLimit} /></span>
                                    : <Money cents={totalLimit - totalSpent} />}
                            </td>
                            <td />
                        </tr>
                    </tfoot>
                )}
            </table>
            <p className="dim gb-hint">
                O limite que você define vale de {MONTHS_PT[month - 1]}/{year} em diante; meses anteriores não mudam.
            </p>
        </section>
    )
}

export default BudgetsSection
