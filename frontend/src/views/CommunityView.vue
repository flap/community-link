<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getPublicCommunity, listThemes, searchCommunity } from '../api'

const props = defineProps({ slug: String })

const community = ref(null)
const themes = ref({})
const error = ref('')
const loading = ref(true)

const linkTypeLabel = {
  video: 'Vídeo', site: 'Site', calendario: 'Calendário', pessoa: 'Pessoa',
  linkedin: 'LinkedIn', instagram: 'Instagram', tiktok: 'TikTok',
  builder_center: 'AWS Builder Center', meetup: 'Meetup',
}
const linkTypes = Object.keys(linkTypeLabel)

// -- Filtros/busca da comunidade (RF-012) ---------------------------------
const filters = ref({ q: '', type: '', from: '', to: '' })
const searching = ref(false)
const searchError = ref('')
const results = ref([])

const filtersActive = computed(() =>
  Boolean(filters.value.q || filters.value.type || filters.value.from || filters.value.to)
)

function toggleType(t) {
  filters.value.type = filters.value.type === t ? '' : t
  runSearch()
}

function clearFilters() {
  filters.value = { q: '', type: '', from: '', to: '' }
  results.value = []
  searchError.value = ''
}

let searchTimer = null
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(runSearch, 300)
}

async function runSearch() {
  if (!filtersActive.value) {
    results.value = []
    searchError.value = ''
    return
  }
  searching.value = true
  searchError.value = ''
  try {
    const data = await searchCommunity(props.slug, {
      q: filters.value.q,
      type: filters.value.type,
      from: filters.value.from,
      to: filters.value.to,
      limit: 100,
    })
    results.value = data.results || []
  } catch (e) {
    searchError.value = e.message || 'Erro na busca'
    results.value = []
  } finally {
    searching.value = false
  }
}

function applyTheme() {
  const name = community.value?.theme || 'default'
  const t = themes.value[name]
  if (!t) return
  const root = document.documentElement
  root.style.setProperty('--bg', t.background)
  root.style.setProperty('--surface', t.surface)
  root.style.setProperty('--text', t.text)
  root.style.setProperty('--accent', t.accent)
  if (t.muted) root.style.setProperty('--muted', t.muted)
}

async function load() {
  loading.value = true
  error.value = ''
  clearFilters()
  try {
    themes.value = await listThemes()
    community.value = await getPublicCommunity(props.slug)
    applyTheme()
  } catch (e) {
    error.value = e.message || 'Comunidade não encontrada'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.slug, load)
</script>

<template>
  <div class="community">
    <div class="container">
      <p v-if="loading" class="muted">Carregando…</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <template v-else-if="community">
        <header class="community-header">
          <img
            v-if="community.logo_url"
            :src="community.logo_url"
            class="community-logo"
            :alt="community.name"
          />
          <h1 class="community-title">{{ community.name }}</h1>
          <p v-if="community.description" class="community-desc">
            {{ community.description }}
          </p>
        </header>

        <!-- Barra de filtros/busca (RF-012) -->
        <div class="filter-bar">
          <input
            v-model="filters.q"
            class="filter-search"
            type="search"
            placeholder="Buscar por título, link ou autor…"
            @input="debouncedSearch"
          />
          <div class="filter-chips">
            <button
              v-for="t in linkTypes"
              :key="t"
              type="button"
              class="chip"
              :class="{ active: filters.type === t }"
              @click="toggleType(t)"
            >
              {{ linkTypeLabel[t] }}
            </button>
          </div>
          <div class="filter-dates">
            <label>
              De
              <input v-model="filters.from" type="date" @change="runSearch" />
            </label>
            <label>
              Até
              <input v-model="filters.to" type="date" @change="runSearch" />
            </label>
            <button
              v-if="filtersActive"
              type="button"
              class="btn secondary chip-clear"
              @click="clearFilters"
            >
              Limpar filtros
            </button>
          </div>
        </div>

        <!-- Resultados filtrados (RF-012) -->
        <section v-if="filtersActive" class="search-results">
          <p v-if="searching" class="muted">Buscando…</p>
          <p v-else-if="searchError" class="error">{{ searchError }}</p>
          <p v-else-if="!results.length" class="muted">
            Nenhum link encontrado para os filtros selecionados.
          </p>
          <template v-else>
            <p class="muted">{{ results.length }} resultado(s)</p>
            <a
              v-for="res in results"
              :key="res.link.id"
              class="link-card"
              :href="res.link.url"
              target="_blank"
              rel="noopener"
            >
              <span v-if="res.link.emoji" class="link-emoji">{{ res.link.emoji }}</span>
              <span>
                <span class="link-title">{{ res.link.title }}</span><br />
                <span class="link-type">
                  {{ linkTypeLabel[res.link.type] || res.link.type }}
                  <template v-if="res.link.author"> · {{ res.link.author }}</template>
                </span>
              </span>
            </a>
          </template>
        </section>

        <!-- Conteúdo normal da comunidade (sem filtros ativos) -->
        <template v-else>
        <section v-for="section in community.sections" :key="section.id">
          <h2 class="section-title">{{ section.title }}</h2>

          <template v-for="link in section.links" :key="link.id">
            <!-- Embed (RF-006) -->
            <div v-if="link.embed_data" class="embed-wrap">
              <iframe
                :src="link.embed_data.src"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
                :title="link.title"
              ></iframe>
            </div>

            <!-- Link com foto de destaque (RF-007): imagem grande acima do link -->
            <a
              v-else-if="link.image_url"
              class="feature-card"
              :href="link.url"
              target="_blank"
              rel="noopener"
            >
              <img :src="link.image_url" class="feature-image" :alt="link.title" />
              <span class="feature-body">
                <span class="link-title">
                  <span v-if="link.emoji" class="link-emoji">{{ link.emoji }}</span>
                  {{ link.title }}
                </span>
                <span class="link-type">{{ linkTypeLabel[link.type] || link.type }}</span>
              </span>
            </a>

            <!-- Link comum / fallback -->
            <a v-else class="link-card" :href="link.url" target="_blank" rel="noopener">
              <span v-if="link.emoji" class="link-emoji">{{ link.emoji }}</span>
              <span>
                <span class="link-title">{{ link.title }}</span><br />
                <span class="link-type">{{ linkTypeLabel[link.type] || link.type }}</span>
              </span>
            </a>
          </template>
        </section>

        <p v-if="!community.sections.length" class="muted">
          Esta comunidade ainda não tem conteúdo publicado.
        </p>
        </template>
      </template>
    </div>
  </div>
</template>
