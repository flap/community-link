<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="container">
    <h1>Community Link</h1>
    <p class="muted">
      Portal agregador de links para comunidades. Crie uma página pública
      bonita e fácil de manter em <strong>awscommunity.com.br/sua-comunidade</strong>.
    </p>
    <div class="row" style="margin-top: 20px">
      <RouterLink class="btn" to="/admin">Área administrativa</RouterLink>
    </div>

    <div class="card" style="margin-top: 32px">
      <h3 style="margin-top: 0">Como funciona</h3>
      <ol class="muted">
        <li>Entre na área administrativa com a credencial de teste.</li>
        <li>Crie sua comunidade (nome, slug e tema).</li>
        <li>Adicione seções e links ricos (vídeo, redes, eventos…).</li>
        <li>Acesse a página pública em <code>/seu-slug</code>.</li>
      </ol>
    </div>
  </div>
</template>
