



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

// Filtered, paged list for the Transações page. The body is a plain array and the
// total matching the filters comes in the X-Total-Count header.
export async function listTransactions({ year, month, accountId, categoryId, q, limit = 50, offset = 0 } = {}){
    const params = new URLSearchParams({ limit, offset })
    if (year) params.set('year', year)
    if (month) params.set('month', month)
    if (accountId) params.set('account_id', accountId)
    if (categoryId) params.set('category_id', categoryId)
    if (q) params.set('q', q)
    const response = await fetch(`/api/banco/transactions?${params}`)
    if (!response.ok) throw new Error(`API transactions failed: ${response.status}`)
    return { items: await response.json(), total: Number(response.headers.get('X-Total-Count')) }
}

// Accounts, categories and goals the transaction form and filters choose from.
export function getTransactionOptions(){
    return getJSON(`/api/banco/transactions/options`)
}

// Writes surface the API's readable 422 message (`detail`) as the Error message.
async function writeTransaction(path, method, body){
    // FormData bodies (file uploads) must go out untouched so the browser sets the multipart boundary.
    const isForm = body instanceof FormData
    const response = await fetch(path, {
        method,
        headers: body && !isForm ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    })
    if (response.ok) return response.status === 204 ? null : response.json()
    const payload = await response.json().catch(() => null)
    throw new Error(typeof payload?.detail === 'string' ? payload.detail : `Erro ${response.status}`)
}

export function createTransaction(body){
    return writeTransaction(`/api/banco/transactions`, 'POST', body)
}

export function updateTransaction(id, body){
    return writeTransaction(`/api/banco/transactions/${id}`, 'PUT', body)
}

export function deleteTransaction(id){
    return writeTransaction(`/api/banco/transactions/${id}`, 'DELETE')
}

// Goals & budgets (Metas & Orçamentos page). Writes reuse writeTransaction: it is a
// generic fetch that turns the API's Portuguese 422 `detail` into the Error message.
export function getGoalsOverview(){
    return getJSON(`/api/banco/goals/overview`)
}

export function createGoal(body){
    return writeTransaction(`/api/banco/goals`, 'POST', body)
}

export function updateGoal(id, body){
    return writeTransaction(`/api/banco/goals/${id}`, 'PUT', body)
}

export function archiveGoal(id, archived){
    return writeTransaction(`/api/banco/goals/${id}/archive`, 'PUT', { archived })
}

export function deleteGoal(id){
    return writeTransaction(`/api/banco/goals/${id}`, 'DELETE')
}

export function getBudgets(year, month){
    return getJSON(`/api/banco/budgets?year=${year}&month=${month}`)
}

// Sets the category's limit from year/month onward.
export function setBudget(categoryId, year, month, limitCents){
    return writeTransaction(`/api/banco/budgets/${categoryId}`, 'PUT',
        { year, month, limit_cents: limitCents })
}

// Stops budgeting the category from year/month onward.
export function removeBudget(categoryId, year, month){
    return writeTransaction(`/api/banco/budgets/${categoryId}?year=${year}&month=${month}`, 'DELETE')
}

// Statement import. Preview uploads the file and writes nothing; commit saves the
// rows the user kept. Both surface the API's readable 422 `detail` as the Error message.
export function previewImport({ file, accountId, mapping = null, remap = false }){
    const form = new FormData()
    form.set('file', file)
    form.set('account_id', accountId)
    if (mapping) form.set('mapping', JSON.stringify(mapping))
    if (remap) form.set('remap', 'true')
    return writeTransaction(`/api/banco/import/preview`, 'POST', form)
}

export function commitImport(body){
    return writeTransaction(`/api/banco/import/commit`, 'POST', body)
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
