# Community Link — Descritivo de Negócio

## Visão Geral

O **Community Link** é um portal agregador de links (SaaS multi-tenant) com foco em experiência visual de alta qualidade, voltado para **comunidades** e criadores de conteúdo. A proposta é oferecer uma página pública, bonita e fácil de manter, na qual uma comunidade concentra todos os seus links relevantes — vídeos, sites, calendários, redes sociais, perfis de pessoas, eventos no Meetup, perfis no AWS Builder Center — organizados em seções temáticas, com suporte a emojis, fotos de destaque e embeds de conteúdo.

O conceito é análogo a soluções como Linktree, mas com três diferenciais claros:

1. **Foco em comunidades** (não apenas perfil individual), com múltiplos administradores e múltiplas seções de conteúdo.
2. **Tipos de link ricos e específicos** (calendário, Meetup, Builder Center, embeds), além dos genéricos.
3. **Visual profissional e padronizado**, customizável dentro de um conjunto de temas pré-definidos, garantindo qualidade estética sem exigir habilidade de design do usuário.

### Objetivo do Projeto

Permitir que qualquer comunidade crie e mantenha, com baixo esforço, uma página pública agregadora de links visualmente atraente, servindo como ponto central de divulgação e acesso ao seu conteúdo e canais.

### Stakeholders Envolvidos

| Papel | Responsabilidade |
|-------|------------------|
| **Administrador de comunidade** | Cria e edita a página da comunidade, gerencia seções e links, escolhe o tema visual |
| **Visitante (público)** | Acessa a página pública da comunidade e consome/navega pelos links |
| **Equipe do produto** | Desenvolve, opera e evolui a plataforma multi-tenant |
| **Operação/Infra AWS** | Garante disponibilidade, escalabilidade e custo da infraestrutura serverless |

### Escopo Macro da Solução

- Plataforma **multi-tenant**: cada comunidade tem sua própria página pública identificada por um *slug* (ex.: `awscommunity.com.br/minha-comunidade`).
- Área administrativa para criar/editar comunidades, seções e links.
- Renderização pública otimizada e responsiva, com temas customizáveis dentro de padrões oferecidos.
- **Fase 1:** cadastro de comunidade, seções, tipos ricos de link, emojis, embeds, foto de destaque, edição fácil.
- **Fase 2:** filtros (data, tipo de conteúdo) e pesquisa (data, conteúdo, autores, comunidades).

> **Nota sobre autenticação:** o fluxo de acesso definitivo ainda será definido. Para o MVP e testes, o backend utilizará **uma credencial fixa** (autenticação simplificada), a ser substituída por um mecanismo completo em iteração futura.

---

## Situação Atual (As-Is)

Hoje, comunidades que desejam divulgar seus canais e conteúdos enfrentam um cenário fragmentado:

- **Divulgação dispersa:** cada canal (YouTube, Instagram, LinkedIn, Meetup, site próprio, calendário de eventos) vive isolado, e o público precisa procurar cada um separadamente.
- **Ferramentas genéricas de "link na bio":** soluções como Linktree são centradas em perfil individual, com layout limitado, sem o conceito de **seções temáticas** nem de **múltiplos administradores** por página. Os tipos de link são genéricos (apenas URL + rótulo), sem tratamento específico para calendário, Meetup ou Builder Center.
- **Manutenção trabalhosa:** manter uma página de links atualizada costuma exigir edição manual em ferramentas pouco amigáveis, muitas vezes concentrada em uma única pessoa.
- **Baixa qualidade visual:** páginas montadas "na mão" (por exemplo, um HTML estático ou uma seção de site) raramente têm consistência estética e responsividade adequadas.

### Sistemas e Ferramentas Utilizados Hoje

- Agregadores genéricos de link (ex.: Linktree, Bio.link).
- Publicações manuais em redes sociais apontando para diversos destinos.
- Eventualmente páginas estáticas próprias mantidas manualmente.

### Equipe Envolvida e Volumes Operacionais

- Tipicamente **1 pessoa** (o "community manager") mantém os links, o que gera gargalo e desatualização.
- Volume esperado por comunidade: dezenas de links, organizados em poucas seções (ex.: "Eventos", "Vídeos", "Redes Sociais", "Membros").

---

## Desafios e Dores

1. **Fragmentação da divulgação — [Crítico]**
   - **Descrição:** os canais da comunidade estão espalhados e o público não tem um ponto central de acesso.
   - **Impacto operacional:** perda de audiência e engajamento; esforço duplicado de divulgação.
   - **Consequência:** conteúdo relevante não é descoberto; comunidade cresce mais devagar.

2. **Ausência de organização por seções — [Alto]**
   - **Descrição:** ferramentas atuais listam links "empilhados", sem agrupamento temático.
   - **Impacto operacional:** páginas longas e confusas quando há muitos links.
   - **Consequência:** dificuldade de navegação e queda na taxa de clique nos links certos.

3. **Tipos de link genéricos — [Alto]**
   - **Descrição:** não há tratamento específico para calendário, eventos (Meetup), perfis (LinkedIn, Instagram, TikTok, Builder Center) ou embeds.
   - **Impacto operacional:** experiência pobre; o usuário só vê um rótulo e uma URL.
   - **Consequência:** menor atratividade e menor conversão em cliques/inscrições.

4. **Manutenção difícil e centralizada — [Alto]**
   - **Descrição:** atualizar links é trabalhoso e normalmente depende de uma só pessoa.
   - **Impacto operacional:** desatualização frequente; gargalo operacional.
   - **Consequência:** links quebrados ou eventos vencidos expostos ao público.

5. **Baixa qualidade e inconsistência visual — [Médio]**
   - **Descrição:** páginas caseiras não têm padrão estético nem responsividade garantida.
   - **Impacto operacional:** imagem pouco profissional da comunidade.
   - **Consequência:** perda de credibilidade e engajamento.

6. **Falta de descoberta e busca (evolução) — [Médio]**
   - **Descrição:** não há como filtrar ou pesquisar conteúdo por data, tipo, autor ou comunidade.
   - **Impacto operacional:** conteúdo antigo/relevante fica "enterrado".
   - **Consequência:** subaproveitamento do acervo de links.

---

## Oportunidades de Melhoria

### Quick Wins

- **Página única e bonita por comunidade** com URL amigável (slug) — resolve imediatamente a fragmentação.
- **Seções temáticas** para organizar os links — melhora navegação sem esforço extra do usuário.
- **Tipos de link ricos** (ícone/emoji + foto de destaque + embed) — aumenta atratividade e cliques.
- **Edição fácil** (área administrativa simples) — reduz o gargalo de manutenção e permite múltiplos admins.

### Ganhos Esperados com a Plataforma

- **Centralização** de toda a presença digital da comunidade em um só lugar.
- **Redução do esforço de manutenção** por meio de uma interface amigável e colaborativa (múltiplos administradores).
- **Aumento de engajamento** graças ao visual profissional e aos tipos de link ricos.
- **Escalabilidade e baixo custo operacional** com arquitetura serverless na AWS (paga-se pelo uso).

### Métricas de Sucesso Sugeridas

- Nº de comunidades ativas criadas.
- Nº de links publicados por comunidade.
- Tempo médio para criar/atualizar uma página (meta: poucos minutos).
- Taxa de cliques nos links da página pública (métrica de fase futura, quando houver analytics).

---

## Premissas e Restrições

### Premissas

- O produto é **multi-tenant**: várias comunidades convivem na mesma plataforma, isoladas logicamente por identificador (slug/ID de comunidade).
- Um **usuário pode administrar várias comunidades**, e uma **comunidade pode ter múltiplos administradores**.
- A personalização visual é feita **dentro de um conjunto de temas/padrões pré-definidos** pela plataforma (não é um editor livre de design).
- O acesso administrativo no MVP usa **uma credencial fixa no backend** apenas para testes; o fluxo de autenticação definitivo será especificado depois.

### Restrições

- **Tecnológicas:** frontend em **Vue**, backend em **Python/FastAPI**, persistência em **Amazon DynamoDB**, deploy **serverless** (CloudFront + API Gateway + AWS Lambda).
- **Orçamentárias:** priorizar arquitetura de baixo custo e sob demanda (serverless), sem servidores ociosos.
- **Escopo do MVP:** monetização, planos pagos, domínio customizado e analytics de cliques estão **fora do escopo** inicial (candidatos a fases futuras).

### Dependências Externas

- **Provedores de embed** dos tipos de link ricos: YouTube/Vimeo (vídeo), Instagram, TikTok, LinkedIn, Meetup.com, AWS Builder Center e serviços de calendário. A qualidade do embed depende das políticas/oEmbed de cada provedor.
- **Infraestrutura AWS** (CloudFront, API Gateway, Lambda, DynamoDB, S3 para imagens).

---

> Fontes dos insumos: arquivo `ideas.MD` (definição inicial de Fase 1 e Fase 2) e decisões de escopo alinhadas com o solicitante (SaaS multi-tenant; um usuário administra várias comunidades com múltiplos admins; stack Vue + FastAPI + DynamoDB em CloudFront/API Gateway/Lambda; credencial fixa para testes; personalização dentro de temas padrão; monetização/analytics fora do MVP).
