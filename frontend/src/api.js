// Cliente HTTP simples para a API do Community Link.
// Autenticação (RF-019/RF-022): com Supabase configurado, usa o access token da
// sessão; sem Supabase (modo static de dev), usa o token fixo do localStorage.
import { getSession } from './supabase'

const BASE = '/api'

export function getAdminToken() {
  return localStorage.getItem('cl_admin_token') || ''
}

export function setAdminToken(token) {
  localStorage.setItem('cl_admin_token', token)
}

export async function getAccessToken() {
  const session = await getSession()
  if (session && session.access_token) return session.access_token
  return getAdminToken()
}

async function request(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) headers['Authorization'] = `Bearer ${await getAccessToken()}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data && data.detail ? data.detail : `Erro ${res.status}`
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    err.status = res.status
    throw err
  }
  return data
}

// -- Público --------------------------------------------------------------
export const listThemes = () => request('/themes')
export const getPublicCommunity = (slug) => request(`/communities/${slug}`)

// -- Admin -----------------------------------------------------------------
export const me = () => request('/admin/me', { auth: true })
export const listCommunities = () => request('/admin/communities', { auth: true })

// Administradores e convites (RF-021)
export const listAdmins = (slug) => request(`/admin/communities/${slug}/admins`, { auth: true })
export const inviteAdmin = (slug, email) =>
  request(`/admin/communities/${slug}/admins`, { method: 'POST', body: { email }, auth: true })
export const removeAdmin = (slug, sub) =>
  request(`/admin/communities/${slug}/admins/${encodeURIComponent(sub)}`, { method: 'DELETE', auth: true })
export const removeInvite = (slug, email) =>
  request(`/admin/communities/${slug}/invites/${encodeURIComponent(email)}`, { method: 'DELETE', auth: true })

// Upload de imagem (foto de destaque — RF-007). Retorna { image_url }.
export async function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/admin/uploads`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${await getAccessToken()}` },
    body: form,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data && data.detail ? data.detail : `Erro ${res.status}`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return data.image_url
}
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
