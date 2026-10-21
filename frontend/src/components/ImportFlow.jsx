import { useState, useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { previewImport, commitImport } from '../api.js'
import Money from './Money.jsx'
import DateBR from './DateBR.jsx'
import '../transactions.css'
import '../import.css'

const DATE_FORMATS = [
    { value: '%d/%m/%Y', label: 'dd/mm/aaaa' },
    { value: '%d/%m/%y', label: 'dd/mm/aa' },
    { value: '%Y-%m-%d', label: 'aaaa-mm-dd' },
    { value: '%d-%m-%Y', label: 'dd-mm-aaaa' },
]
const NUMBER_FORMATS = {
    br: { decimal_separator: ',', thousands_separator: '.', label: '1.234,56' },
    us: { decimal_separator: '.', thousands_separator: ',', label: '1,234.56' },
}

const guessColumn = (columns, pattern) => columns.find((c) => pattern.test(c)) ?? ''

// Start the mapping form from the account's saved mapping, or guess from the header names.
function initialMapping({ columns, suggested, mapping }){
    if (mapping) {
        const numberFormat = mapping.decimal_separator === '.' ? 'us' : 'br'
        const ref = (v) => (v === null || v === undefined ? '' : String(v))
        return {
            hasHeader: mapping.has_header,
            dateCol: ref(mapping.date_col), descCol: ref(mapping.description_col),
            amountMode: mapping.amount_col === null || mapping.amount_col === undefined ? 'split' : 'single',
            amountCol: ref(mapping.amount_col), debitCol: ref(mapping.debit_col), creditCol: ref(mapping.credit_col),
            dateFormat: mapping.date_format, numberFormat, invertSign: mapping.invert_sign,
            delimiter: mapping.delimiter, encoding: mapping.encoding,
        }
    }
    return {
        hasHeader: true,
        dateCol: guessColumn(columns, /data|date/i),
        descCol: guessColumn(columns, /descri|hist|lan[cç]|memo|estab/i),
        amountMode: 'single',
        amountCol: guessColumn(columns, /valor|amount|quantia/i), debitCol: '', creditCol: '',
        dateFormat: '%d/%m/%Y', numberFormat: 'br', invertSign: false,
        delimiter: suggested.delimiter, encoding: suggested.encoding,
    }
}

// The body the API's CsvMapping expects. Without a header, columns are 0-based positions.
function buildMapping(m){
    const ref = (v) => (v === '' ? null : (m.hasHeader ? v : Number(v)))
    const single = m.amountMode === 'single'
    return {
        date_col: ref(m.dateCol), description_col: ref(m.descCol),
        amount_col: single ? ref(m.amountCol) : null,
        debit_col: single ? null : ref(m.debitCol), credit_col: single ? null : ref(m.creditCol),
        date_format: m.dateFormat,
        decimal_separator: NUMBER_FORMATS[m.numberFormat].decimal_separator,
        thousands_separator: NUMBER_FORMATS[m.numberFormat].thousands_separator,
        has_header: m.hasHeader, encoding: m.encoding, delimiter: m.delimiter, invert_sign: m.invertSign,
    }
}

function MappingStep({ info, onSubmit, onBack, busy }){
    const [m, setM] = useState(() => initialMapping(info))
    const set = (field) => (e) => setM((f) => ({ ...f, [field]: e.target.value }))

    // With a header row the options are column names; without one, positions.
    const options = m.hasHeader
        ? info.columns.map((c) => ({ value: c, label: c }))
        : info.columns.map((c, i) => ({ value: String(i), label: `Coluna ${i + 1} (${c})` }))
    const columnSelect = (field, optional) => (
        <select className="tx-input" value={m[field]} onChange={set(field)}>
            <option value="">{optional ? 'Nenhuma' : 'Selecione…'}</option>
            {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
    )

    const ready = m.dateCol !== '' && m.descCol !== '' &&
        (m.amountMode === 'single' ? m.amountCol !== '' : (m.debitCol !== '' || m.creditCol !== ''))
    const sampleRows = m.hasHeader ? info.sample : [info.columns, ...info.sample]

    return (
        <form className="tx-form" onSubmit={(e) => { e.preventDefault(); onSubmit(buildMapping(m)) }}>
            <p className="imp-lead">Indique quais colunas do CSV são a data, a descrição e o valor. O mapeamento fica salvo para esta conta.</p>

            <div className="imp-sample">
                <table className="tx-table">
                    <thead><tr>{info.columns.map((c, i) => <th key={i}>{m.hasHeader ? c : `Coluna ${i + 1}`}</th>)}</tr></thead>
                    <tbody>
                        {sampleRows.map((r, i) => (
                            <tr key={i}>{info.columns.map((_, j) => <td key={j}>{r[j]}</td>)}</tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <label className="imp-check">
                <input type="checkbox" checked={m.hasHeader}
                       onChange={(e) => setM((f) => ({ ...f, hasHeader: e.target.checked, dateCol: '', descCol: '', amountCol: '', debitCol: '', creditCol: '' }))} />
                A primeira linha é o cabeçalho
            </label>

            <div className="tx-row">
                <label className="tx-field">Data{columnSelect('dateCol')}</label>
                <label className="tx-field">Formato da data
                    <select className="tx-input" value={m.dateFormat} onChange={set('dateFormat')}>
                        {DATE_FORMATS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                    </select>
                </label>
            </div>

            <label className="tx-field">Descrição{columnSelect('descCol')}</label>

            <label className="tx-field">Valor
                <select className="tx-input" value={m.amountMode} onChange={set('amountMode')}>
                    <option value="single">Uma coluna com sinal</option>
                    <option value="split">Colunas separadas de débito e crédito</option>
                </select>
            </label>

            {m.amountMode === 'single' ? (
                <>
                    <label className="tx-field">Coluna do valor{columnSelect('amountCol')}</label>
                    <label className="tx-field">Sinal
                        <select className="tx-input" value={m.invertSign ? 'inverted' : 'normal'}
                                onChange={(e) => setM((f) => ({ ...f, invertSign: e.target.value === 'inverted' }))}>
                            <option value="normal">Negativo é despesa, positivo é receita</option>
                            <option value="inverted">Positivo é despesa, negativo é receita</option>
                        </select>
                    </label>
                </>
            ) : (
                <div className="tx-row">
                    <label className="tx-field">Débitos (saídas){columnSelect('debitCol', true)}</label>
                    <label className="tx-field">Créditos (entradas){columnSelect('creditCol', true)}</label>
                </div>
            )}

            <label className="tx-field">Formato dos números
                <select className="tx-input" value={m.numberFormat} onChange={set('numberFormat')}>
                    {Object.entries(NUMBER_FORMATS).map(([k, f]) => <option key={k} value={k}>{f.label}</option>)}
                </select>
            </label>

            <div className="tx-actions">
                <button type="submit" className="btn btn-accent" disabled={!ready || busy}>
                    {busy ? 'Lendo…' : 'Ver prévia'}
                </button>
                <button type="button" className="btn" onClick={onBack}>Voltar</button>
            </div>
        </form>
    )
}

function PreviewStep({ rows, setRows, options, isCsv, onCommit, onBack, onRemap, busy }){
    const selected = rows.filter((r) => r.selected).length
    const duplicates = rows.filter((r) => r.duplicate).length
    const selectable = rows.filter((r) => !r.duplicate)
    const allSelected = selectable.length > 0 && selectable.every((r) => r.selected)

    const patch = (index, change) => setRows((rs) => rs.map((r) => (r.index === index ? { ...r, ...change } : r)))
    const toggleAll = () => setRows((rs) => rs.map((r) => (r.duplicate ? r : { ...r, selected: !allSelected })))

    return (
        <>
            <p className="imp-lead">
                {rows.length} {rows.length === 1 ? 'linha' : 'linhas'}
                {duplicates > 0 && <>, {duplicates} já {duplicates === 1 ? 'importada' : 'importadas'} (desmarcadas)</>}
                . Ajuste as categorias e desmarque o que não quiser importar.
            </p>

            <div className="imp-table-wrap">
                <table className="tx-table imp-table">
                    <thead>
                        <tr>
                            <th><input type="checkbox" aria-label="Selecionar todas" checked={allSelected}
                                       disabled={selectable.length === 0} onChange={toggleAll} /></th>
                            <th>Data</th><th>Descrição</th><th>Categoria</th><th className="n">Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r) => (
                            <tr key={r.index} className={r.duplicate ? 'imp-dup' : ''}>
                                <td><input type="checkbox" aria-label={`Importar ${r.description}`}
                                           checked={r.selected} disabled={r.duplicate}
                                           onChange={(e) => patch(r.index, { selected: e.target.checked })} /></td>
                                <td className="tx-date"><DateBR iso={r.date} /></td>
                                <td>
                                    <span className="imp-desc">{r.description}</span>
                                    {r.duplicate && <span className="imp-badge">Duplicada</span>}
                                </td>
                                <td>
                                    <select className="tx-input imp-cat" aria-label={`Categoria de ${r.description}`}
                                            value={r.category_id ?? ''} disabled={r.duplicate}
                                            onChange={(e) => patch(r.index, { category_id: e.target.value ? Number(e.target.value) : null })}>
                                        <option value="">Sem categoria</option>
                                        {options.categories.filter((c) => c.kind === r.kind).map((c) => (
                                            <option key={c.id} value={c.id}>{c.name}</option>
                                        ))}
                                    </select>
                                </td>
                                <td className="n">
                                    <Money cents={r.kind === 'expense' ? -r.amount_cents : r.amount_cents} signed className={r.kind} />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="tx-actions">
                <button type="button" className="btn btn-accent" disabled={selected === 0 || busy} onClick={onCommit}>
                    {busy ? 'Importando…' : `Importar ${selected} ${selected === 1 ? 'transação' : 'transações'}`}
                </button>
                <button type="button" className="btn" onClick={onBack}>Voltar</button>
                {isCsv && <button type="button" className="btn push" onClick={onRemap} disabled={busy}>Alterar mapeamento</button>}
            </div>
        </>
    )
}

// Import flow in a wide side panel: file + account -> (CSV) column mapping -> preview -> summary.
// onDone runs when the panel closes after rows were written, so the caller can reload.
function ImportFlow({ options, onClose, onDone }){
    const [step, setStep] = useState('file')     // file | mapping | preview | done
    const [accountId, setAccountId] = useState(options.accounts[0] ? String(options.accounts[0].id) : '')
    const [file, setFile] = useState(null)
    const [mappingInfo, setMappingInfo] = useState(null)   // needs_mapping response
    const [mapping, setMapping] = useState(null)           // mapping the current preview was parsed with
    const [rows, setRows] = useState([])
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const panelRef = useRef(null)
    const isCsv = file?.name.toLowerCase().endsWith('.csv')

    const finish = () => (result?.imported > 0 ? onDone() : onClose())

    useEffect(() => {
        panelRef.current?.querySelector('input, select')?.focus()
    }, [step])

    useEffect(() => {
        const onKey = (e) => {
            if (e.key === 'Escape') finish()
            if (e.key !== 'Tab') return
            const focusable = panelRef.current.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled)')
            const first = focusable[0]
            const last = focusable[focusable.length - 1]
            if (e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus() }
            else if (!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus() }
        }
        document.addEventListener('keydown', onKey)
        return () => document.removeEventListener('keydown', onKey)
    })

    async function runPreview(extra = {}){
        setBusy(true)
        setError('')
        try {
            const body = await previewImport({ file, accountId, ...extra })
            if (body.needs_mapping) {
                setMappingInfo(body)
                setStep('mapping')
            } else {
                setMapping(body.mapping)
                setRows(body.rows.map((r, index) => ({ ...r, index, selected: !r.duplicate })))
                setStep('preview')
            }
        } catch (e) {
            setError(e.message)
        } finally {
            setBusy(false)
        }
    }

    async function commit(){
        setBusy(true)
        setError('')
        try {
            const chosen = rows.filter((r) => r.selected).map((r) => ({
                date: r.date, amount_cents: r.amount_cents, kind: r.kind, description: r.description,
                import_hash: r.import_hash, category_id: r.category_id,
            }))
            const outcome = await commitImport({ account_id: Number(accountId), rows: chosen, mapping })
            setResult({ imported: outcome.imported, ignored: rows.length - outcome.imported })
            setStep('done')
        } catch (e) {
            setError(e.message)
        } finally {
            setBusy(false)
        }
    }

    const goToFile = () => { setStep('file'); setError('') }
    const titles = { file: 'Importar extrato', mapping: 'Mapear colunas do CSV', preview: 'Prévia da importação', done: 'Importação concluída' }

    return (
        <>
            <div className="tx-backdrop" onClick={finish} />
            <aside className="tx-panel imp-panel" role="dialog" aria-modal="true"
                   aria-labelledby="imp-title" ref={panelRef}>
                <div className="tx-panel-head">
                    <h2 id="imp-title" className="card-title">{titles[step]}</h2>
                    <button type="button" className="tx-icon-btn" onClick={finish} aria-label="Fechar painel">
                        <X size={18} aria-hidden="true" />
                    </button>
                </div>

                {step === 'file' && (
                    <form className="tx-form" onSubmit={(e) => { e.preventDefault(); runPreview() }}>
                        <label className="tx-field">Arquivo (OFX ou CSV)
                            <input className="tx-input imp-file" type="file" accept=".ofx,.csv"
                                   onChange={(e) => { setFile(e.target.files[0] ?? null); setError('') }} />
                        </label>
                        <label className="tx-field">Conta de destino
                            <select className="tx-input" value={accountId} onChange={(e) => setAccountId(e.target.value)}>
                                {options.accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                            </select>
                        </label>
                        {error && <p className="tx-error" role="alert">{error}</p>}
                        <div className="tx-actions">
                            <button type="submit" className="btn btn-accent" disabled={!file || !accountId || busy}>
                                {busy ? 'Lendo…' : 'Continuar'}
                            </button>
                            <button type="button" className="btn" onClick={onClose}>Cancelar</button>
                            {isCsv && (
                                <button type="button" className="btn push" disabled={busy}
                                        onClick={() => runPreview({ remap: true })}>
                                    Mapear colunas manualmente
                                </button>
                            )}
                        </div>
                    </form>
                )}

                {step === 'mapping' && (
                    <>
                        {error && <p className="tx-error" role="alert">{error}</p>}
                        <MappingStep info={mappingInfo} busy={busy} onBack={goToFile}
                                     onSubmit={(m) => runPreview({ mapping: m })} />
                    </>
                )}

                {step === 'preview' && (
                    <>
                        {error && <p className="tx-error" role="alert">{error}</p>}
                        <PreviewStep rows={rows} setRows={setRows} options={options} isCsv={isCsv} busy={busy}
                                     onCommit={commit} onBack={goToFile} onRemap={() => runPreview({ remap: true })} />
                    </>
                )}

                {step === 'done' && (
                    <div className="tx-form">
                        <p className="imp-summary">
                            {result.imported} {result.imported === 1 ? 'importada' : 'importadas'},{' '}
                            {result.ignored} {result.ignored === 1 ? 'ignorada' : 'ignoradas'}.
                        </p>
                        <div className="tx-actions">
                            <button type="button" className="btn btn-accent" onClick={finish}>Fechar</button>
                        </div>
                    </div>
                )}
            </aside>
        </>
    )
}

export default ImportFlow
