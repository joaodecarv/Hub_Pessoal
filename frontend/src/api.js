



async function getJSON(path, options){
    const response = await fetch(path, options)
    if(!response.ok){
        throw new Error(`Erro ${response.status} ao acessar ${path}`)   
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
    if (!response.ok) throw new Error(`Erro ${response.status} ao carregar as transações`)
    return { items: await response.json(), total: Number(response.headers.get('X-Total-Count')) }
}

// Accounts, categories and goals the transaction form and filters choose from.
export function getTransactionOptions(){
    return getJSON(`/api/banco/transactions/options`)
}

// Sends a write (or any JSON request) and surfaces the API's readable `detail` (422/409) as the Error message.
export async function sendJson(path, method, body){
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
    return sendJson(`/api/banco/transactions`, 'POST', body)
}

export function updateTransaction(id, body){
    return sendJson(`/api/banco/transactions/${id}`, 'PUT', body)
}

export function deleteTransaction(id){
    return sendJson(`/api/banco/transactions/${id}`, 'DELETE')
}

// Goals & budgets (Metas & Orçamentos page). Writes use sendJson.
export function getGoalsOverview(){
    return getJSON(`/api/banco/goals/overview`)
}

export function createGoal(body){
    return sendJson(`/api/banco/goals`, 'POST', body)
}

export function updateGoal(id, body){
    return sendJson(`/api/banco/goals/${id}`, 'PUT', body)
}

export function archiveGoal(id, archived){
    return sendJson(`/api/banco/goals/${id}/archive`, 'PUT', { archived })
}

export function deleteGoal(id){
    return sendJson(`/api/banco/goals/${id}`, 'DELETE')
}

export function getBudgets(year, month){
    return getJSON(`/api/banco/budgets?year=${year}&month=${month}`)
}

// Sets the category's limit from year/month onward.
export function setBudget(categoryId, year, month, limitCents){
    return sendJson(`/api/banco/budgets/${categoryId}`, 'PUT',
        { year, month, limit_cents: limitCents })
}

// Stops budgeting the category from year/month onward.
export function removeBudget(categoryId, year, month){
    return sendJson(`/api/banco/budgets/${categoryId}?year=${year}&month=${month}`, 'DELETE')
}

// Statement import. Preview uploads the file and writes nothing; commit saves the
// rows the user kept. Both surface the API's readable 422 `detail` as the Error message.
export function previewImport({ file, accountId, mapping = null, remap = false }){
    const form = new FormData()
    form.set('file', file)
    form.set('account_id', accountId)
    if (mapping) form.set('mapping', JSON.stringify(mapping))
    if (remap) form.set('remap', 'true')
    return sendJson(`/api/banco/import/preview`, 'POST', form)
}

export function commitImport(body){
    return sendJson(`/api/banco/import/commit`, 'POST', body)
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

// Surfaces the API's readable error (e.g. missing Gemini key) as the Error message.
export function refreshDigest(topic){
    return sendJson(`/api/digest/refresh?topic=${topic}`, 'POST')
}

export function getGeminiStatus(){
    return getJSON(`/api/config/gemini`)
}

export function saveGeminiKey(apiKey){
    return sendJson(`/api/config/gemini`, 'PUT', { api_key: apiKey })
}

export function getAppVersion(){
    return getJSON(`/api/config/version`)
}
