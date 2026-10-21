import { useState, useEffect } from 'react'
import HubHome from './HubHome.jsx'
import BancoDashboard from './BancoDashboard.jsx'
import BancoTransactions from './BancoTransactions.jsx'
import GoalsBudgets from './GoalsBudgets.jsx'
import NewsPage from './NewsPage.jsx'
import Configuracoes from './Configuracoes.jsx'
import ThemeToggle from './components/ThemeToggle.jsx'

const NAV = [
    { id: 'home', label: 'Início', icon: '◇' },
    { id: 'dashboard', label: 'Finanças', icon: '▦' },
    { id: 'transactions', label: 'Transações', icon: '≣' },
    { id: 'goals', label: 'Metas & Orçamentos', icon: '◎' },
    { id: 'news', label: 'Notícias', icon: '✦' },
    { id: 'settings', label: 'Configurações', icon: '⚙' },
]

function App(){
    const [page, setPage] = useState('home')
    const [newsTopic, setNewsTopic] = useState('ai')
    const [settingsTab, setSettingsTab] = useState('accounts')

    useEffect(() => {
        document.title = `${NAV.find((n) => n.id === page).label} · Hub Pessoal`
    }, [page])

    function go(id, extra){
        if (id === 'news' && extra) setNewsTopic(extra)
        if (id === 'settings') setSettingsTab(extra ?? 'accounts')
        setPage(id)
    }

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="brand">
                    <span className="brand-mark" /> Hub Pessoal
                </div>
                <nav className="nav" aria-label="Principal">
                    {NAV.map((item) => (
                        <button key={item.id}
                                className={`nav-item${page === item.id ? ' is-active' : ''}`}
                                onClick={() => go(item.id)}>
                            <span className="nav-icon">{item.icon}</span>
                            <span className="nav-label">{item.label}</span>
                        </button>
                    ))}
                </nav>
                <ThemeToggle />
            </aside>

            <main className="content">
                {page === 'home' && <HubHome onNavigate={go} />}
                {page === 'dashboard' && <BancoDashboard />}
                {page === 'transactions' && <BancoTransactions />}
                {page === 'goals' && <GoalsBudgets />}
                {page === 'news' && <NewsPage key={newsTopic} topic={newsTopic} onTopic={setNewsTopic} onNavigate={go} />}
                {page === 'settings' && <Configuracoes key={settingsTab} initialTab={settingsTab} />}
            </main>
        </div>
    )
}

export default App
