import { useState } from 'react'

// Renders an ISO timestamp as a legível ("há x min" / data).
// "now" is captured once at mount so render stays pure.
function Timestamp({ iso }){
    const [now] = useState(() => Date.now())
    if (!iso) return <span className="dim">nunca</span>

    const d = new Date(iso)
    const mins = Math.round((now - d.getTime()) / 60000)

    let label
    if (mins < 1) label = 'agora mesmo'
    else if (mins < 60) label = `há ${mins} min`
    else if (mins < 1440) label = `há ${Math.round(mins / 60)} h`
    else label = `${d.toLocaleDateString('pt-BR')} ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`

    return <span>{label}</span>
}

export default Timestamp
