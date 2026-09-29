import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import AdminView from './views/AdminView.vue'
import CommunityView from './views/CommunityView.vue'
import './assets/styles.css'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/admin', name: 'admin', component: AdminView },
  // A página pública da comunidade usa o slug no path (ex.: /aws-community-br)
  { path: '/:slug', name: 'community', component: CommunityView, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
