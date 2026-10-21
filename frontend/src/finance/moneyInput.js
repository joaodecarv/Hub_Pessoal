// Money typed by the user ("1.234,56", "12,5", "R$ 10") <-> integer cents.

// Returns integer cents, or null when the text is not a valid amount.
export function parseMoneyToCents(text){
    const cleaned = text.replace(/R\$|\s/g, '')
    if (!/^\d{1,3}(\.\d{3})*(,\d{0,2})?$|^\d+(,\d{0,2})?$/.test(cleaned)) return null
    const [whole, fraction = ''] = cleaned.replace(/\./g, '').split(',')
    return Number(whole) * 100 + Number(fraction.padEnd(2, '0'))
}

// 123456 -> "1.234,56" (the form's initial text when editing).
export function centsToInput(cents){
    return (cents / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
