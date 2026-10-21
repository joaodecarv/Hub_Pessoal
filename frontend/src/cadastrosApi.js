// Contas, categorias e regras (Configurações). Errors carry the API's readable
// Portuguese `detail` (422 validation, 409 conflicts) as the Error message.
import { sendJson } from './api.js'

const BASE = '/api/banco/cadastros'

const request = (path, method = 'GET', body) => sendJson(`${BASE}${path}`, method, body)

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
