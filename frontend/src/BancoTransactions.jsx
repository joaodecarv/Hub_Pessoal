import { useState, useEffect } from 'react'
import { getTransactions } from './api.js'
import Money from './components/Money.jsx'
import DateBR from './components/DateBR.jsx'

const kindClass = (kind) =>
    kind === 'income' ? 'income' : kind === 'expense' ? 'expense' : 'savings'

function BancoTransactions(){
    const [transactions, setTransactions] = useState([])

    useEffect(() => {
        getTransactions(100, 0).then(setTransactions)
    }, [])

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Transactions</h1>
                    <p className="page-subtitle">Most recent first</p>
                </div>
            </div>

            <section className="card">
                {transactions.length === 0 ? <p className="note">Loading…</p> : (
                    <ul className="rows">
                        {transactions.map((tx) => (
                            <li key={tx.id}>
                                <span className="row-main">
                                    {tx.description} <span className="row-sub">· <DateBR iso={tx.date} /></span>
                                </span>
                                <Money cents={tx.amount_cents} className={kindClass(tx.kind)} />
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </>
    )
}

export default BancoTransactions
