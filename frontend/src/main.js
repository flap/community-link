import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import AdminView from './views/AdminView.vue'
import LoginView from './views/LoginView.vue'
import CommunityView from './views/CommunityView.vue'
import { authEnabled, getSession } from './supabase'
import { getAdminToken } from './api'
import './assets/styles.css'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAuth: true } },
  // A página pública da comunidade usa o slug no path (ex.: /aws-community-br)
  { path: '/:slug', name: 'community', component: CommunityView, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Guarda de rota (RF-020): /admin exige sessão Supabase (ou token fixo no modo dev).
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const authed = authEnabled ? Boolean(await getSession()) : Boolean(getAdminToken())
  return authed ? true : { name: 'login' }
})

createApp(App).use(router).mount('#app')
