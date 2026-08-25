import { useState, useEffect } from 'react'
import { getTransactions } from '../api.js'
import Money from './Money.jsx'
import DateBR from './DateBR.jsx'

const kindClass = (kind) =>
    kind === 'income' ? 'income' : kind === 'expense' ? 'expense' : 'savings'

function RecentActivity({ limit = 6 }){
    const [txs, setTxs] = useState([])

    useEffect(() => {
        getTransactions(limit, 0).then(setTxs)
    }, [limit])

    if (!txs.length) return <p className="note">No transactions.</p>

    return (
        <ul className="rows">
            {txs.map((tx) => (
                <li key={tx.id}>
                    <span className="row-main">
                        {tx.description} <span className="row-sub">· <DateBR iso={tx.date} /></span>
                    </span>
                    <Money cents={tx.amount_cents} className={kindClass(tx.kind)} />
                </li>
            ))}
        </ul>
    )
}

export default RecentActivity
