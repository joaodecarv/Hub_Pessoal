import { useState, useEffect } from 'react'
import { getSummary, getCategories } from './api.js'
import Money from './components/Money.jsx'

function BancoDashboard(){
    const [summary, setSummary] = useState(null)
    const [categories, setCategories] = useState([])

    useEffect(() => {
    getSummary().then(setSummary)
    getCategories().then(setCategories)
    }, [])


    if (summary===null){
        return <p> Loading...</p>
    }

    const c = summary.current

    return (
        <div className="dashboard-grid">
            <section>
                <h2>{summary.month}/{summary.year}</h2>
                <p>Income: <Money cents={c.income_cents} /></p>
                <p>Expenses: <Money cents={c.expense_cents} /></p>
                <p>Savings: <Money cents={c.savings_cents} /></p>
                <p>Net: <Money cents={c.net_cents} /></p>

            </section>

            <section>
                <h3>Categories</h3>
                <ul>
                    {categories.map((cat) => (
                        <li key={cat.category_id}>
                            {cat.category_name || "Sem categoria"}: <Money cents={cat.total_cents} />
                        </li>
                    ))}
                </ul>
            </section>

        </div>    
    )
}

export default BancoDashboard
