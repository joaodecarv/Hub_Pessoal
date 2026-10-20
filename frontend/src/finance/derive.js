// Pure calculations behind the finance dashboard (no React, no fetching), so they can be tested.

export function cumulative(values){
    let total = 0
    return values.map((v) => (total += v))
}

export function shareOfIncome(cents, incomeCents){
    return incomeCents ? (cents / incomeCents) * 100 : null
}

// Percentage-point change of a value's share of income vs the previous month.
export function shareChangePP(current, previous){
    const now = shareOfIncome(current.cents, current.incomeCents)
    const before = shareOfIncome(previous.cents, previous.incomeCents)
    return now === null || before === null ? null : now - before
}

// Last value vs the mean of the values before it, in percent. Leading zeros are months
// before the category existed (or before any data), so they are left out of the mean.
export function vsAverage(history){
    const first = history.findIndex((v) => v !== 0)
    const earlier = history.slice(first === -1 ? 0 : first, -1)
    const avg = earlier.length ? earlier.reduce((a, b) => a + b, 0) / earlier.length : 0
    return avg ? ((history[history.length - 1] - avg) / avg) * 100 : null
}

// Monthly amount still needed to reach a goal by its deadline (a partial month counts whole).
export function goalMonthlyNeed(goal){
    if (goal.achieved) return 0
    if (goal.deadline === null) return null
    const months = Math.max(1, Math.ceil(goal.days_remaining / 30))
    return Math.ceil((goal.target_cents - goal.saved_cents) / months)
}
