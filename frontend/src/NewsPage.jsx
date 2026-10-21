import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { getDigest, refreshDigest, getGeminiStatus } from './api.js'
import Timestamp from './components/Timestamp.jsx'

const TOPICS = [
    { id: 'ai', label: 'IA' },
    { id: 'finance', label: 'Finanças' },
]
const SUBS = {
    ai: 'Resumo do setor de IA · em inglês',
    finance: 'Notícias do mercado · em português',
}

function NewsPage({ topic, onTopic, onNavigate }){
    const [digest, setDigest] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [hasKey, setHasKey] = useState(true)

    useEffect(() => {
        getDigest(topic).then(setDigest)
        getGeminiStatus().then((s) => setHasKey(s.configured)).catch(() => {})
    }, [topic])

    function handleRefresh(){
        setLoading(true)
        setError('')
        refreshDigest(topic)
            .then(setDigest)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false))
    }

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Notícias</h1>
                    <p className="page-subtitle">{SUBS[topic]}</p>
                </div>
                <button className="btn btn-accent" onClick={handleRefresh} disabled={loading || !hasKey}>
                    {loading ? 'Atualizando…' : 'Atualizar'}
                </button>
            </div>

            <div className="seg cfg-tabs" role="group" aria-label="Assunto">
                {TOPICS.map((t) => (
                    <button key={t.id} className={topic === t.id ? 'is-on' : ''} aria-pressed={topic === t.id}
                            onClick={() => onTopic(t.id)}>
                        {t.label}
                    </button>
                ))}
            </div>

            {!hasKey && (
                <section className="card news-key">
                    <p style={{ margin: 0 }}>Para gerar resumos, cadastre sua chave do Gemini.</p>
                    <button className="btn btn-accent" onClick={() => onNavigate('settings', 'gemini')}>
                        Configurar chave
                    </button>
                </section>
            )}

            {error && hasKey && <p className="tx-error" role="alert">{error}</p>}

            <section className="card">
                {digest === null ? (
                    <p className="note">Nenhum resumo ainda. Clique em Atualizar para gerar um.</p>
                ) : (
                    <>
                        <p className="dim" style={{ marginTop: 0 }}>
                            Atualizado <Timestamp iso={digest.updated_at} />
                        </p>
                        <div className="digest">
                            <ReactMarkdown>{digest.markdown}</ReactMarkdown>
                        </div>
                    </>
                )}
            </section>
        </>
    )
}

export default NewsPage
