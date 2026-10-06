<script setup>
import { RouterLink } from 'vue-router'
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
        <strong style="color: var(--accent)">awscommunity.com.br/sua-comunidade</strong>.
      </p>
      <RouterLink class="btn" to="/admin">Área administrativa ↗</RouterLink>
    </section>

    <div class="container">
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
