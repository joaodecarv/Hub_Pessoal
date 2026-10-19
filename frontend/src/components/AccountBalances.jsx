import { Landmark, PiggyBank, CreditCard, Wallet } from 'lucide-react'
import Money from './Money.jsx'

const KIND = {
    checking:    { icon: Landmark,   label: 'Conta corrente' },
    savings:     { icon: PiggyBank,  label: 'Poupança' },
    credit_card: { icon: CreditCard, label: 'Cartão de crédito' },
    cash:        { icon: Wallet,     label: 'Dinheiro' },
}

const signClass = (c) => (c > 0 ? 'income' : c < 0 ? 'expense' : '')

function AccountBalances({ accounts }){
    if (!accounts.length) return <p className="note">Nenhuma conta.</p>
    const total = accounts.reduce((s, a) => s + a.balance_cents, 0)

    return (
        <ul className="rows">
            {accounts.map((a) => {
                const { icon: Icon, label } = KIND[a.kind] || KIND.cash
                return (
                    <li key={a.id}>
                        <span className="row-main row-icon">
                            <Icon size={18} aria-hidden="true" />
                            <span>{a.name} <span className="row-sub">· {label}</span></span>
                        </span>
                        <Money cents={a.balance_cents} className={signClass(a.balance_cents)} />
                    </li>
                )
            })}
            <li className="row-total">
                <span>Total</span>
                <Money cents={total} className={signClass(total)} />
            </li>
        </ul>
    )
}

export default AccountBalances
