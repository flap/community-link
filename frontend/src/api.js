// Cliente HTTP simples para a API do Community Link.
// A credencial administrativa (MVP) é um bearer token guardado no localStorage.

const BASE = '/api'

export function getAdminToken() {
  return localStorage.getItem('cl_admin_token') || ''
}

export function setAdminToken(token) {
  localStorage.setItem('cl_admin_token', token)
}

async function request(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) headers['Authorization'] = `Bearer ${getAdminToken()}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data && data.detail ? data.detail : `Erro ${res.status}`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return data
}

// -- Público --------------------------------------------------------------
export const listThemes = () => request('/themes')
export const getPublicCommunity = (slug) => request(`/communities/${slug}`)

// -- Admin -----------------------------------------------------------------
export const listCommunities = () => request('/admin/communities', { auth: true })
export const createCommunity = (payload) =>
  request('/admin/communities', { method: 'POST', body: payload, auth: true })
export const updateCommunity = (slug, payload) =>
  request(`/admin/communities/${slug}`, { method: 'PATCH', body: payload, auth: true })
export const deleteCommunity = (slug) =>
  request(`/admin/communities/${slug}`, { method: 'DELETE', auth: true })

export const listSections = (slug) =>
  request(`/admin/communities/${slug}/sections`, { auth: true })
export const createSection = (slug, payload) =>
  request(`/admin/communities/${slug}/sections`, { method: 'POST', body: payload, auth: true })
export const updateSection = (slug, id, payload) =>
  request(`/admin/communities/${slug}/sections/${id}`, { method: 'PATCH', body: payload, auth: true })
export const deleteSection = (slug, id) =>
  request(`/admin/communities/${slug}/sections/${id}`, { method: 'DELETE', auth: true })
export const reorderSections = (slug, orderedIds) =>
  request(`/admin/communities/${slug}/sections/reorder`, {
    method: 'PUT', body: { ordered_ids: orderedIds }, auth: true,
  })

export const listLinks = (slug) =>
  request(`/admin/communities/${slug}/links`, { auth: true })
export const createLink = (slug, payload) =>
  request(`/admin/communities/${slug}/links`, { method: 'POST', body: payload, auth: true })
export const updateLink = (slug, id, payload) =>
  request(`/admin/communities/${slug}/links/${id}`, { method: 'PATCH', body: payload, auth: true })
export const deleteLink = (slug, id) =>
  request(`/admin/communities/${slug}/links/${id}`, { method: 'DELETE', auth: true })
export const reorderLinks = (slug, sectionId, orderedIds) =>
  request(`/admin/communities/${slug}/sections/${sectionId}/links/reorder`, {
    method: 'PUT', body: { ordered_ids: orderedIds }, auth: true,
  })
