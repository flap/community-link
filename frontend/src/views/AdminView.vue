<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  createCommunity, createLink, createSection,
  deleteCommunity, deleteLink, deleteSection,
  getAdminToken, listCommunities, listLinks, listSections,
  listThemes, setAdminToken,
} from '../api'

const LINK_TYPES = [
  'video', 'site', 'calendario', 'pessoa', 'linkedin',
  'instagram', 'tiktok', 'builder_center', 'meetup',
]

const token = ref(getAdminToken())
const authed = ref(false)
const error = ref('')
const themes = ref({})

const communities = ref([])
const selected = ref(null)
const sections = ref([])
const links = ref([])

const newCommunity = ref({ name: '', slug: '', description: '', theme: 'default' })
const newSection = ref({ title: '', order: 0 })
const newLink = ref({ section_id: '', type: 'site', title: '', url: '', emoji: '', embed: false })

const themeNames = computed(() => Object.keys(themes.value))

function saveToken() {
  setAdminToken(token.value.trim())
  loadCommunities()
}

async function loadCommunities() {
  error.value = ''
  try {
    themes.value = await listThemes()
    communities.value = await listCommunities()
    authed.value = true
  } catch (e) {
    authed.value = false
    error.value = e.message
  }
}

async function addCommunity() {
  error.value = ''
  try {
    await createCommunity({ ...newCommunity.value })
    newCommunity.value = { name: '', slug: '', description: '', theme: 'default' }
    await loadCommunities()
  } catch (e) { error.value = e.message }
}

async function removeCommunity(slug) {
  if (!confirm(`Excluir a comunidade "${slug}"? Esta ação remove seções e links.`)) return
  try {
    await deleteCommunity(slug)
    if (selected.value === slug) selected.value = null
    await loadCommunities()
  } catch (e) { error.value = e.message }
}

async function selectCommunity(slug) {
  selected.value = slug
  await refreshContent()
}

async function refreshContent() {
  if (!selected.value) return
  sections.value = await listSections(selected.value)
  links.value = await listLinks(selected.value)
  if (sections.value.length && !newLink.value.section_id) {
    newLink.value.section_id = sections.value[0].id
  }
}

async function addSection() {
  try {
    await createSection(selected.value, { ...newSection.value })
    newSection.value = { title: '', order: 0 }
    await refreshContent()
  } catch (e) { error.value = e.message }
}

async function removeSection(id) {
  if (!confirm('Excluir esta seção e seus links?')) return
  try { await deleteSection(selected.value, id); await refreshContent() }
  catch (e) { error.value = e.message }
}

async function addLink() {
  error.value = ''
  try {
    const payload = { ...newLink.value }
    if (!payload.emoji) delete payload.emoji
    await createLink(selected.value, payload)
    newLink.value = { section_id: payload.section_id, type: 'site', title: '', url: '', emoji: '', embed: false }
    await refreshContent()
  } catch (e) { error.value = e.message }
}

async function removeLink(id) {
  try { await deleteLink(selected.value, id); await refreshContent() }
  catch (e) { error.value = e.message }
}

function sectionName(id) {
  return sections.value.find((s) => s.id === id)?.title || '—'
}

onMounted(() => { if (token.value) loadCommunities() })
</script>

<template>
  <div class="container wide">
    <div class="spread">
      <h1>Administração</h1>
      <RouterLink class="btn secondary" to="/">Início</RouterLink>
    </div>

    <!-- Login (credencial fixa do MVP) -->
    <div class="card">
      <label>Credencial administrativa (token)</label>
      <div class="row">
        <input v-model="token" type="password" placeholder="Bearer token" style="flex:1" />
        <button class="btn" @click="saveToken">Entrar</button>
      </div>
      <p class="muted">MVP: token fixo definido no backend (CL_ADMIN_TOKEN).</p>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="authed">
      <!-- Nova comunidade -->
      <div class="card">
        <h3 style="margin-top:0">Nova comunidade</h3>
        <div class="grid">
          <div>
            <label>Nome</label>
            <input v-model="newCommunity.name" placeholder="AWS Community Brasil" />
          </div>
          <div>
            <label>Slug (URL)</label>
            <input v-model="newCommunity.slug" placeholder="aws-community-br" />
          </div>
          <div>
            <label>Descrição</label>
            <input v-model="newCommunity.description" placeholder="Comunidade de builders AWS" />
          </div>
          <div>
            <label>Tema</label>
            <select v-model="newCommunity.theme">
              <option v-for="t in themeNames" :key="t" :value="t">{{ themes[t].label }}</option>
            </select>
          </div>
        </div>
        <div class="row" style="margin-top:12px">
          <button class="btn" @click="addCommunity">Criar comunidade</button>
        </div>
      </div>

      <!-- Lista de comunidades -->
      <div class="card">
        <h3 style="margin-top:0">Minhas comunidades</h3>
        <p v-if="!communities.length" class="muted">Nenhuma comunidade ainda.</p>
        <div v-for="c in communities" :key="c.slug" class="spread" style="padding:8px 0; border-bottom:1px solid #334155">
          <div>
            <strong>{{ c.name }}</strong>
            <span class="muted"> /{{ c.slug }} · {{ c.theme }}</span>
          </div>
          <div class="row">
            <button class="btn secondary" @click="selectCommunity(c.slug)">Gerenciar</button>
            <a class="btn secondary" :href="`/${c.slug}`" target="_blank">Ver página</a>
            <button class="btn danger" @click="removeCommunity(c.slug)">Excluir</button>
          </div>
        </div>
      </div>

      <!-- Gestão de conteúdo da comunidade selecionada -->
      <div v-if="selected" class="card">
        <h3 style="margin-top:0">Conteúdo · /{{ selected }}</h3>

        <h4>Seções</h4>
        <div class="row" style="margin-bottom:10px">
          <input v-model="newSection.title" placeholder="Título da seção (ex.: Eventos)" style="flex:1" />
          <input v-model.number="newSection.order" type="number" placeholder="ordem" style="width:90px" />
          <button class="btn" @click="addSection">Adicionar</button>
        </div>
        <div v-for="s in sections" :key="s.id" class="spread" style="padding:6px 0">
          <span>{{ s.title }} <span class="muted">(ordem {{ s.order }})</span></span>
          <button class="btn danger" @click="removeSection(s.id)">Excluir</button>
        </div>

        <h4 style="margin-top:20px">Links</h4>
        <p v-if="!sections.length" class="muted">Crie uma seção antes de adicionar links.</p>
        <template v-else>
          <div class="grid">
            <div>
              <label>Seção</label>
              <select v-model="newLink.section_id">
                <option v-for="s in sections" :key="s.id" :value="s.id">{{ s.title }}</option>
              </select>
            </div>
            <div>
              <label>Tipo</label>
              <select v-model="newLink.type">
                <option v-for="t in LINK_TYPES" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div>
              <label>Título</label>
              <input v-model="newLink.title" placeholder="Palestra sobre Lambda" />
            </div>
            <div>
              <label>URL</label>
              <input v-model="newLink.url" placeholder="https://…" />
            </div>
            <div>
              <label>Emoji (opcional)</label>
              <input v-model="newLink.emoji" placeholder="🎥" maxlength="8" />
            </div>
            <div class="row" style="align-items:center; margin-top:24px">
              <input id="embed" v-model="newLink.embed" type="checkbox" style="width:auto" />
              <label for="embed" style="margin:0">Exibir como embed (vídeo)</label>
            </div>
          </div>
          <div class="row" style="margin-top:12px">
            <button class="btn" @click="addLink">Adicionar link</button>
          </div>
        </template>

        <div style="margin-top:16px">
          <div v-for="l in links" :key="l.id" class="spread" style="padding:6px 0; border-bottom:1px solid #334155">
            <span>
              <span v-if="l.emoji">{{ l.emoji }}</span>
              <strong>{{ l.title }}</strong>
              <span class="muted"> · {{ l.type }} · {{ sectionName(l.section_id) }}</span>
            </span>
            <button class="btn danger" @click="removeLink(l.id)">Excluir</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
