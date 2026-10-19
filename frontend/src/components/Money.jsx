// signed=true prefixes "+" on positives. Negatives always use a real minus (U+2212).
function Money({ cents, className, signed }){
    const formatted = (Math.abs(cents) / 100).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    })
    const sign = cents < 0 ? '−' : (signed && cents > 0 ? '+' : '')
    return <span className={className}>{sign}{formatted}</span>
}

export default Money
