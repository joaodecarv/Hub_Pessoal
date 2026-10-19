import Money from './Money.jsx'
import DateBR from './DateBR.jsx'

function status(g){
    if (g.achieved) return { text: 'Concluída', cls: 'goal-done' }
    if (g.on_track === false) return { text: 'Atrasada', cls: 'goal-late' }
    if (g.on_track === true) return { text: 'No ritmo', cls: '' }
    return { text: 'Sem prazo', cls: '' }
}

function Goals({ goals }){
    if (!goals.length) return <p className="note">Nenhuma meta ativa.</p>

    return (
        <ul className="goals">
            {goals.map((g) => {
                const s = status(g)
                const pct = Math.min(100, Math.round((g.saved_cents / g.target_cents) * 100))
                return (
                    <li key={g.id} className={s.cls}>
                        <div className="goal-head">
                            <span className="row-main">{g.name}</span>
                            <span className="goal-status">{s.text}</span>
                        </div>
                        <div className="goal-bar" role="progressbar" aria-valuenow={pct}
                             aria-valuemin={0} aria-valuemax={100} aria-label={`${g.name}: ${pct}%`}>
                            <div style={{ width: `${pct}%` }} />
                        </div>
                        <div className="goal-foot row-sub">
                            <span><Money cents={g.saved_cents} /> de <Money cents={g.target_cents} /> · {pct}%</span>
                            {g.deadline && <span>até <DateBR iso={g.deadline} /></span>}
                        </div>
                    </li>
                )
            })}
        </ul>
    )
}

export default Goals
