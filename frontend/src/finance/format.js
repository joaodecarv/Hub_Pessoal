// Display formatting shared by the finance widgets. Negatives use a real minus (U+2212).

export function brl(cents, { signed = false } = {}){
    const s = (Math.abs(cents) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    return (cents < 0 ? '−' : signed && cents > 0 ? '+' : '') + s
}

// Plain number with 2 decimals, for table cells under a "Valores em R$" caption.
export function num(cents, { signed = false } = {}){
    const s = (Math.abs(cents) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    return (cents < 0 ? '−' : signed && cents > 0 ? '+' : '') + s
}

export function pct(v, digits = 1){
    return v === null ? '—' : `${v < 0 ? '−' : ''}${Math.abs(v).toFixed(digits).replace('.', ',')}%`
}

// Percentage points, for changes of a share (25% -> 30% is "5,0 p.p.", not "5%").
export function pp(v){
    return `${Math.abs(v).toFixed(1).replace('.', ',')} p.p.`
}
