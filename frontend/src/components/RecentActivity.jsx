import { useState, useEffect } from 'react'
import { getTransactions } from '../api.js'
import Money from './Money.jsx'
import DateBR from './DateBR.jsx'

const KIND_CLASS = { income: 'income', expense: 'expense', savings: 'savings' }

function RecentActivity({ limit = 6 }){
    const [txs, setTxs] = useState([])

    useEffect(() => {
        getTransactions(limit, 0).then(setTxs)
    }, [limit])

    if (!txs.length) return <p className="note">Nenhuma transação.</p>

    return (
        <ul className="rows">
            {txs.map((tx) => (
                <li key={tx.id}>
                    <span className="row-main">
                        {tx.description} <span className="row-sub">· <DateBR iso={tx.date} /></span>
                    </span>
                    <Money cents={tx.kind === 'expense' ? -tx.amount_cents : tx.amount_cents}
                           signed className={KIND_CLASS[tx.kind]} />
                </li>
            ))}
        </ul>
    )
}

export default RecentActivity
