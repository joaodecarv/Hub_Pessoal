



async function getJSON(path, options){
    const response = await fetch(path, options)
    if(!response.ok){
        throw new Error(`API ${path} failed: ${response.status}`)   
    }
    return response.json()
}

export function getAccounts(){
    return getJSON(`/api/banco/accounts`)
}

export function getTransactions(limit = 50, offset = 0){
    return getJSON(`/api/banco/transactions?limit=${limit}&offset=${offset}`)
}

export function getSummary(year, month){
    const params = (year && month) ? `?year=${year}&month=${month}` : ''
    return getJSON(`/api/banco/summary${params}`)
}


export function getTrends(year, month, months = 6){
    const params = new URLSearchParams()
    if (year && month){ params.set('year', year); params.set('month', month) }
    params.set('months', months)
    return getJSON(`/api/banco/trends?${params.toString()}`)
}


export function getBalances(){
    return getJSON(`/api/banco/balances`)
}

export function getGoals(year, month){
    return getJSON(`/api/banco/goals?year=${year}&month=${month}`)
}

export function getTopExpenses(year, month, limit = 5){
    return getJSON(`/api/banco/top-expenses?year=${year}&month=${month}&limit=${limit}`)
}

export function getDailyExpenses(year, month){
    return getJSON(`/api/banco/daily-expenses?year=${year}&month=${month}`)
}

// kind: 'expense' | 'income'
export function getCategoryHistory(year, month, months = 6, kind = 'expense'){
    return getJSON(`/api/banco/category-history?year=${year}&month=${month}&months=${months}&kind=${kind}`)
}

export function getDigest(topic){
    return getJSON(`/api/digest?topic=${topic}`)
}

export function refreshDigest(topic){
    return getJSON(`/api/digest/refresh?topic=${topic}`, {method: 'POST'})
}
