import { useState, useEffect } from 'react'
import { getGeminiStatus, saveGeminiKey } from '../api.js'
import '../transactions.css'
import '../settings.css'

function GeminiTab(){
    const [configured, setConfigured] = useState(null)
    const [key, setKey] = useState('')
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState('')
    const [saved, setSaved] = useState(false)

    useEffect(() => {
        getGeminiStatus().then((s) => setConfigured(s.configured))
                         .catch(() => setError('Não foi possível ler o estado da chave.'))
    }, [])

    async function save(e){
        e.preventDefault()
        setBusy(true); setError(''); setSaved(false)
        try {
            const s = await saveGeminiKey(key)
            setConfigured(s.configured); setKey(''); setSaved(true)
        } catch (err) {
            setError(err.message)
        }
        setBusy(false)
    }

    return (
        <section className="card cfg-gemini">
            <p className="cfg-hint">
                O Gemini gera os resumos de notícias. Cole sua chave da API (obtida no Google AI Studio);
                ela fica salva só neste computador e nunca é exibida de volta.
            </p>
            <p role="status">
                Estado: <strong>{configured === null ? 'verificando…' : configured ? 'chave configurada' : 'chave não configurada'}</strong>
            </p>
            <form className="tx-form" onSubmit={save}>
                <label className="tx-field">{configured ? 'Substituir chave' : 'Chave da API'}
                    <input className="tx-input" type="password" autoComplete="off" value={key}
                           onChange={(e) => setKey(e.target.value)} />
                </label>
                {error && <p className="tx-error" role="alert">{error}</p>}
                {saved && <p className="cfg-hint" role="status">Chave salva.</p>}
                <div className="tx-actions">
                    <button type="submit" className="btn btn-accent" disabled={busy || !key.trim()}>
                        {busy ? 'Salvando…' : 'Salvar chave'}
                    </button>
                </div>
            </form>
        </section>
    )
}

export default GeminiTab
