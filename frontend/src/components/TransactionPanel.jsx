import { useState, useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { createTransaction, updateTransaction, deleteTransaction } from '../api.js'
import { parseMoneyToCents, centsToInput } from '../finance/moneyInput.js'
import '../transactions.css'

const KINDS = [
    { value: 'expense', label: 'Despesa' },
    { value: 'income', label: 'Receita' },
    { value: 'savings', label: 'Poupança' },
]

const todayISO = () => {
    const d = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// Fixed/variable is stored as true / false / null (inherit from the category).
const FIXED_TO_VALUE = { true: 'fixed', false: 'variable' }
const VALUE_TO_FIXED = { fixed: true, variable: false, inherit: null }

function initialForm(tx, options){
    if (tx) return {
        kind: tx.kind,
        amount: centsToInput(tx.amount_cents),
        date: tx.date,
        description: tx.description,
        accountId: String(tx.account_id),
        categoryId: tx.category_id ? String(tx.category_id) : '',
        fixed: FIXED_TO_VALUE[tx.is_fixed_override] ?? 'inherit',
        goalId: tx.goal_id ? String(tx.goal_id) : '',
        notes: tx.notes,
    }
    return {
        kind: 'expense', amount: '', date: todayISO(), description: '',
        accountId: options.accounts[0] ? String(options.accounts[0].id) : '',
        categoryId: '', fixed: 'inherit', goalId: '', notes: '',
    }
}

// Side panel to create (tx = null) or edit/delete a transaction.
// onSaved runs after a successful save or delete so the caller can reload.
function TransactionPanel({ tx, options, onClose, onSaved }){
    const [form, setForm] = useState(() => initialForm(tx, options))
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const [confirmingDelete, setConfirmingDelete] = useState(false)
    const panelRef = useRef(null)
    const isEdit = Boolean(tx)

    useEffect(() => {
        panelRef.current?.querySelector('input, select')?.focus()
        const onKey = (e) => {
            if (e.key === 'Escape') onClose()
            if (e.key !== 'Tab') return
            // Keep Tab inside the panel while it is open.
            const focusable = panelRef.current.querySelectorAll('button, input, select, textarea')
            const first = focusable[0]
            const last = focusable[focusable.length - 1]
            if (e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus() }
            else if (!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus() }
        }
        document.addEventListener('keydown', onKey)
        return () => document.removeEventListener('keydown', onKey)
    }, [onClose])

    const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

    function changeKind(kind){
        setForm((f) => {
            const category = options.categories.find((c) => String(c.id) === f.categoryId)
            return {
                ...f, kind,
                categoryId: category && category.kind === kind ? f.categoryId : '',
                fixed: kind === 'expense' ? f.fixed : 'inherit',
                goalId: kind === 'savings' ? f.goalId : '',
            }
        })
    }

    async function run(action){
        setBusy(true)
        setError('')
        try {
            await action()
            onSaved()
        } catch (e) {
            setError(e.message)
            setBusy(false)
        }
    }

    function save(e){
        e.preventDefault()
        const cents = parseMoneyToCents(form.amount)
        if (!cents) { setError('Informe um valor maior que zero, por exemplo 1.234,56'); return }
        const body = {
            date: form.date,
            amount_cents: cents,
            kind: form.kind,
            description: form.description,
            account_id: form.accountId ? Number(form.accountId) : null,
            category_id: form.categoryId ? Number(form.categoryId) : null,
            is_fixed_override: VALUE_TO_FIXED[form.fixed],
            notes: form.notes,
            goal_id: form.goalId ? Number(form.goalId) : null,
        }
        run(() => (isEdit ? updateTransaction(tx.id, body) : createTransaction(body)))
    }

    const categories = options.categories.filter((c) => c.kind === form.kind)
    const goals = options.goals.filter((g) => !g.archived || String(g.id) === form.goalId)

    return (
        <>
            <div className="tx-backdrop" onClick={onClose} />
            <aside className="tx-panel" role="dialog" aria-modal="true"
                   aria-labelledby="tx-panel-title" ref={panelRef}>
                <div className="tx-panel-head">
                    <h2 id="tx-panel-title" className="card-title">{isEdit ? 'Editar transação' : 'Nova transação'}</h2>
                    <button type="button" className="tx-icon-btn" onClick={onClose} aria-label="Fechar painel">
                        <X size={18} aria-hidden="true" />
                    </button>
                </div>

                <form className="tx-form" onSubmit={save}>
                    <div className="seg tx-kind" role="group" aria-label="Tipo">
                        {KINDS.map((k) => (
                            <button key={k.value} type="button" className={form.kind === k.value ? 'is-on' : ''}
                                    aria-pressed={form.kind === k.value} onClick={() => changeKind(k.value)}>
                                {k.label}
                            </button>
                        ))}
                    </div>

                    <div className="tx-row">
                        <label className="tx-field">Valor
                            <input className="tx-input" inputMode="decimal" placeholder="0,00"
                                   value={form.amount} onChange={set('amount')} />
                        </label>
                        <label className="tx-field">Data
                            <input className="tx-input" type="date" value={form.date} onChange={set('date')} />
                        </label>
                    </div>

                    <label className="tx-field">Descrição
                        <input className="tx-input" value={form.description} onChange={set('description')} />
                    </label>

                    <label className="tx-field">Conta
                        <select className="tx-input" value={form.accountId} onChange={set('accountId')}>
                            <option value="">Selecione…</option>
                            {options.accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                        </select>
                    </label>

                    <label className="tx-field">Categoria
                        <select className="tx-input" value={form.categoryId} onChange={set('categoryId')}>
                            <option value="">Sem categoria</option>
                            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                    </label>

                    {form.kind === 'expense' && (
                        <label className="tx-field">Fixa ou variável
                            <select className="tx-input" value={form.fixed} onChange={set('fixed')}>
                                <option value="inherit">Herdar da categoria</option>
                                <option value="fixed">Fixa</option>
                                <option value="variable">Variável</option>
                            </select>
                        </label>
                    )}

                    {form.kind === 'savings' && (
                        <label className="tx-field">Conta para a meta
                            <select className="tx-input" value={form.goalId} onChange={set('goalId')}>
                                <option value="">Nenhuma</option>
                                {goals.map((g) => (
                                    <option key={g.id} value={g.id}>{g.name}{g.archived ? ' (arquivada)' : ''}</option>
                                ))}
                            </select>
                        </label>
                    )}

                    <label className="tx-field">Notas
                        <textarea className="tx-input tx-notes" rows={3} value={form.notes} onChange={set('notes')} />
                    </label>

                    {error && <p className="tx-error" role="alert">{error}</p>}

                    <div className="tx-actions">
                        <button type="submit" className="btn btn-accent" disabled={busy}>
                            {busy ? 'Salvando…' : 'Salvar'}
                        </button>
                        <button type="button" className="btn" onClick={onClose}>Cancelar</button>
                        {isEdit && !confirmingDelete && (
                            <button type="button" className="btn push" onClick={() => setConfirmingDelete(true)}>
                                Excluir
                            </button>
                        )}
                    </div>

                    {isEdit && confirmingDelete && (
                        <div className="tx-confirm" role="alertdialog" aria-label="Confirmar exclusão">
                            <p>Excluir esta transação? Isso não pode ser desfeito.</p>
                            <div className="tx-actions">
                                <button type="button" className="btn tx-danger" disabled={busy}
                                        onClick={() => run(() => deleteTransaction(tx.id))}>
                                    Confirmar exclusão
                                </button>
                                <button type="button" className="btn" onClick={() => setConfirmingDelete(false)}>
                                    Manter
                                </button>
                            </div>
                        </div>
                    )}
                </form>
            </aside>
        </>
    )
}

export default TransactionPanel
