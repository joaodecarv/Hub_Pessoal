// One headline figure with a vs-previous-month delta, colored by meaning:
// invertDelta=true means "up is bad" (Despesas). formatDelta defaults to format.
function StatCard({ label, value, delta, format, formatDelta = format, valueClass, invertDelta, prevLabel, large }){
    let deltaEl = null
    if (delta !== undefined && delta !== null){
        const up = delta > 0
        const good = invertDelta ? !up : up
        const cls = delta === 0 ? '' : good ? 'delta-up' : 'delta-down'
        const arrow = delta === 0 ? '' : up ? '▲ ' : '▼ '
        deltaEl = (
            <span className={`stat-delta ${cls}`}>
                {arrow}{formatDelta(Math.abs(delta))} vs {prevLabel}
            </span>
        )
    }

    return (
        <div className="card stat">
            <span className="stat-label">{label}</span>
            <span className={`stat-value${large ? ' stat-value-lg' : ''} ${valueClass || ''}`}>{format(value)}</span>
            {deltaEl}
        </div>
    )
}

export default StatCard
