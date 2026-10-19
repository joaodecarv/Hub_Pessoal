import Money from './Money.jsx'
import DateBR from './DateBR.jsx'

function TopExpenses({ items }){
    if (!items.length) return <p className="note">Nenhuma despesa neste mês.</p>

    return (
        <ol className="rows">
            {items.map((tx, i) => (
                <li key={tx.id}>
                    <span className="row-main">
                        <span className="row-rank">{i + 1}</span>
                        {tx.description} <span className="row-sub">· <DateBR iso={tx.date} /></span>
                    </span>
                    <Money cents={-tx.amount_cents} className="expense" />
                </li>
            ))}
        </ol>
    )
}

export default TopExpenses
