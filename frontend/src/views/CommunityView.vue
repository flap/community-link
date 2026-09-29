<script setup>
import { onMounted, ref, watch } from 'vue'
import { getPublicCommunity, listThemes } from '../api'

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

            <!-- Link comum / fallback -->
            <a v-else class="link-card" :href="link.url" target="_blank" rel="noopener">
              <span v-if="link.emoji" class="link-emoji">{{ link.emoji }}</span>
              <img v-if="link.image_url" :src="link.image_url" class="link-thumb" :alt="link.title" />
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
    </div>
  </div>
</template>
