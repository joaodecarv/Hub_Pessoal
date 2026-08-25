function Money({ cents, className }){
    const formatted = (cents / 100).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    })
    return <span className={className}>{formatted}</span>
}

export default Money
