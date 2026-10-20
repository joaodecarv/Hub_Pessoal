import { useState } from 'react'
import { brl, pct, pp } from '../finance/format.js'
import { shareOfIncome, shareChangePP } from '../finance/derive.js'

const tone = (x) => x.tone ?? (x.fixed ? 'fixed' : 'var')

function PP({ now, prev, inc, goodUp }){
    const d = shareChangePP({ cents: now, incomeCents: inc.now }, { cents: prev, incomeCents: inc.before })
    if (d === null) return <span className="row-sub">—</span>
    if (Math.abs(d) < 0.05) return <span className="row-sub">0,0 p.p.</span>
    const good = goodUp ? d > 0 : d < 0
    return <span className={good ? 'income' : 'expense'}>{d > 0 ? '▲' : '▼'} {pp(d)}</span>
}

// How each real of the month's income was used: every expense category, savings and the
// leftover as a share of income, with the change in percentage points vs the previous month.
// `categories` rows come from /category-history (history_cents: last = this month).
function IncomeShare({ summary, categories, prevLabel }){
    const [hl, setHl] = useState(null)
    const c = summary.current, p = summary.previous
    const inc = { now: c.income_cents, before: p.income_cents }
    if (!inc.now) return <p className="note">Sem receitas neste mês, então não há como dividir a renda.</p>

    const last = (x) => x.history_cents[x.history_cents.length - 1]
    const before = (x) => x.history_cents[x.history_cents.length - 2] ?? 0
    const spent = categories.filter((x) => last(x) > 0)
    const fixed = spent.filter((x) => x.is_fixed), variable = spent.filter((x) => !x.is_fixed)
    const sum = (list, f) => list.reduce((a, x) => a + f(x), 0)

    const segs = [
        ...[...fixed, ...variable].map((x) => ({ id: x.category_name, label: x.category_name, fixed: x.is_fixed, now: last(x), prev: before(x) })),
        { id: 'Guardado', label: 'Guardado', tone: 'save', goodUp: true, now: c.savings_cents, prev: p.savings_cents },
        // A negative leftover (spent more than earned) has no place in a 100% bar.
        ...(c.net_cents > 0 ? [{ id: 'Sobra', label: 'Sobra', tone: 'good', goodUp: true, now: c.net_cents, prev: p.net_cents }] : []),
    ].filter((x) => x.now > 0)
    const heads = [
        { label: 'Despesas fixas', now: sum(fixed, last), prev: sum(fixed, before) },
        { label: 'Despesas variáveis', now: sum(variable, last), prev: sum(variable, before) },
        { label: 'Guardado', cls: 'savings', goodUp: true, now: c.savings_cents, prev: p.savings_cents },
        { label: c.net_cents < 0 ? 'Déficit' : 'Sobra', cls: c.net_cents < 0 ? 'expense' : 'income', goodUp: true, now: c.net_cents, prev: p.net_cents },
    ]
    const ranked = [...segs].sort((a, b) => b.now - a.now)
    const maxShare = shareOfIncome(ranked[0]?.now ?? 0, inc.now) || 1

    return (
        <>
            <div className="share-heads">
                {heads.map((h) => (
                    <div key={h.label}>
                        <small>{h.label}</small>
                        <b className={h.cls ?? ''}>{pct(shareOfIncome(h.now, inc.now))}</b>
                        <PP now={h.now} prev={h.prev} inc={inc} goodUp={h.goodUp} />
                    </div>
                ))}
            </div>
            <div className="share-bar" role="img" aria-label={ranked.map((x) => `${x.label} ${pct(shareOfIncome(x.now, inc.now))}`).join(', ')}>
                {segs.map((x) => {
                    const w = shareOfIncome(x.now, inc.now)
                    return (
                        <span key={x.id} style={{ flexGrow: x.now }} className={`sh-${tone(x)} ${hl && hl !== x.id ? 'is-dim' : ''}`}
                              onMouseEnter={() => setHl(x.id)} onMouseLeave={() => setHl(null)}>
                            {w >= 7 && <em>{x.label} {pct(w, 0)}</em>}
                        </span>
                    )
                })}
            </div>
            <div className="share-key">
                <span><i className="sh-fixed" />Fixas</span><span><i className="sh-var" />Variáveis</span>
                <span><i className="sh-save" />Guardado</span><span><i className="sh-good" />Sobra</span>
                <span className="share-key-note">variação em pontos percentuais vs {prevLabel}</span>
            </div>
            <ol className="share-list" style={{ gridTemplateRows: `repeat(${Math.ceil(ranked.length / 2)}, auto)` }}>
                {ranked.map((x) => {
                    const w = shareOfIncome(x.now, inc.now)
                    return (
                        <li key={x.id} className={hl === x.id ? 'is-hl' : ''} onMouseEnter={() => setHl(x.id)} onMouseLeave={() => setHl(null)}>
                            <span>{x.label}{x.fixed && <span className="row-sub"> · fixa</span>}</span>
                            <span className="share-track"><span className={`sh-${tone(x)}`} style={{ width: `${(w / maxShare) * 100}%` }} /></span>
                            <b>{pct(w)}</b>
                            <span className="share-pp"><PP now={x.now} prev={x.prev} inc={inc} goodUp={x.goodUp} /></span>
                            <span className="row-sub share-amt">{brl(x.now)}</span>
                        </li>
                    )
                })}
            </ol>
        </>
    )
}

export default IncomeShare
