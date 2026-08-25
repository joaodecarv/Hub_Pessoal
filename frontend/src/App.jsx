import BancoDashboard from "./BancoDashboard.jsx"
import BancoTransactions from "./BancoTransactions.jsx"
import { useState } from 'react'
function App() {

  const [page, setPage] = useState('dashboard')

  return(
    <main>
      <h1>Hub Pessoal</h1>
      <nav>
        <button onClick={() => setPage('dashboard')}>Dashboard</button>
        <button onClick={() => setPage('transactions')}>Transactions</button>

      </nav>

      {page === 'dashboard' ? <BancoDashboard /> : <BancoTransactions />}

    </main>
  )
}

export default App