import { useState } from 'react'
import AccountsTab from './components/AccountsTab.jsx'
import CategoriesTab from './components/CategoriesTab.jsx'
import RulesTab from './components/RulesTab.jsx'
import GeminiTab from './components/GeminiTab.jsx'
import AboutTab from './components/AboutTab.jsx'
import './settings.css'

const TABS = [
    { id: 'accounts', label: 'Contas', Panel: AccountsTab },
    { id: 'categories', label: 'Categorias', Panel: CategoriesTab },
    { id: 'rules', label: 'Regras', Panel: RulesTab },
    { id: 'gemini', label: 'Gemini', Panel: GeminiTab },
    { id: 'about', label: 'Sobre', Panel: AboutTab },
]

function Configuracoes({ initialTab = 'accounts' }){
    const [tab, setTab] = useState(initialTab)
    const { Panel } = TABS.find((t) => t.id === tab)

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Configurações</h1>
                    <p className="page-subtitle">Contas, categorias, regras de categorização, chave do Gemini e informações do app.</p>
                </div>
            </div>

            <div className="seg cfg-tabs" role="group" aria-label="Seção">
                {TABS.map((t) => (
                    <button key={t.id} className={tab === t.id ? 'is-on' : ''} aria-pressed={tab === t.id}
                            onClick={() => setTab(t.id)}>
                        {t.label}
                    </button>
                ))}
            </div>

            <Panel />
        </>
    )
}

export default Configuracoes
