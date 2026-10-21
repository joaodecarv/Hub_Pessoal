// Contas, categorias e regras (Configurações). Errors carry the API's readable
// Portuguese `detail` (422 validation, 409 conflicts) as the Error message.
const BASE = '/api/banco/cadastros'

async function request(path, method = 'GET', body){
    const response = await fetch(`${BASE}${path}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
    })
    if (response.ok) return response.status === 204 ? null : response.json()
    const payload = await response.json().catch(() => null)
    throw new Error(typeof payload?.detail === 'string' ? payload.detail : `Erro ${response.status}`)
}

export const listAccounts = () => request('/accounts')
export const createAccount = (body) => request('/accounts', 'POST', body)
export const updateAccount = (id, body) => request(`/accounts/${id}`, 'PUT', body)
export const deleteAccount = (id) => request(`/accounts/${id}`, 'DELETE')

export const listCategories = () => request('/categories')
export const createCategory = (body) => request('/categories', 'POST', body)
export const updateCategory = (id, body) => request(`/categories/${id}`, 'PUT', body)
export const deleteCategory = (id) => request(`/categories/${id}`, 'DELETE')
// { transactions, rules, budgets } that deleting the category would affect.
export const getCategoryImpact = (id) => request(`/categories/${id}/impact`)

export const listRules = () => request('/rules')
export const createRule = (body) => request('/rules', 'POST', body)
export const updateRule = (id, body) => request(`/rules/${id}`, 'PUT', body)
export const deleteRule = (id) => request(`/rules/${id}`, 'DELETE')
