import { useState } from 'react'
import HubHome from './HubHome.jsx'
import BancoDashboard from './BancoDashboard.jsx'
import BancoTransactions from './BancoTransactions.jsx'
import NewsPage from './NewsPage.jsx'

const NAV = [
    { id: 'home', label: 'Home', icon: '◇' },
    { id: 'dashboard', label: 'Dashboard', icon: '▦' },
    { id: 'transactions', label: 'Transactions', icon: '≣' },
    { id: 'ai', label: 'AI News', icon: '✦' },
    { id: 'finance', label: 'Finance News', icon: '$' },
]

function App(){
    const [page, setPage] = useState('home')

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="brand">
                    <span className="brand-mark" /> Hub Pessoal
                </div>
                <nav className="nav">
                    {NAV.map((item) => (
                        <button key={item.id}
                                className={`nav-item${page === item.id ? ' is-active' : ''}`}
                                onClick={() => setPage(item.id)}>
                            <span className="nav-icon">{item.icon}</span>
                            <span className="nav-label">{item.label}</span>
                        </button>
                    ))}
                </nav>
            </aside>

            <main className="content">
                {page === 'home' && <HubHome onNavigate={setPage} />}
                {page === 'dashboard' && <BancoDashboard />}
                {page === 'transactions' && <BancoTransactions />}
                {page === 'ai' && <NewsPage topic="ai" />}
                {page === 'finance' && <NewsPage topic="finance" />}
            </main>
        </div>
    )
}

export default App
