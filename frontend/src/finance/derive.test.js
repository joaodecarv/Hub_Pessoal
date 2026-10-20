import { describe, expect, test } from 'vitest'
import { cumulative, shareOfIncome, shareChangePP, vsAverage, goalMonthlyNeed } from './derive.js'

describe('cumulative', () => {
    test('running total of daily spending, so the curve only goes up', () => {
        expect(cumulative([100, 0, 250, 50])).toEqual([100, 100, 350, 400])
    })
})

describe('shareOfIncome', () => {
    test('percent of the month income a value took', () => {
        expect(shareOfIncome(2500, 10000)).toBe(25)
    })

    test('is null when there was no income, instead of dividing by zero', () => {
        expect(shareOfIncome(2500, 0)).toBeNull()
    })
})

describe('shareChangePP', () => {
    test('difference in percentage points between this month and last month shares', () => {
        // 25% of income now vs 20% last month
        expect(shareChangePP({ cents: 2500, incomeCents: 10000 }, { cents: 2000, incomeCents: 10000 })).toBe(5)
    })

    test('a smaller income makes the same spending weigh more', () => {
        // R$ 20 both months, but income fell from 100 to 80: 20% -> 25%
        expect(shareChangePP({ cents: 2000, incomeCents: 8000 }, { cents: 2000, incomeCents: 10000 })).toBe(5)
    })

    test('is null when either month had no income', () => {
        expect(shareChangePP({ cents: 2000, incomeCents: 8000 }, { cents: 2000, incomeCents: 0 })).toBeNull()
    })
})

describe('vsAverage', () => {
    test('percent change of the last month vs the average of the earlier months', () => {
        // earlier months average 200; last month 240 -> +20%
        expect(vsAverage([100, 200, 300, 240])).toBe(20)
        expect(vsAverage([400, 400, 300])).toBe(-25)
    })

    test('is null when the earlier months average zero (nothing to compare with)', () => {
        expect(vsAverage([0, 0, 500])).toBeNull()
    })

    test('months before the category first appears do not drag the average down', () => {
        // data only starts in month 4: average of [200] -> 300 is +50%, not vs [0, 0, 0, 200]
        expect(vsAverage([0, 0, 0, 200, 300])).toBe(50)
        // a zero after the first appearance is a real month without spending and does count
        expect(vsAverage([0, 200, 0, 150])).toBe(50)
    })
})

describe('goalMonthlyNeed', () => {
    const goal = { target_cents: 1000000, saved_cents: 400000, days_remaining: 90, achieved: false, deadline: '2027-01-15' }

    test('what is still missing, spread over the months left until the deadline', () => {
        // R$ 6.000 missing, 3 months left
        expect(goalMonthlyNeed(goal)).toBe(200000)
    })

    test('a partial month counts as a whole month', () => {
        expect(goalMonthlyNeed({ ...goal, days_remaining: 70 })).toBe(200000)
    })

    test('past the deadline, everything missing is due now', () => {
        expect(goalMonthlyNeed({ ...goal, days_remaining: -5 })).toBe(600000)
    })

    test('achieved goals need nothing; goals without deadline have no monthly need', () => {
        expect(goalMonthlyNeed({ ...goal, achieved: true })).toBe(0)
        expect(goalMonthlyNeed({ ...goal, deadline: null, days_remaining: null })).toBeNull()
    })
})
