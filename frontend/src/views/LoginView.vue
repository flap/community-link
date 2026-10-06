<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { authEnabled, getSession, providerLabels, socialProviders, supabase } from '../supabase'
import { setAdminToken } from '../api'

const router = useRouter()

const mode = ref('login') // login | signup | reset
const email = ref('')
const password = ref('')
const staticToken = ref('')
const error = ref('')
const info = ref('')
const busy = ref(false)

const redirectTo = `${window.location.origin}/admin`

function friendly(message) {
  const m = (message || '').toLowerCase()
  if (m.includes('invalid login credentials')) return 'E-mail ou senha inválidos.'
  if (m.includes('email not confirmed')) return 'Confirme seu e-mail antes de entrar (verifique sua caixa de entrada).'
  if (m.includes('user already registered')) return 'Este e-mail já está cadastrado. Faça login.'
  if (m.includes('password should be at least')) return 'A senha precisa ter pelo menos 6 caracteres.'
  if (m.includes('rate limit')) return 'Muitas tentativas. Aguarde um instante e tente novamente.'
  return message || 'Não foi possível autenticar.'
}

async function run(fn) {
  error.value = ''
  info.value = ''
  busy.value = true
  try { await fn() } catch (e) { error.value = friendly(e.message) } finally { busy.value = false }
}

function submitEmail() {
  return run(async () => {
    if (mode.value === 'login') {
      const { error: e } = await supabase.auth.signInWithPassword({ email: email.value, password: password.value })
      if (e) throw e
      router.push('/admin')
    } else if (mode.value === 'signup') {
      const { data, error: e } = await supabase.auth.signUp({
        email: email.value, password: password.value, options: { emailRedirectTo: redirectTo },
      })
      if (e) throw e
      if (data.session) router.push('/admin')
      else info.value = 'Cadastro realizado! Verifique seu e-mail para confirmar a conta.'
    } else {
      const { error: e } = await supabase.auth.resetPasswordForEmail(email.value, { redirectTo })
      if (e) throw e
      info.value = 'Enviamos um link de redefinição de senha para o seu e-mail.'
    }
  })
}

function social(provider) {
  return run(async () => {
    const { error: e } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo } })
    if (e) throw e
  })
}

function submitStatic() {
  setAdminToken(staticToken.value.trim())
  router.push('/admin')
}

onMounted(async () => {
  if (authEnabled && (await getSession())) router.replace('/admin')
})
</script>

<template>
  <div>
    <header class="site-header">
      <RouterLink to="/" class="brand" style="text-decoration:none;color:inherit">community<span class="accent">.link</span></RouterLink>
      <nav><RouterLink to="/">Início</RouterLink></nav>
    </header>

    <div class="login-wrap">
      <div class="card login-card">
        <span class="pill"><span class="dot"></span> Área administrativa</span>
        <h1 class="login-title">
          {{ mode === 'signup' ? 'Criar conta' : mode === 'reset' ? 'Recuperar senha' : 'Entrar' }}
        </h1>
        <p class="muted">Gerencie as páginas das suas comunidades.</p>

        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="info" class="info">{{ info }}</p>

        <!-- Supabase Auth: e-mail/senha + social (RF-019/RF-020) -->
        <template v-if="authEnabled">
          <div v-if="socialProviders.length && mode !== 'reset'" class="social-list">
            <button
              v-for="p in socialProviders" :key="p"
              class="btn secondary social-btn" :disabled="busy" @click="social(p)"
            >
              Continuar com {{ providerLabels[p] || p }}
            </button>
          </div>
          <div v-if="socialProviders.length && mode !== 'reset'" class="divider"><span>ou</span></div>

          <form @submit.prevent="submitEmail">
            <label for="email">E-mail</label>
            <input id="email" v-model="email" type="email" required autocomplete="email" placeholder="voce@exemplo.com" />

            <template v-if="mode !== 'reset'">
              <label for="password">Senha</label>
              <input
                id="password" v-model="password" type="password" required minlength="6"
                :autocomplete="mode === 'signup' ? 'new-password' : 'current-password'"
                placeholder="mínimo 6 caracteres"
              />
            </template>

            <button class="btn login-submit" type="submit" :disabled="busy">
              {{ busy ? 'Aguarde…' : mode === 'signup' ? 'Criar conta' : mode === 'reset' ? 'Enviar link' : 'Entrar' }}
            </button>
          </form>

          <div class="login-links">
            <template v-if="mode === 'login'">
              <a href="#" @click.prevent="mode = 'signup'">Criar conta</a>
              <a href="#" @click.prevent="mode = 'reset'">Esqueci minha senha</a>
            </template>
            <a v-else href="#" @click.prevent="mode = 'login'">Já tenho conta — entrar</a>
          </div>
        </template>

        <!-- Fallback: modo static (dev) sem Supabase configurado (RF-022) -->
        <template v-else>
          <p class="muted">
            Supabase não configurado (<code>VITE_SUPABASE_URL</code>). Modo de desenvolvimento:
            informe a credencial fixa do backend.
          </p>
          <form @submit.prevent="submitStatic">
            <label for="token">Credencial (CL_ADMIN_TOKEN)</label>
            <input id="token" v-model="staticToken" type="password" required />
            <button class="btn login-submit" type="submit">Entrar</button>
          </form>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrap { display: flex; justify-content: center; padding: 48px 16px 80px; }
.login-card { width: 100%; max-width: 440px; padding: 28px; }
.login-title { font-size: 28px; font-weight: 800; margin: 14px 0 4px; }
.social-list { display: grid; gap: 8px; margin: 18px 0 6px; }
.social-btn { justify-content: center; width: 100%; }
.divider { display: flex; align-items: center; gap: 12px; color: var(--muted); font-size: 12px; margin: 14px 0 6px; }
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.12); }
.login-submit { width: 100%; justify-content: center; margin-top: 16px; }
.login-links { display: flex; justify-content: space-between; margin-top: 14px; font-size: 14px; }
.info { color: #86efac; font-size: 13px; margin: 8px 0; }
</style>
