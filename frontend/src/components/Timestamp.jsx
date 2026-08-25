import { useState } from 'react'

// Renders an ISO timestamp as a friendly "x min ago" / date label.
// "now" is captured once at mount so render stays pure.
function Timestamp({ iso }){
    const [now] = useState(() => Date.now())
    if (!iso) return <span className="dim">never</span>

    const d = new Date(iso)
    const mins = Math.round((now - d.getTime()) / 60000)

    let label
    if (mins < 1) label = 'just now'
    else if (mins < 60) label = `${mins} min ago`
    else if (mins < 1440) label = `${Math.round(mins / 60)} h ago`
    else label = `${d.toLocaleDateString('pt-BR')} ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`

    return <span>{label}</span>
}

export default Timestamp
