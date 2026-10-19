import { ChevronLeft, ChevronRight } from 'lucide-react'
import { MONTHS_PT } from '../months.js'

function MonthSelector({ year, month, onChange }){
    function shift(delta){
        let m = month + delta
        let y = year
        if (m < 1){ m = 12; y -= 1 }
        if (m > 12){ m = 1; y += 1 }
        onChange(y, m)
    }

    return (
        <div className="month-select">
            <button onClick={() => shift(-1)} aria-label="Mês anterior"><ChevronLeft size={18} aria-hidden="true" /></button>
            <span className="ms-label" aria-live="polite">{MONTHS_PT[month - 1]} / {year}</span>
            <button onClick={() => shift(1)} aria-label="Próximo mês"><ChevronRight size={18} aria-hidden="true" /></button>
        </div>
    )
}

export default MonthSelector
