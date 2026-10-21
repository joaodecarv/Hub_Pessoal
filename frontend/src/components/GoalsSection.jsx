import { useState } from 'react'
import { Plus } from 'lucide-react'
import { archiveGoal, deleteGoal } from '../api.js'
import Money from './Money.jsx'
import DateBR from './DateBR.jsx'
import GoalForm from './GoalForm.jsx'

function status(g){
    if (g.achieved) return { text: 'Concluída', cls: 'gb-done' }
    if (g.on_track === false) return { text: 'Atrasada', cls: 'gb-late' }
    if (g.on_track === true) return { text: 'No ritmo', cls: '' }
    return { text: 'Sem prazo', cls: '' }
}

// Roughly how much to put aside per month to reach the target by the deadline.
function monthlyPace(g){
    if (g.achieved || g.days_remaining == null || g.days_remaining <= 0) return null
    const remaining = g.target_cents - g.saved_cents
    return Math.ceil(remaining / Math.max(1, g.days_remaining / 30))
}

function GoalCard({ goal, onChanged }){
    const [editing, setEditing] = useState(false)
    const [confirming, setConfirming] = useState(false)
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)

    if (editing) {
        return <GoalForm goal={goal} onCancel={() => setEditing(false)}
                         onSaved={() => { setEditing(false); onChanged() }} />
    }

    async function run(action){
        setBusy(true)
        setError('')
        try {
            await action()
            onChanged()
        } catch (e) {
            setError(e.message)
            setBusy(false)
        }
    }

    const s = goal.archived ? { text: 'Arquivada', cls: '' } : status(goal)
    const pct = Math.min(100, Math.round((goal.saved_cents / goal.target_cents) * 100))
    const pace = goal.archived ? null : monthlyPace(goal)

    return (
        <article className={`card gb-goal ${s.cls}`}>
            <div className="gb-goal-head">
                <h3 className="gb-goal-name">{goal.name}</h3>
                <span className="gb-goal-status">{s.text}</span>
            </div>
            <div className="gb-bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
                 aria-label={`${goal.name}: ${pct}%`}>
                <div style={{ width: `${pct}%` }} />
            </div>
            <div className="gb-goal-foot">
                <span><Money cents={goal.saved_cents} /> de <Money cents={goal.target_cents} /> · {pct}%</span>
                {goal.deadline && <span>até <DateBR iso={goal.deadline} /></span>}
            </div>
            {pace != null && (
                <p className="gb-goal-note">Para chegar no prazo: <Money cents={pace} />/mês</p>
            )}
            {goal.notes && <p className="gb-goal-note">{goal.notes}</p>}

            {error && <p className="tx-error" role="alert">{error}</p>}

            {confirming ? (
                <div className="tx-confirm" role="alertdialog" aria-label="Confirmar exclusão">
                    <p>Excluir a meta “{goal.name}”? Os aportes deixam de contar para ela, mas as transações continuam.</p>
                    <div className="tx-actions">
                        <button className="btn tx-danger" disabled={busy} onClick={() => run(() => deleteGoal(goal.id))}>
                            Confirmar exclusão
                        </button>
                        <button className="btn" onClick={() => setConfirming(false)}>Manter</button>
                    </div>
                </div>
            ) : (
                <div className="tx-actions">
                    <button className="btn" onClick={() => setEditing(true)}>Editar</button>
                    <button className="btn" disabled={busy} onClick={() => run(() => archiveGoal(goal.id, !goal.archived))}>
                        {goal.archived ? 'Restaurar' : 'Arquivar'}
                    </button>
                    <button className="btn push" onClick={() => setConfirming(true)}>Excluir</button>
                </div>
            )}
        </article>
    )
}

function GoalsSection({ goals, onChanged }){
    const [creating, setCreating] = useState(false)
    const active = goals.filter((g) => !g.archived)
    const archived = goals.filter((g) => g.archived)

    return (
        <section aria-labelledby="gb-goals-title">
            <div className="gb-section-head">
                <h2 id="gb-goals-title" className="gb-section-title">Metas</h2>
                {!creating && (
                    <button className="btn btn-accent" onClick={() => setCreating(true)}>
                        <Plus size={16} aria-hidden="true" className="gb-plus" /> Nova meta
                    </button>
                )}
            </div>

            {creating && (
                <GoalForm goal={null} onCancel={() => setCreating(false)}
                          onSaved={() => { setCreating(false); onChanged() }} />
            )}

            {active.length === 0 && !creating && <p className="note">Nenhuma meta ativa.</p>}
            <div className="gb-goals">
                {active.map((g) => <GoalCard key={g.id} goal={g} onChanged={onChanged} />)}
            </div>

            {archived.length > 0 && (
                <details className="gb-archived">
                    <summary>Arquivadas ({archived.length})</summary>
                    <div className="gb-goals">
                        {archived.map((g) => <GoalCard key={g.id} goal={g} onChanged={onChanged} />)}
                    </div>
                </details>
            )}
        </section>
    )
}

export default GoalsSection
