import {useState, useEffect} from 'react'
import { getTransactions } from './api.js'
import Money from './components/Money.jsx'

function BancoTransactions(){
    const [transactions, setTransactions] = useState([])

    useEffect(() => {
        getTransactions().then(setTransactions)
    }, [])

    return (
        <section>
            <h2>Recent Transactions</h2>
            <ul>
                {transactions.map((tx) =>(
                    <li key={tx.id}>
                        {tx.date} - {tx.description} (<Money cents = {tx.amount_cents} />)
                    </li>
                ))}
            </ul>
        </section>
    )
}



export default BancoTransactions