import Money from './Money.jsx'

// One headline figure with an optional vs-previous-month delta.
// invertDelta=true means "up is bad" (used for Expenses).
function StatCard({ label, cents, valueClass, deltaCents, invertDelta }){
    let delta = null
    if (deltaCents !== undefined && deltaCents !== null){
        const up = deltaCents > 0
        const good = invertDelta ? !up : up
        const arrow = deltaCents === 0 ? '–' : up ? '↑' : '↓'
        const cls = deltaCents === 0 ? '' : good ? 'delta-up' : 'delta-down'
        delta = (
            <span className={`stat-delta ${cls}`}>
                {arrow} <Money cents={Math.abs(deltaCents)} /> vs last
            </span>
        )
    }

    return (
        <div className="card stat">
            <span className="stat-label">{label}</span>
            <span className={`stat-value ${valueClass || ''}`}><Money cents={cents} /></span>
            {delta}
        </div>
    )
}

export default StatCard
