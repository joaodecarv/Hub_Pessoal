import Money from './Money.jsx'

function FixedVariableBar({ data }){
    const { fixed_cents, variable_cents } = data
    const total = fixed_cents + variable_cents
    if (total === 0) return <p className="note">Nenhuma despesa neste mês.</p>

    const fpct = (fixed_cents / total) * 100
    const vpct = (variable_cents / total) * 100

    return (
        <>
            <div className="fv-bar" aria-hidden="true">
                <div className="fv-seg-fixed" style={{ width: `${fpct}%` }} />
                <div className="fv-seg-var" style={{ width: `${vpct}%` }} />
            </div>
            <div className="fv-legend">
                <div>
                    <div className="fv-k"><span className="legend-dot fv-dot-fixed" />Fixas · {Math.round(fpct)}%</div>
                    <div className="fv-v"><Money cents={fixed_cents} /></div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div className="fv-k"><span className="legend-dot fv-dot-var" />Variáveis · {Math.round(vpct)}%</div>
                    <div className="fv-v"><Money cents={variable_cents} /></div>
                </div>
            </div>
        </>
    )
}

export default FixedVariableBar
