import { useState, useEffect, useCallback } from 'react'
import { Plus, Search } from 'lucide-react'
import { listTransactions, getTransactionOptions } from './api.js'
import Money from './components/Money.jsx'
import DateBR from './components/DateBR.jsx'
import MonthSelector from './components/MonthSelector.jsx'
import TransactionPanel from './components/TransactionPanel.jsx'
import './transactions.css'

const PAGE_SIZE = 50
const KIND_CLASS = { income: 'income', expense: 'expense', savings: 'savings' }

function BancoTransactions(){
    const now = new Date()
    const [year, setYear] = useState(now.getFullYear())
    const [month, setMonth] = useState(now.getMonth() + 1)
    const [allTime, setAllTime] = useState(false)
    const [accountId, setAccountId] = useState('')
    const [categoryId, setCategoryId] = useState('')
    const [search, setSearch] = useState('')
    const [q, setQ] = useState('')           // debounced copy of `search`
    const [page, setPage] = useState(0)

    const [options, setOptions] = useState(null)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const [reloads, setReloads] = useState(0)
    const [panel, setPanel] = useState(null)  // null = closed, { tx } = open (tx null = new)

    useEffect(() => { getTransactionOptions().then(setOptions) }, [])

    useEffect(() => {
        const timer = setTimeout(() => { setQ(search.trim()); setPage(0) }, 300)
        return () => clearTimeout(timer)
    }, [search])

    useEffect(() => {
        let stale = false
        listTransactions({
            year: allTime ? null : year, month: allTime ? null : month,
            accountId, categoryId, q, limit: PAGE_SIZE, offset: page * PAGE_SIZE,
        }).then((r) => { if (!stale) { setResult(r); setError('') } })
          .catch(() => { if (!stale) setError('Não foi possível carregar as transações.') })
        return () => { stale = true }
    }, [year, month, allTime, accountId, categoryId, q, page, reloads])

    const closePanel = useCallback(() => setPanel(null), [])
    const saved = useCallback(() => { setPanel(null); setReloads((n) => n + 1) }, [])
    const resetPage = (setter) => (e) => { setter(e.target.value); setPage(0) }

    const accountName = (id) => options?.accounts.find((a) => a.id === id)?.name ?? ''
    const categoryName = (id) => options?.categories.find((c) => c.id === id)?.name ?? 'Sem categoria'

    const total = result?.total ?? 0
    const first = total === 0 ? 0 : page * PAGE_SIZE + 1
    const last = Math.min((page + 1) * PAGE_SIZE, total)

    return (
        <>
            <div className="page-head">
                <div>
                    <h1 className="page-title">Transações</h1>
                    <p className="page-subtitle">Mais recentes primeiro. Clique numa linha para editar.</p>
                </div>
                <button className="btn btn-accent" onClick={() => setPanel({ tx: null })} disabled={!options}>
                    <Plus size={16} aria-hidden="true" className="tx-plus" /> Nova
                </button>
            </div>

            <div className="tx-filters">
                <div className="tx-period">
                    {!allTime && (
                        <MonthSelector year={year} month={month}
                                       onChange={(y, m) => { setYear(y); setMonth(m); setPage(0) }} />
                    )}
                    <div className="seg" role="group" aria-label="Período">
                        <button className={allTime ? '' : 'is-on'} aria-pressed={!allTime}
                                onClick={() => { setAllTime(false); setPage(0) }}>Mês</button>
                        <button className={allTime ? 'is-on' : ''} aria-pressed={allTime}
                                onClick={() => { setAllTime(true); setPage(0) }}>Tudo</button>
                    </div>
                </div>

                <select className="tx-input tx-filter" aria-label="Conta" value={accountId}
                        onChange={resetPage(setAccountId)}>
                    <option value="">Todas as contas</option>
                    {options?.accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>

                <select className="tx-input tx-filter" aria-label="Categoria" value={categoryId}
                        onChange={resetPage(setCategoryId)}>
                    <option value="">Todas as categorias</option>
                    {options?.categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>

                <label className="tx-search">
                    <Search size={16} aria-hidden="true" />
                    <input className="tx-input" type="search" placeholder="Buscar na descrição"
                           aria-label="Buscar na descrição" value={search}
                           onChange={(e) => setSearch(e.target.value)} />
                </label>
            </div>

            <section className="card tx-card">
                {error ? <p className="tx-error" role="alert">{error}</p>
                : !result || !options ? <p className="note">Carregando…</p>
                : result.items.length === 0 ? <p className="note">Nenhuma transação encontrada.</p> : (
                    <table className="tx-table">
                        <thead>
                            <tr>
                                <th>Data</th><th>Descrição</th><th>Conta</th><th>Categoria</th>
                                <th className="n">Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {result.items.map((tx) => (
                                <tr key={tx.id} onClick={() => setPanel({ tx })}>
                                    <td className="tx-date"><DateBR iso={tx.date} /></td>
                                    <td>
                                        <button className="tx-open" onClick={(e) => { e.stopPropagation(); setPanel({ tx }) }}>
                                            {tx.description}
                                        </button>
                                    </td>
                                    <td className="tx-dim">{accountName(tx.account_id)}</td>
                                    <td className="tx-dim">{categoryName(tx.category_id)}</td>
                                    <td className="n">
                                        <Money cents={tx.kind === 'expense' ? -tx.amount_cents : tx.amount_cents}
                                               signed className={KIND_CLASS[tx.kind]} />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            {total > PAGE_SIZE && (
                <div className="tx-pager">
                    <span className="dim">{first}–{last} de {total}</span>
                    <button className="btn" disabled={page === 0} onClick={() => setPage(page - 1)}>Anterior</button>
                    <button className="btn" disabled={last >= total} onClick={() => setPage(page + 1)}>Próxima</button>
                </div>
            )}

            {panel && (
                <TransactionPanel key={panel.tx?.id ?? 'new'} tx={panel.tx} options={options}
                                  onClose={closePanel} onSaved={saved} />
            )}
        </>
    )
}

export default BancoTransactions
