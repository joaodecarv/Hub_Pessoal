import { useState, useEffect, useCallback } from 'react'
import { Plus } from 'lucide-react'
import {
    listCategories, createCategory, updateCategory, deleteCategory, getCategoryImpact,
} from '../cadastrosApi.js'
import SettingsPanel from './SettingsPanel.jsx'
import '../transactions.css'
import '../settings.css'

const KINDS = [
    { value: 'expense', label: 'Despesa' },
    { value: 'income', label: 'Receita' },
    { value: 'savings', label: 'Poupança' },
]
const KIND_LABEL = Object.fromEntries(KINDS.map((k) => [k.value, k.label]))

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

function CategoryForm({ category, onClose, onSaved }){
    const [form, setForm] = useState({
        name: category?.name ?? '',
        kind: category?.kind ?? 'expense',
        color: category?.color ?? '#808080',
        is_fixed: category?.is_fixed ?? false,
    })
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const [impact, setImpact] = useState(null)  // null = not asked for yet

    async function run(action){
        setBusy(true)
        setError('')
        try { await action(); onSaved() }
        catch (e) { setError(e.message); setBusy(false) }
    }

    function save(e){
        e.preventDefault()
        run(() => (category ? updateCategory(category.id, form) : createCategory(form)))
    }

    async function askDelete(){
        setError('')
        try { setImpact(await getCategoryImpact(category.id)) }
        catch (e) { setError(e.message) }
    }

    const nothingAffected = impact && !impact.transactions && !impact.rules && !impact.budgets

    return (
        <SettingsPanel title={category ? 'Editar categoria' : 'Nova categoria'} onClose={onClose}>
            <form className="tx-form" onSubmit={save}>
                <label className="tx-field">Nome
                    <input className="tx-input" value={form.name}
                           onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </label>

                <div className="tx-field" role="group" aria-label="Tipo">Tipo
                    <div className="seg tx-kind">
                        {KINDS.map((k) => (
                            <button key={k.value} type="button" className={form.kind === k.value ? 'is-on' : ''}
                                    aria-pressed={form.kind === k.value}
                                    onClick={() => setForm({ ...form, kind: k.value, is_fixed: k.value === 'expense' && form.is_fixed })}>
                                {k.label}
                            </button>
                        ))}
                    </div>
                </div>

                <label className="tx-field">Cor
                    <input className="tx-input cfg-color" type="color" value={form.color}
                           onChange={(e) => setForm({ ...form, color: e.target.value })} />
                </label>

                {form.kind === 'expense' && (
                    <label className="cfg-check">
                        <input type="checkbox" checked={form.is_fixed}
                               onChange={(e) => setForm({ ...form, is_fixed: e.target.checked })} />
                        Despesa fixa (desmarcado = variável)
                    </label>
                )}

                {error && <p className="tx-error" role="alert">{error}</p>}

                <div className="tx-actions">
                    <button type="submit" className="btn btn-accent" disabled={busy}>
                        {busy ? 'Salvando…' : 'Salvar'}
                    </button>
                    <button type="button" className="btn" onClick={onClose}>Cancelar</button>
                    {category && !impact && (
                        <button type="button" className="btn push" onClick={askDelete}>Excluir</button>
                    )}
                </div>

                {category && impact && (
                    <div className="tx-confirm" role="alertdialog" aria-label="Confirmar exclusão">
                        <p>Excluir a categoria {category.name}?</p>
                        {nothingAffected ? (
                            <p className="cfg-hint">Nenhuma transação, regra ou orçamento usa esta categoria.</p>
                        ) : (
                            <ul className="cfg-impact">
                                <li>{plural(impact.transactions, 'transação ficará', 'transações ficarão')} sem categoria</li>
                                <li>{plural(impact.rules, 'regra será apagada', 'regras serão apagadas')}</li>
                                <li>{plural(impact.budgets, 'orçamento será apagado', 'orçamentos serão apagados')}</li>
                            </ul>
                        )}
                        <div className="tx-actions">
                            <button type="button" className="btn tx-danger" disabled={busy}
                                    onClick={() => run(() => deleteCategory(category.id))}>
                                Confirmar exclusão
                            </button>
                            <button type="button" className="btn" onClick={() => setImpact(null)}>Manter</button>
                        </div>
                    </div>
                )}
            </form>
        </SettingsPanel>
    )
}

function CategoriesTab(){
    const [categories, setCategories] = useState(null)
    const [error, setError] = useState('')
    const [panel, setPanel] = useState(null)
    const [reloads, setReloads] = useState(0)

    useEffect(() => {
        listCategories().then((r) => { setCategories(r); setError('') })
                        .catch(() => setError('Não foi possível carregar as categorias.'))
    }, [reloads])

    const closePanel = useCallback(() => setPanel(null), [])
    const saved = useCallback(() => { setPanel(null); setReloads((n) => n + 1) }, [])

    return (
        <>
            <div className="cfg-bar">
                <p>Como suas transações são classificadas. Clique numa linha para editar.</p>
                <button className="btn btn-accent" onClick={() => setPanel({ category: null })}>
                    <Plus size={16} aria-hidden="true" className="tx-plus" /> Nova
                </button>
            </div>

            <section className="card tx-card">
                {error ? <p className="tx-error" role="alert">{error}</p>
                : !categories ? <p className="note">Carregando…</p>
                : categories.length === 0 ? <p className="note">Nenhuma categoria cadastrada.</p> : (
                    <table className="tx-table">
                        <thead>
                            <tr><th>Nome</th><th>Tipo</th><th>Fixa ou variável</th></tr>
                        </thead>
                        <tbody>
                            {categories.map((c) => (
                                <tr key={c.id} onClick={() => setPanel({ category: c })}>
                                    <td>
                                        <span className="cfg-swatch" style={{ background: c.color }} aria-hidden="true" />
                                        <button className="tx-open" onClick={(e) => { e.stopPropagation(); setPanel({ category: c }) }}>
                                            {c.name}
                                        </button>
                                    </td>
                                    <td className="tx-dim">{KIND_LABEL[c.kind]}</td>
                                    <td className="tx-dim">{c.kind === 'expense' ? (c.is_fixed ? 'Fixa' : 'Variável') : '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            {panel && <CategoryForm category={panel.category} onClose={closePanel} onSaved={saved} />}
        </>
    )
}

export default CategoriesTab
