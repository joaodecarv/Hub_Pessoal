import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import '../transactions.css'
import '../settings.css'

// Side panel shell for the Configurações forms. Reuses the Transações panel
// styles; the form goes in `children`. Esc closes, Tab stays inside.
function SettingsPanel({ title, onClose, children }){
    const panelRef = useRef(null)

    useEffect(() => {
        panelRef.current?.querySelector('input, select')?.focus()
        const onKey = (e) => {
            if (e.key === 'Escape') onClose()
            if (e.key !== 'Tab') return
            const focusable = panelRef.current.querySelectorAll('button:not(:disabled), input, select, textarea')
            const first = focusable[0]
            const last = focusable[focusable.length - 1]
            if (e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus() }
            else if (!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus() }
        }
        document.addEventListener('keydown', onKey)
        return () => document.removeEventListener('keydown', onKey)
    }, [onClose])

    return (
        <>
            <div className="tx-backdrop" onClick={onClose} />
            <aside className="tx-panel" role="dialog" aria-modal="true"
                   aria-labelledby="settings-panel-title" ref={panelRef}>
                <div className="tx-panel-head">
                    <h2 id="settings-panel-title" className="card-title">{title}</h2>
                    <button type="button" className="tx-icon-btn" onClick={onClose} aria-label="Fechar painel">
                        <X size={18} aria-hidden="true" />
                    </button>
                </div>
                {children}
            </aside>
        </>
    )
}

export default SettingsPanel
