import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import { listRules, listCategories, createRule, updateRule, deleteRule } from '../cadastrosApi.js'
import SettingsPanel from './SettingsPanel.jsx'
import '../transactions.css'
import '../settings.css'

const MATCH_TYPES = [
    { value: 'contains', label: 'Contém' },
    { value: 'regex', label: 'Regex' },
]
const MATCH_LABEL = Object.fromEntries(MATCH_TYPES.map((m) => [m.value, m.label]))

function RuleForm({ rule, categories, onClose, onSaved }){
    const [form, setForm] = useState({
        pattern: rule?.pattern ?? '',
        match_type: rule?.match_type ?? 'contains',
        category_id: rule ? String(rule.category_id) : '',
        priority: String(rule?.priority ?? 100),
    })
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const [confirmingDelete, setConfirmingDelete] = useState(false)

    async function run(action){
        setBusy(true)
        setError('')
        try { await action(); onSaved() }
        catch (e) { setError(e.message); setBusy(false) }
    }

    function save(e){
        e.preventDefault()
        const priority = form.priority.trim() === '' ? NaN : Number(form.priority)
        if (!Number.isInteger(priority)) { setError('Prioridade deve ser um número inteiro'); return }
        const body = {
            pattern: form.pattern,
            match_type: form.match_type,
            category_id: form.category_id ? Number(form.category_id) : null,
            priority,
        }
        run(() => (rule ? updateRule(rule.id, body) : createRule(body)))
    }

    return (
        <SettingsPanel title={rule ? 'Editar regra' : 'Nova regra'} onClose={onClose}>
            <form className="tx-form" onSubmit={save}>
                <div className="tx-field" role="group" aria-label="Tipo de regra">Quando a descrição
                    <div className="seg tx-kind">
                        {MATCH_TYPES.map((m) => (
                            <button key={m.value} type="button" className={form.match_type === m.value ? 'is-on' : ''}
                                    aria-pressed={form.match_type === m.value}
                                    onClick={() => setForm({ ...form, match_type: m.value })}>
                                {m.label}
                            </button>
                        ))}
                    </div>
                </div>

                <label className="tx-field">{form.match_type === 'regex' ? 'Expressão regular' : 'Texto'}
                    <input className="tx-input" value={form.pattern}
                           placeholder={form.match_type === 'regex' ? '^PIX .*aluguel' : 'padaria'}
                           onChange={(e) => setForm({ ...form, pattern: e.target.value })} />
                </label>

                <label className="tx-field">Categoria
                    <select className="tx-input" value={form.category_id}
                            onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                        <option value="">Selecione…</option>
                        {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                </label>

                <label className="tx-field">Prioridade
                    <input className="tx-input" inputMode="numeric" value={form.priority}
                           onChange={(e) => setForm({ ...form, priority: e.target.value })} />
                </label>
                <p className="cfg-hint">Menor número é aplicado primeiro; vale a primeira regra que casar.</p>

                {error && <p className="tx-error" role="alert">{error}</p>}

                <div className="tx-actions">
                    <button type="submit" className="btn btn-accent" disabled={busy}>
                        {busy ? 'Salvando…' : 'Salvar'}
                    </button>
                    <button type="button" className="btn" onClick={onClose}>Cancelar</button>
                    {rule && !confirmingDelete && (
                        <button type="button" className="btn push" onClick={() => setConfirmingDelete(true)}>
                            Excluir
                        </button>
                    )}
                </div>

                {rule && confirmingDelete && (
                    <div className="tx-confirm" role="alertdialog" aria-label="Confirmar exclusão">
                        <p>Excluir esta regra? Isso não pode ser desfeito.</p>
                        <div className="tx-actions">
                            <button type="button" className="btn tx-danger" disabled={busy}
                                    onClick={() => run(() => deleteRule(rule.id))}>
                                Confirmar exclusão
                            </button>
                            <button type="button" className="btn" onClick={() => setConfirmingDelete(false)}>
                                Manter
                            </button>
                        </div>
                    </div>
                )}
            </form>
        </SettingsPanel>
    )
}

function RulesTab(){
    const [rules, setRules] = useState(null)
    const [categories, setCategories] = useState([])
    const [error, setError] = useState('')
    const [panel, setPanel] = useState(null)
    const [reloads, setReloads] = useState(0)

    useEffect(() => {
        Promise.all([listRules(), listCategories()])
            .then(([r, c]) => { setRules(r); setCategories(c); setError('') })
            .catch(() => setError('Não foi possível carregar as regras.'))
    }, [reloads])

    const closePanel = useCallback(() => setPanel(null), [])
    const saved = useCallback(() => { setPanel(null); setReloads((n) => n + 1) }, [])
    const categoryName = (id) => categories.find((c) => c.id === id)?.name ?? ''

    return (
        <>
            <div className="cfg-bar">
                <p>Categorizam automaticamente as importações, em ordem de prioridade. Clique numa linha para editar.</p>
                <button className="btn btn-accent" onClick={() => setPanel({ rule: null })}>
                    <Plus size={16} aria-hidden="true" className="tx-plus" /> Nova
                </button>
            </div>

            <section className="card tx-card">
                {error ? <p className="tx-error" role="alert">{error}</p>
                : !rules ? <p className="note">Carregando…</p>
                : rules.length === 0 ? <p className="note">Nenhuma regra cadastrada.</p> : (
                    <table className="tx-table">
                        <thead>
                            <tr><th className="n">Prioridade</th><th>Quando a descrição</th><th>Padrão</th><th>Categoria</th></tr>
                        </thead>
                        <tbody>
                            {rules.map((r) => (
                                <tr key={r.id} onClick={() => setPanel({ rule: r })}>
                                    <td className="n">{r.priority}</td>
                                    <td className="tx-dim">{MATCH_LABEL[r.match_type]}</td>
                                    <td>
                                        <button className="tx-open" onClick={(e) => { e.stopPropagation(); setPanel({ rule: r }) }}>
                                            {r.pattern}
                                        </button>
                                    </td>
                                    <td className="tx-dim">{categoryName(r.category_id)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            {panel && <RuleForm rule={panel.rule} categories={categories} onClose={closePanel} onSaved={saved} />}
        </>
    )
}

export default RulesTab
