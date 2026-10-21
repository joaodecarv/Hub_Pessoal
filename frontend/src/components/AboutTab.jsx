import { useState, useEffect } from 'react'
import { getAppVersion } from '../api.js'

function AboutTab(){
    const [version, setVersion] = useState(null)

    useEffect(() => {
        getAppVersion().then((v) => setVersion(v.version)).catch(() => setVersion('desconhecida'))
    }, [])

    return (
        <section className="card">
            <p style={{ margin: 0 }}><strong>Hub Pessoal</strong></p>
            <p className="dim">Versão {version ?? '…'}</p>
        </section>
    )
}

export default AboutTab
