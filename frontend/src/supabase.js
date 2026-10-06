// Cliente Supabase Auth (RF-019 / RF-020).
// Se VITE_SUPABASE_URL/VITE_SUPABASE_ANON_KEY não estiverem definidos, o app
// opera no modo "static" (credencial fixa de dev) e `supabase` é null.
import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = url && anonKey
  ? createClient(url, anonKey, {
      auth: { flowType: 'pkce', persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : null

export const authEnabled = supabase !== null

// Provedores sociais exibidos na tela de login (precisam estar habilitados no projeto Supabase).
export const socialProviders = (import.meta.env.VITE_SUPABASE_PROVIDERS || 'google,github')
  .split(',')
  .map((p) => p.trim())
  .filter(Boolean)

export const providerLabels = {
  google: 'Google',
  github: 'GitHub',
  linkedin_oidc: 'LinkedIn',
  discord: 'Discord',
  twitter: 'X / Twitter',
  facebook: 'Facebook',
  apple: 'Apple',
  gitlab: 'GitLab',
  azure: 'Microsoft',
  slack_oidc: 'Slack',
}

export async function getSession() {
  if (!supabase) return null
  const { data } = await supabase.auth.getSession()
  return data.session
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut()
}
