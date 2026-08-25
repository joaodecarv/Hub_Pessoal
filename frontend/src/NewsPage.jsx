import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { getDigest, refreshDigest } from './api.js'
import Timestamp from './components/Timestamp.jsx'

const TITLES = { ai: 'AI News', finance: 'Finance News' }
const SUBS = {
    ai: 'AI-industry digest · English',
    finance: 'Notícias do mercado · Português',
}

function NewsPage({ topic }){
    const [digest, setDigest] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        getDigest(topic).then(setDigest)
    }, [topic])

    function handleRefresh(){
        setLoading(true)
        refreshDigest(topic)
            .then(setDigest)
            .finally(() => setLoading(false))
    }

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">{TITLES[topic]}</h1>
                    <p className="page-subtitle">{SUBS[topic]}</p>
                </div>
                <button className="btn btn-accent" onClick={handleRefresh} disabled={loading}>
                    {loading ? 'Refreshing…' : 'Refresh'}
                </button>
            </div>

            <section className="card">
                {digest === null ? (
                    <p className="note">No digest cached yet. Click Refresh to build one.</p>
                ) : (
                    <>
                        <p className="dim" style={{ marginTop: 0 }}>
                            Updated <Timestamp iso={digest.updated_at} />
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
