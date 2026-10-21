import { useState } from 'react'
import { createGoal, updateGoal } from '../api.js'
import { parseMoneyToCents, centsToInput } from '../finance/moneyInput.js'

// Inline form to create (goal = null) or edit a goal. onSaved runs after a successful save.
function GoalForm({ goal, onCancel, onSaved }){
    const [form, setForm] = useState({
        name: goal?.name ?? '',
        target: goal ? centsToInput(goal.target_cents) : '',
        deadline: goal?.deadline ?? '',
        notes: goal?.notes ?? '',
    })
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)

    const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

    async function save(e){
        e.preventDefault()
        const cents = parseMoneyToCents(form.target)
        if (!cents) { setError('Informe um valor alvo maior que zero, por exemplo 5.000,00'); return }
        const body = { name: form.name, target_cents: cents, deadline: form.deadline || null, notes: form.notes }
        setBusy(true)
        setError('')
        try {
            await (goal ? updateGoal(goal.id, body) : createGoal(body))
            onSaved()
        } catch (err) {
            setError(err.message)
            setBusy(false)
        }
    }

    return (
        <form className="card gb-form" onSubmit={save} aria-label={goal ? 'Editar meta' : 'Nova meta'}>
            <h3 className="card-title">{goal ? 'Editar meta' : 'Nova meta'}</h3>
            <div className="gb-form-grid">
                <label className="tx-field gb-wide">Nome
                    <input className="tx-input" value={form.name} onChange={set('name')} autoFocus />
                </label>
                <label className="tx-field">Valor alvo
                    <input className="tx-input" inputMode="decimal" placeholder="0,00"
                           value={form.target} onChange={set('target')} />
                </label>
                <label className="tx-field">Prazo (opcional)
                    <input className="tx-input" type="date" value={form.deadline} onChange={set('deadline')} />
                </label>
                <label className="tx-field gb-wide">Notas
                    <textarea className="tx-input gb-notes" rows={2} value={form.notes} onChange={set('notes')} />
                </label>
            </div>
            {error && <p className="tx-error" role="alert">{error}</p>}
            <div className="tx-actions">
                <button type="submit" className="btn btn-accent" disabled={busy}>{busy ? 'Salvando…' : 'Salvar'}</button>
                <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
            </div>
        </form>
    )
}

export default GoalForm
