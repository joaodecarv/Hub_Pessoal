import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import { listAccounts, createAccount, updateAccount, deleteAccount } from '../cadastrosApi.js'
import SettingsPanel from './SettingsPanel.jsx'
import '../transactions.css'
import '../settings.css'

const ACCOUNT_KINDS = {
    checking: 'Conta corrente',
    savings: 'Poupança',
    credit_card: 'Cartão de crédito',
    cash: 'Dinheiro',
}

function AccountForm({ account, onClose, onSaved }){
    const [name, setName] = useState(account?.name ?? '')
    const [kind, setKind] = useState(account?.kind ?? 'checking')
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const [confirmingDelete, setConfirmingDelete] = useState(false)
    const hasTransactions = Boolean(account?.transaction_count)

    async function run(action){
        setBusy(true)
        setError('')
        try { await action(); onSaved() }
        catch (e) { setError(e.message); setBusy(false) }
    }

    function save(e){
        e.preventDefault()
        const body = { name, kind }
        run(() => (account ? updateAccount(account.id, body) : createAccount(body)))
    }

    return (
        <SettingsPanel title={account ? 'Editar conta' : 'Nova conta'} onClose={onClose}>
            <form className="tx-form" onSubmit={save}>
                <label className="tx-field">Nome
                    <input className="tx-input" value={name} onChange={(e) => setName(e.target.value)} />
                </label>
                <label className="tx-field">Tipo
                    <select className="tx-input" value={kind} onChange={(e) => setKind(e.target.value)}>
                        {Object.entries(ACCOUNT_KINDS).map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                        ))}
                    </select>
                </label>

                {error && <p className="tx-error" role="alert">{error}</p>}

                <div className="tx-actions">
                    <button type="submit" className="btn btn-accent" disabled={busy}>
                        {busy ? 'Salvando…' : 'Salvar'}
                    </button>
                    <button type="button" className="btn" onClick={onClose}>Cancelar</button>
                    {account && !confirmingDelete && (
                        <button type="button" className="btn push" onClick={() => setConfirmingDelete(true)}>
                            Excluir
                        </button>
                    )}
                </div>

                {account && confirmingDelete && (
                    <div className="tx-confirm" role="alertdialog" aria-label="Confirmar exclusão">
                        {hasTransactions ? (
                            <p>
                                Esta conta tem {account.transaction_count} {account.transaction_count === 1 ? 'transação' : 'transações'} e não pode ser excluída:
                                apagá-la corromperia o histórico. Exclua ou mova as transações antes.
                            </p>
                        ) : (
                            <p>Excluir a conta {account.name}? Isso não pode ser desfeito.</p>
                        )}
                        <div className="tx-actions">
                            {!hasTransactions && (
                                <button type="button" className="btn tx-danger" disabled={busy}
                                        onClick={() => run(() => deleteAccount(account.id))}>
                                    Confirmar exclusão
                                </button>
                            )}
                            <button type="button" className="btn" onClick={() => setConfirmingDelete(false)}>
                                {hasTransactions ? 'Entendi' : 'Manter'}
                            </button>
                        </div>
                    </div>
                )}
            </form>
        </SettingsPanel>
    )
}

function AccountsTab(){
    const [accounts, setAccounts] = useState(null)
    const [error, setError] = useState('')
    const [panel, setPanel] = useState(null)  // null = closed, { account } = open (account null = new)
    const [reloads, setReloads] = useState(0)

    useEffect(() => {
        listAccounts().then((r) => { setAccounts(r); setError('') })
                      .catch(() => setError('Não foi possível carregar as contas.'))
    }, [reloads])

    const closePanel = useCallback(() => setPanel(null), [])
    const saved = useCallback(() => { setPanel(null); setReloads((n) => n + 1) }, [])

    return (
        <>
            <div className="cfg-bar">
                <p>Contas onde suas transações acontecem. Clique numa linha para editar.</p>
                <button className="btn btn-accent" onClick={() => setPanel({ account: null })}>
                    <Plus size={16} aria-hidden="true" className="tx-plus" /> Nova
                </button>
            </div>

            <section className="card tx-card">
                {error ? <p className="tx-error" role="alert">{error}</p>
                : !accounts ? <p className="note">Carregando…</p>
                : accounts.length === 0 ? <p className="note">Nenhuma conta cadastrada.</p> : (
                    <table className="tx-table">
                        <thead>
                            <tr><th>Nome</th><th>Tipo</th><th className="n">Transações</th></tr>
                        </thead>
                        <tbody>
                            {accounts.map((a) => (
                                <tr key={a.id} onClick={() => setPanel({ account: a })}>
                                    <td>
                                        <button className="tx-open" onClick={(e) => { e.stopPropagation(); setPanel({ account: a }) }}>
                                            {a.name}
                                        </button>
                                    </td>
                                    <td className="tx-dim">{ACCOUNT_KINDS[a.kind]}</td>
                                    <td className="n">{a.transaction_count}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            {panel && <AccountForm account={panel.account} onClose={closePanel} onSaved={saved} />}
        </>
    )
}

export default AccountsTab
