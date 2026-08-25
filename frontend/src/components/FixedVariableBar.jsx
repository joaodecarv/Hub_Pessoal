import Money from './Money.jsx'

function FixedVariableBar({ data }){
    const { fixed_cents, variable_cents } = data
    const total = fixed_cents + variable_cents
    const fpct = total ? (fixed_cents / total) * 100 : 0
    const vpct = total ? (variable_cents / total) * 100 : 0

    if (total === 0) return <p className="note">No expenses this month.</p>

    return (
        <>
            <div className="fv-bar">
                <div className="fv-seg-fixed" style={{ width: `${fpct}%` }} />
                <div className="fv-seg-var" style={{ width: `${vpct}%` }} />
            </div>
            <div className="fv-legend">
                <div>
                    <div className="fv-k">Fixed · {Math.round(fpct)}%</div>
                    <div className="fv-v"><Money cents={fixed_cents} /></div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div className="fv-k">Variable · {Math.round(vpct)}%</div>
                    <div className="fv-v"><Money cents={variable_cents} /></div>
                </div>
            </div>
        </>
    )
}

export default FixedVariableBar
