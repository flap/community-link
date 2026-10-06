<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  createCommunity, createLink, createSection,
  deleteCommunity, deleteLink, deleteSection,
  getAdminToken, listCommunities, listLinks, listSections,
  listThemes, reorderLinks, reorderSections, setAdminToken,
  updateCommunity, updateLink, updateSection, uploadImage,
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

const newCommunity = ref({ name: '', slug: '', description: '', theme: 'aws' })
const newSection = ref({ title: '' })
const newLink = ref({ section_id: '', type: 'site', title: '', url: '', emoji: '', image_url: '', embed: false })

// edição inline
const editCommunity = ref(null)      // objeto editável da comunidade selecionada
const editingSectionId = ref(null)
const sectionDraft = ref({ title: '' })
const editingLinkId = ref(null)
const linkDraft = ref({})

const themeNames = computed(() => Object.keys(themes.value))
const selectedCommunity = computed(() => communities.value.find((c) => c.slug === selected.value))
const uploading = ref(false)

async function handleUpload(event, target) {
  // `target` é o objeto reativo (newLink/linkDraft) já desembrulhado pelo template.
  const file = event.target.files && event.target.files[0]
  if (!file) return
  error.value = ''
  uploading.value = true
  try {
    const url = await uploadImage(file)
    target.image_url = url
  } catch (e) { error.value = e.message }
  finally { uploading.value = false; event.target.value = '' }
}

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
    newCommunity.value = { name: '', slug: '', description: '', theme: 'aws' }
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
  const c = selectedCommunity.value
  // slug é imutável (RF-015) — não entra no draft de edição
  editCommunity.value = c
    ? { name: c.name, description: c.description || '', theme: c.theme, logo_url: c.logo_url || '' }
    : null
  await refreshContent()
}

async function saveCommunity() {
  error.value = ''
  try {
    await updateCommunity(selected.value, { ...editCommunity.value })
    await loadCommunities()
  } catch (e) { error.value = e.message }
}

async function refreshContent() {
  if (!selected.value) return
  sections.value = await listSections(selected.value)
  links.value = await listLinks(selected.value)
  if (sections.value.length && !newLink.value.section_id) {
    newLink.value.section_id = sections.value[0].id
  }
}

function linksOf(sectionId) {
  return links.value
    .filter((l) => l.section_id === sectionId)
    .sort((a, b) => a.order - b.order)
}

// -- Seções ----------------------------------------------------------------
async function addSection() {
  try {
    await createSection(selected.value, { title: newSection.value.title, order: sections.value.length })
    newSection.value = { title: '' }
    await refreshContent()
  } catch (e) { error.value = e.message }
}

function startEditSection(s) {
  editingSectionId.value = s.id
  sectionDraft.value = { title: s.title }
}
async function saveSection(id) {
  try {
    await updateSection(selected.value, id, { ...sectionDraft.value })
    editingSectionId.value = null
    await refreshContent()
  } catch (e) { error.value = e.message }
}
async function removeSection(id) {
  if (!confirm('Excluir esta seção e seus links?')) return
  try { await deleteSection(selected.value, id); await refreshContent() }
  catch (e) { error.value = e.message }
}
async function moveSection(index, dir) {
  const ids = sections.value.map((s) => s.id)
  const j = index + dir
  if (j < 0 || j >= ids.length) return
  ;[ids[index], ids[j]] = [ids[j], ids[index]]
  try { sections.value = await reorderSections(selected.value, ids) }
  catch (e) { error.value = e.message }
}

// -- Links -----------------------------------------------------------------
async function addLink() {
  error.value = ''
  try {
    const payload = { ...newLink.value, order: linksOf(newLink.value.section_id).length }
    if (!payload.emoji) delete payload.emoji
    if (!payload.image_url) delete payload.image_url
    await createLink(selected.value, payload)
    newLink.value = { section_id: payload.section_id, type: 'site', title: '', url: '', emoji: '', image_url: '', embed: false }
    await refreshContent()
  } catch (e) { error.value = e.message }
}

function startEditLink(l) {
  editingLinkId.value = l.id
  linkDraft.value = {
    type: l.type, title: l.title, url: l.url, emoji: l.emoji || '',
    author: l.author || '', embed: l.embed, section_id: l.section_id,
    image_url: l.image_url || '',
  }
}
async function saveLink(id) {
  try {
    const payload = { ...linkDraft.value }
    if (!payload.emoji) payload.emoji = null
    if (!payload.image_url) payload.image_url = null
    await updateLink(selected.value, id, payload)
    editingLinkId.value = null
    await refreshContent()
  } catch (e) { error.value = e.message }
}
async function removeLink(id) {
  try { await deleteLink(selected.value, id); await refreshContent() }
  catch (e) { error.value = e.message }
}
async function moveLink(sectionId, index, dir) {
  const ids = linksOf(sectionId).map((l) => l.id)
  const j = index + dir
  if (j < 0 || j >= ids.length) return
  ;[ids[index], ids[j]] = [ids[j], ids[index]]
  try { await reorderLinks(selected.value, sectionId, ids); await refreshContent() }
  catch (e) { error.value = e.message }
}

// -- Drag and drop ---------------------------------------------------------
const drag = ref({ kind: null, sectionId: null, id: null })

function onDragStart(kind, id, sectionId = null) {
  drag.value = { kind, id, sectionId }
}
async function onDropSection(targetId) {
  if (drag.value.kind !== 'section' || drag.value.id === targetId) return
  const ids = sections.value.map((s) => s.id)
  const from = ids.indexOf(drag.value.id)
  const to = ids.indexOf(targetId)
  ids.splice(to, 0, ids.splice(from, 1)[0])
  try { sections.value = await reorderSections(selected.value, ids) }
  catch (e) { error.value = e.message }
  drag.value = { kind: null, sectionId: null, id: null }
}
async function onDropLink(sectionId, targetId) {
  if (drag.value.kind !== 'link' || drag.value.sectionId !== sectionId) return
  const ids = linksOf(sectionId).map((l) => l.id)
  const from = ids.indexOf(drag.value.id)
  const to = ids.indexOf(targetId)
  if (from === -1 || to === -1 || from === to) return
  ids.splice(to, 0, ids.splice(from, 1)[0])
  try { await reorderLinks(selected.value, sectionId, ids); await refreshContent() }
  catch (e) { error.value = e.message }
  drag.value = { kind: null, sectionId: null, id: null }
}

onMounted(() => { if (token.value) loadCommunities() })
</script>

<template>
  <div>
    <header class="site-header">
      <span class="brand">community<span class="accent">.link</span></span>
      <nav>
        <RouterLink to="/">Início</RouterLink>
        <RouterLink to="/admin">Administração</RouterLink>
      </nav>
    </header>

    <div class="container wide">
      <h1>Administração</h1>

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
            <div><label>Nome</label><input v-model="newCommunity.name" placeholder="AWS Community Brasil" /></div>
            <div><label>Slug (URL)</label><input v-model="newCommunity.slug" placeholder="aws-community-br" /></div>
            <div><label>Descrição</label><input v-model="newCommunity.description" placeholder="Comunidade de builders AWS" /></div>
            <div>
              <label>Tema</label>
              <select v-model="newCommunity.theme">
                <option v-for="t in themeNames" :key="t" :value="t">{{ themes[t].label }}</option>
              </select>
            </div>
          </div>
          <div class="row" style="margin-top:12px"><button class="btn" @click="addCommunity">Criar comunidade</button></div>
        </div>

        <!-- Lista de comunidades -->
        <div class="card">
          <h3 style="margin-top:0">Minhas comunidades</h3>
          <p v-if="!communities.length" class="muted">Nenhuma comunidade ainda.</p>
          <div v-for="c in communities" :key="c.slug" class="spread" style="padding:8px 0; border-bottom:1px solid #334155">
            <div><strong>{{ c.name }}</strong><span class="muted"> /{{ c.slug }} · {{ c.theme }}</span></div>
            <div class="row">
              <button class="btn secondary" @click="selectCommunity(c.slug)">Gerenciar</button>
              <a class="btn secondary" :href="`/${c.slug}`" target="_blank">Ver página</a>
              <button class="btn danger" @click="removeCommunity(c.slug)">Excluir</button>
            </div>
          </div>
        </div>

        <!-- Gestão de conteúdo da comunidade selecionada -->
        <div v-if="selected && editCommunity" class="card">
          <h3 style="margin-top:0">Editar comunidade · /{{ selected }}</h3>
          <div class="grid">
            <div><label>Nome</label><input v-model="editCommunity.name" /></div>
            <div><label>Slug (imutável)</label><input :value="selected" disabled /></div>
            <div><label>Descrição</label><input v-model="editCommunity.description" /></div>
            <div>
              <label>Tema</label>
              <select v-model="editCommunity.theme">
                <option v-for="t in themeNames" :key="t" :value="t">{{ themes[t].label }}</option>
              </select>
            </div>
            <div><label>Logo (URL)</label><input v-model="editCommunity.logo_url" placeholder="https://…" /></div>
          </div>
          <div class="row" style="margin-top:12px"><button class="btn" @click="saveCommunity">Salvar comunidade</button></div>
        </div>

        <!-- Seções e links -->
        <div v-if="selected" class="card">
          <h3 style="margin-top:0">Seções e links · /{{ selected }}</h3>
          <p class="muted">Reordene com os botões ↑ ↓ ou arrastando os itens.</p>

          <div class="row" style="margin:10px 0">
            <input v-model="newSection.title" placeholder="Nova seção (ex.: Eventos)" style="flex:1" />
            <button class="btn" @click="addSection">Adicionar seção</button>
          </div>

          <div
            v-for="(s, si) in sections" :key="s.id"
            class="section-block"
            draggable="true"
            @dragstart="onDragStart('section', s.id)"
            @dragover.prevent
            @drop="onDropSection(s.id)"
          >
            <div class="spread section-head">
              <div class="row" style="flex:1">
                <span class="drag-handle" title="Arraste para reordenar">⠿</span>
                <template v-if="editingSectionId === s.id">
                  <input v-model="sectionDraft.title" style="flex:1" />
                  <button class="btn" @click="saveSection(s.id)">Salvar</button>
                  <button class="btn secondary" @click="editingSectionId = null">Cancelar</button>
                </template>
                <template v-else>
                  <strong style="flex:1">{{ s.title }}</strong>
                  <button class="btn secondary small" @click="startEditSection(s)">Editar</button>
                </template>
              </div>
              <div class="row">
                <button class="btn secondary small" :disabled="si === 0" @click="moveSection(si, -1)">↑</button>
                <button class="btn secondary small" :disabled="si === sections.length - 1" @click="moveSection(si, 1)">↓</button>
                <button class="btn danger small" @click="removeSection(s.id)">Excluir</button>
              </div>
            </div>

            <!-- Links da seção -->
            <div
              v-for="(l, li) in linksOf(s.id)" :key="l.id"
              class="link-row"
              draggable="true"
              @dragstart.stop="onDragStart('link', l.id, s.id)"
              @dragover.prevent
              @drop.stop="onDropLink(s.id, l.id)"
            >
              <template v-if="editingLinkId === l.id">
                <div class="grid" style="width:100%">
                  <div class="row">
                    <select v-model="linkDraft.type" style="flex:1">
                      <option v-for="t in LINK_TYPES" :key="t" :value="t">{{ t }}</option>
                    </select>
                    <input v-model="linkDraft.emoji" placeholder="emoji" style="width:90px" maxlength="8" />
                  </div>
                  <input v-model="linkDraft.title" placeholder="Título" />
                  <input v-model="linkDraft.url" placeholder="https://…" />
                  <div class="row" style="align-items:center">
                    <label style="margin:0">Foto de destaque:</label>
                    <input type="file" accept="image/jpeg,image/png,image/webp"
                           @change="(e) => handleUpload(e, linkDraft)" style="flex:1" />
                    <img v-if="linkDraft.image_url" :src="linkDraft.image_url" class="thumb-preview" alt="preview" />
                    <button v-if="linkDraft.image_url" class="btn secondary small" @click="linkDraft.image_url = ''">Remover</button>
                  </div>
                  <div class="row">
                    <label style="margin:0">Seção:</label>
                    <select v-model="linkDraft.section_id" style="flex:1">
                      <option v-for="sec in sections" :key="sec.id" :value="sec.id">{{ sec.title }}</option>
                    </select>
                    <label style="margin:0"><input type="checkbox" v-model="linkDraft.embed" style="width:auto" /> embed</label>
                  </div>
                  <div class="row">
                    <button class="btn" @click="saveLink(l.id)">Salvar link</button>
                    <button class="btn secondary" @click="editingLinkId = null">Cancelar</button>
                  </div>
                </div>
              </template>
              <template v-else>
                <span class="drag-handle" title="Arraste para reordenar">⠿</span>
                <img v-if="l.image_url" :src="l.image_url" class="thumb-preview" alt="" />
                <span class="link-body">
                  <span v-if="l.emoji">{{ l.emoji }}</span>
                  <strong>{{ l.title }}</strong>
                  <span class="muted"> · {{ l.type }}{{ l.embed ? ' · embed' : '' }}</span>
                </span>
                <span class="row">
                  <button class="btn secondary small" :disabled="li === 0" @click="moveLink(s.id, li, -1)">↑</button>
                  <button class="btn secondary small" :disabled="li === linksOf(s.id).length - 1" @click="moveLink(s.id, li, 1)">↓</button>
                  <button class="btn secondary small" @click="startEditLink(l)">Editar</button>
                  <button class="btn danger small" @click="removeLink(l.id)">Excluir</button>
                </span>
              </template>
            </div>

            <p v-if="!linksOf(s.id).length" class="muted" style="padding:4px 0 0 24px">Sem links nesta seção.</p>
          </div>

          <!-- Adicionar link -->
          <div v-if="sections.length" class="card" style="margin-top:16px; background:#0b1220">
            <h4 style="margin-top:0">Adicionar link</h4>
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
              <div><label>Título</label><input v-model="newLink.title" placeholder="Palestra sobre Lambda" /></div>
              <div><label>URL</label><input v-model="newLink.url" placeholder="https://…" /></div>
              <div><label>Emoji (opcional)</label><input v-model="newLink.emoji" placeholder="🎥" maxlength="8" /></div>
              <div>
                <label>Foto de destaque (opcional)</label>
                <div class="row" style="align-items:center">
                  <input type="file" accept="image/jpeg,image/png,image/webp"
                         @change="(e) => handleUpload(e, newLink)" style="flex:1" />
                  <img v-if="newLink.image_url" :src="newLink.image_url" class="thumb-preview" alt="preview" />
                  <button v-if="newLink.image_url" class="btn secondary small" @click="newLink.image_url = ''">Remover</button>
                </div>
              </div>
              <div class="row" style="align-items:center; margin-top:24px">
                <input id="embed" v-model="newLink.embed" type="checkbox" style="width:auto" />
                <label for="embed" style="margin:0">Exibir como embed (vídeo)</label>
              </div>
            </div>
            <div class="row" style="margin-top:12px">
              <button class="btn" @click="addLink">Adicionar link</button>
              <span v-if="uploading" class="muted">enviando imagem…</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.section-block {
  background: var(--surface);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
}
.section-head { margin-bottom: 8px; }
.link-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; margin: 6px 0 6px 20px;
  background: #0b1220; border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.05);
}
.link-body { flex: 1; }
.drag-handle { cursor: grab; color: var(--muted); user-select: none; font-size: 16px; }
.btn.small { padding: 6px 10px; font-size: 12px; border-radius: 8px; }
.thumb-preview { width: 40px; height: 40px; border-radius: 8px; object-fit: cover; border: 1px solid rgba(255,255,255,0.12); }
</style>
