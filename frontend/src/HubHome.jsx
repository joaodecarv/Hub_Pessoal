import { useState, useEffect } from 'react'
import { getSummary, getDigest } from './api.js'
import Money from './components/Money.jsx'
import Timestamp from './components/Timestamp.jsx'

function digestStatus(d){
    if (d === undefined) return <span className="dim">Loading…</span>
    if (d === null) return <span className="muted">No digest yet</span>
    return <span className="muted">Updated <Timestamp iso={d.updated_at} /></span>
}

function HubHome({ onNavigate }){
    const [summary, setSummary] = useState(null)
    const [ai, setAi] = useState(undefined)
    const [fin, setFin] = useState(undefined)

    useEffect(() => {
        getSummary().then(setSummary)
        getDigest('ai').then(setAi)
        getDigest('finance').then(setFin)
    }, [])

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Hub Pessoal</h1>
                    <p className="page-subtitle">Your finances and news in one place</p>
                </div>
            </div>

            <div className="home-grid">
                <button className="entry" onClick={() => onNavigate('dashboard')}>
                    <span className="entry-icon">▦</span>
                    <span className="entry-name">Finances</span>
                    <span className="dim">Net this month →</span>
                    {summary
                        ? <span className="entry-big"><Money cents={summary.current.net_cents} /></span>
                        : <span className="dim">Loading…</span>}
                </button>

                <button className="entry" onClick={() => onNavigate('ai')}>
                    <span className="entry-icon">✦</span>
                    <span className="entry-name">AI News</span>
                    {digestStatus(ai)}
                    <span className="dim" style={{ marginTop: 'auto' }}>Open digest →</span>
                </button>

                <button className="entry" onClick={() => onNavigate('finance')}>
                    <span className="entry-icon">$</span>
                    <span className="entry-name">Finance News</span>
                    {digestStatus(fin)}
                    <span className="dim" style={{ marginTop: 'auto' }}>Open digest →</span>
                </button>
            </div>
        </>
    )
}

export default HubHome
