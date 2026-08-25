function Money ({cents}){
    const reais = cents / 100
    const formatted = reais.toLocaleString('pt-BR',{
        style: 'currency',
        currency: 'BRL'
    })
    return <span>{formatted}</span>
}



export default Money