// Tiny fetch wrapper around the backend API.
//
// NOTE (shortcut): the JWT is kept in localStorage for simplicity. This is
// documented in the README as a deliberate MVP trade-off — a production build
// would use an httpOnly cookie + refresh flow to avoid XSS token theft.
const BASE = '/api'

let token = localStorage.getItem('hh_token') || ''

export function setToken(t) {
  token = t
  localStorage.setItem('hh_token', t)
}

export function clearToken() {
  token = ''
  localStorage.removeItem('hh_token')
}

export function hasToken() {
  return !!token
}

async function req(path, opts = {}) {
  const headers = { ...(opts.headers || {}) }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(BASE + path, { ...opts, headers })

  if (res.status === 401) {
    clearToken()
  }
  if (!res.ok) {
    let detail
    try {
      detail = (await res.json()).detail
    } catch {
      detail = res.statusText
    }
    throw new Error(detail || 'Request failed')
  }
  return res.status === 204 ? null : res.json()
}

function jsonBody(data) {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }
}

export const api = {
  async login(email, password) {
    const body = new URLSearchParams({ username: email, password })
    const res = await fetch(BASE + '/auth/login', { method: 'POST', body })
    if (!res.ok) throw new Error('Incorrect email or password')
    const data = await res.json()
    setToken(data.access_token)
    return data
  },
  me: () => req('/auth/me'),

  listHardware(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v != null)
    )
    const qs = new URLSearchParams(clean).toString()
    return req('/hardware' + (qs ? `?${qs}` : ''))
  },
  createHardware: (data) => req('/hardware', { method: 'POST', ...jsonBody(data) }),
  updateHardware: (id, data) =>
    req(`/hardware/${id}`, { method: 'PATCH', ...jsonBody(data) }),
  toggleRepair: (id) => req(`/hardware/${id}/toggle-repair`, { method: 'POST' }),
  deleteHardware: (id) => req(`/hardware/${id}`, { method: 'DELETE' }),

  rent: (id) => req(`/hardware/${id}/rent`, { method: 'POST' }),
  returnItem: (id) => req(`/hardware/${id}/return`, { method: 'POST' }),

  createUser: (data) => req('/auth/users', { method: 'POST', ...jsonBody(data) }),
  listUsers: () => req('/auth/users'),

  aiStatus: () => req('/ai/status'),
  audit: () => req('/ai/audit'),
  search: (query) => req('/ai/search', { method: 'POST', ...jsonBody({ query }) }),
}
