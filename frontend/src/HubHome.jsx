import { useState, useEffect } from 'react'
import { getSummary, getDigest } from './api.js'
import Money from './components/Money.jsx'
import Timestamp from './components/Timestamp.jsx'

function digestStatus(d){
    if (d === undefined) return <span className="dim">Carregando…</span>
    if (d === null) return <span className="muted">Nenhum resumo ainda</span>
    return <span className="muted">Atualizado <Timestamp iso={d.updated_at} /></span>
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
                    <p className="page-subtitle">Suas finanças e notícias em um só lugar</p>
                </div>
            </div>

            <div className="home-grid">
                <button className="entry" onClick={() => onNavigate('dashboard')}>
                    <span className="entry-icon">▦</span>
                    <span className="entry-name">Finanças</span>
                    <span className="dim">Saldo do mês →</span>
                    {summary
                        ? <span className="entry-big"><Money cents={summary.current.net_cents} /></span>
                        : <span className="dim">Carregando…</span>}
                </button>

                <button className="entry" onClick={() => onNavigate('news', 'ai')}>
                    <span className="entry-icon">✦</span>
                    <span className="entry-name">Notícias de IA</span>
                    {digestStatus(ai)}
                    <span className="dim" style={{ marginTop: 'auto' }}>Abrir resumo →</span>
                </button>

                <button className="entry" onClick={() => onNavigate('news', 'finance')}>
                    <span className="entry-icon">$</span>
                    <span className="entry-name">Notícias de Finanças</span>
                    {digestStatus(fin)}
                    <span className="dim" style={{ marginTop: 'auto' }}>Abrir resumo →</span>
                </button>
            </div>
        </>
    )
}

export default HubHome
