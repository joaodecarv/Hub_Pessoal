



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

export function getCategories(year, month){
    const params = (year && month) ? `?year=${year}&month=${month}` : ''
    return getJSON(`/api/banco/categories${params}`)
}

export function getTrends(year, month, months = 6){
    const params = new URLSearchParams()
    if (year && month){ params.set('year', year); params.set('month', month) }
    params.set('months', months)
    return getJSON(`/api/banco/trends?${params.toString()}`)
}

export function getFixedVariable(year, month){
    const params = (year && month) ? `?year=${year}&month=${month}` : ''
    return getJSON(`/api/banco/fixed-variable${params}`)
}

export function getDigest(topic){
    return getJSON(`/api/digest?topic=${topic}`)
}

export function refreshDigest(topic){
    return getJSON(`/api/digest/refresh?topic=${topic}`, {method: 'POST'})
}
