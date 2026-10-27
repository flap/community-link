<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { searchGlobal } from '../api'

const linkTypeLabel = {
  video: 'Vídeo', site: 'Site', calendario: 'Calendário', pessoa: 'Pessoa',
  linkedin: 'LinkedIn', instagram: 'Instagram', tiktok: 'TikTok',
  builder_center: 'AWS Builder Center', meetup: 'Meetup',
}

const q = ref('')
const results = ref([])
const nextCursor = ref(null)
const searching = ref(false)
const searchError = ref('')
const searched = ref(false)

let searchTimer = null
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => runSearch(false), 300)
}

async function runSearch(append) {
  const term = q.value.trim()
  if (!term) {
    results.value = []
    nextCursor.value = null
    searched.value = false
    searchError.value = ''
    return
  }
  searching.value = true
  searchError.value = ''
  try {
    const params = { q: term, limit: 20 }
    if (append && nextCursor.value) params.cursor = nextCursor.value
    const data = await searchGlobal(params)
    results.value = append ? results.value.concat(data.results || []) : (data.results || [])
    nextCursor.value = data.next_cursor || null
    searched.value = true
  } catch (e) {
    searchError.value = e.message || 'Erro na busca'
  } finally {
    searching.value = false
  }
}

function loadMore() {
  runSearch(true)
}
</script>

<template>
  <div>
    <header class="site-header">
      <span class="brand">community<span class="accent">.link</span></span>
      <nav>
        <RouterLink to="/">Início</RouterLink>
        <RouterLink to="/login">Entrar</RouterLink>
      </nav>
    </header>

    <section class="hero">
      <div class="eyebrow">AWS COMMUNITY</div>
      <h1>Community Link</h1>
      <p>
        Portal agregador de links para comunidades. Crie uma página pública
        bonita e fácil de manter em
        <strong style="color: var(--accent)">link.awscommunity.com.br/sua-comunidade</strong>.
      </p>
      <RouterLink class="btn" to="/admin">Área administrativa ↗</RouterLink>
    </section>

    <div class="container">
      <!-- Busca global entre comunidades (RF-013) -->
      <div class="card">
        <span class="pill"><span class="dot"></span> Buscar</span>
        <input
          v-model="q"
          class="global-search"
          type="search"
          placeholder="Pesquisar links em todas as comunidades…"
          style="margin-top: 12px"
          @input="debouncedSearch"
        />

        <p v-if="searching && !results.length" class="muted" style="margin-top: 12px">
          Buscando…
        </p>
        <p v-else-if="searchError" class="error">{{ searchError }}</p>
        <p
          v-else-if="searched && !results.length"
          class="muted"
          style="margin-top: 12px"
        >
          Nenhum resultado encontrado.
        </p>

        <div v-if="results.length" class="search-results" style="margin-top: 12px">
          <a
            v-for="res in results"
            :key="res.community_slug + '/' + res.link.id"
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
              <br />
              <RouterLink
                class="result-origin"
                :to="`/${res.community_slug}`"
                @click.stop
              >
                em {{ res.community_name }}
              </RouterLink>
            </span>
          </a>

          <button
            v-if="nextCursor"
            type="button"
            class="btn secondary"
            style="margin-top: 8px"
            :disabled="searching"
            @click="loadMore"
          >
            {{ searching ? 'Carregando…' : 'Carregar mais' }}
          </button>
        </div>
      </div>

      <div class="card">
        <span class="pill"><span class="dot"></span> Como funciona</span>
        <ol class="muted" style="margin-top: 12px">
          <li>Entre na área administrativa com a credencial de teste.</li>
          <li>Crie sua comunidade (nome, slug e tema).</li>
          <li>Adicione seções e links ricos (vídeo, redes, eventos…).</li>
          <li>Acesse a página pública em <code>/seu-slug</code>.</li>
        </ol>
      </div>
    </div>
  </div>
</template>
