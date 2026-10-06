# Community Link — Especificação Técnica

## 1. Escopo do Projeto

### 1.1 Objetivo

Desenvolver um **portal agregador de links SaaS multi-tenant** para comunidades, com páginas públicas visualmente atraentes, organizadas em seções, com tipos de link ricos (vídeo, site, calendário, pessoas, LinkedIn, Instagram, TikTok, AWS Builder Center, Meetup), emojis, embeds, foto de destaque e edição fácil. Backend em Python/FastAPI sobre AWS serverless (CloudFront + API Gateway + Lambda), persistência em DynamoDB e frontend em Vue.

### 1.2 Fora de Escopo (MVP)

- Autenticação completa de usuários (o MVP usa **credencial fixa** no backend para testes; o fluxo definitivo será especificado depois).
- Monetização, planos pagos e cobrança.
- Domínio customizado por comunidade.
- Analytics avançado de cliques e dashboards.
- Aplicativos móveis nativos (o site é responsivo).

### 1.3 Fases de Entrega

| Fase | Escopo resumido |
|------|-----------------|
| **Fase 1** | Cadastro de comunidade, seções, tipos ricos de link, emojis, embeds, foto de destaque, temas, edição fácil, página pública |
| **Fase 2** | Filtros (data, tipo de conteúdo) e pesquisa (data, conteúdo, autores, comunidades) |

---

## 2. Requisitos Funcionais

### RF-001: Cadastro de Comunidade
- **Descrição:** permitir criar uma comunidade com nome, slug (URL única), descrição, logo/avatar e tema visual.
- **Regra de negócio:** o slug deve ser único em toda a plataforma (multi-tenant) e conter apenas caracteres URL-safe.
- **Critério de aceite:** dado um slug inédito e válido, ao salvar, a comunidade é criada e acessível em `/{slug}`; slug duplicado ou inválido retorna erro claro.
- **Prioridade:** Must
- **Fase:** 1

### RF-002: Gestão de Múltiplos Administradores
- **Descrição:** uma comunidade pode ter vários administradores; um usuário pode administrar várias comunidades.
- **Regra de negócio:** apenas administradores da comunidade podem editá-la.
- **Critério de aceite:** um admin vê e edita apenas as comunidades às quais pertence; a associação admin↔comunidade é persistida.
- **Prioridade:** Must
- **Fase:** 1
- **Observação:** no MVP com credencial fixa, o vínculo é simplificado; o controle por usuário real depende da autenticação definitiva.

### RF-003: Gestão de Seções de Conteúdo
- **Descrição:** permitir criar, renomear, ordenar e remover seções temáticas dentro da página da comunidade.
- **Regra de negócio:** cada link pertence a uma seção; a ordem das seções é definida pelo admin.
- **Critério de aceite:** as seções aparecem na página pública na ordem definida; remover uma seção com links exige confirmação.
- **Prioridade:** Must
- **Fase:** 1

### RF-004: Cadastro de Links com Tipos Ricos
- **Descrição:** adicionar links com um dos tipos suportados: `video`, `site`, `calendario`, `pessoa`, `linkedin`, `instagram`, `tiktok`, `builder_center`, `meetup`.
- **Regra de negócio:** cada tipo pode ter tratamento visual/embed específico; a URL é validada conforme o tipo.
- **Critério de aceite:** ao escolher um tipo e informar a URL, o link é salvo com o ícone/tratamento correto e exibido na seção escolhida.
- **Prioridade:** Must
- **Fase:** 1

### RF-005: Emojis nos Links
- **Descrição:** permitir associar um emoji a cada link.
- **Regra de negócio:** um emoji opcional por link, armazenado como caractere Unicode.
- **Critério de aceite:** o emoji escolhido aparece junto ao link na página pública.
- **Prioridade:** Should
- **Fase:** 1

### RF-006: Embeds de Conteúdo
- **Descrição:** exibir embed do conteúdo quando o tipo suportar (ex.: vídeo do YouTube/Vimeo, evento do Meetup).
- **Regra de negócio:** o embed é gerado a partir da URL via oEmbed/regras por provedor; se indisponível, exibir como link comum (fallback).
- **Critério de aceite:** um link de vídeo válido renderiza o player embutido; caso o provedor não permita embed, o link abre externamente.
- **Prioridade:** Should
- **Fase:** 1

### RF-007: Foto de Destaque do Link
- **Descrição:** permitir enviar uma imagem de destaque para um link, por upload de arquivo na área administrativa (ao criar ou editar o link).
- **Regra de negócio:** o upload passa por um endpoint dedicado (`POST /api/admin/uploads`) que valida formato (JPEG/PNG/WebP) e tamanho (≤ 5 MB) e retorna a URL pública (`image_url`); em produção as imagens ficam em **S3**, em dev são salvas localmente e servidas pela API em `/api/media/{nome}`.
- **Critério de aceite:** a imagem enviada é exibida como destaque do link na página pública e como miniatura na área administrativa; arquivo com formato não suportado ou acima do limite é rejeitado com mensagem (RN-005).
- **Prioridade:** Should
- **Fase:** 1

### RF-008: Edição Fácil / Publicação
- **Descrição:** área administrativa simples para editar comunidade, seções e links, com publicação imediata.
- **Regra de negócio:** alterações salvas refletem na página pública sem etapa manual de "deploy".
- **Critério de aceite:** ao salvar uma alteração, a página pública correspondente exibe o novo conteúdo em segundos.
- **Prioridade:** Must
- **Fase:** 1

### RF-009: Personalização Visual por Temas
- **Descrição:** permitir escolher tema visual (cores, fundo, estilo) dentro de um conjunto de padrões oferecidos pela plataforma.
- **Regra de negócio:** a customização é limitada aos padrões disponibilizados (não é editor livre).
- **Critério de aceite:** ao selecionar um tema, a página pública passa a usá-lo; os temas disponíveis são listados na área administrativa.
- **Prioridade:** Should
- **Fase:** 1

### RF-010: Página Pública da Comunidade
- **Descrição:** renderizar a página pública responsiva em `/{slug}`, com seções, links, emojis, embeds e tema aplicado.
- **Regra de negócio:** páginas públicas são acessíveis sem autenticação.
- **Critério de aceite:** acessar `/{slug}` exibe o conteúdo publicado, responsivo em desktop e mobile.
- **Prioridade:** Must
- **Fase:** 1

### RF-011: Autenticação Simplificada (MVP)
- **Descrição:** proteger a área administrativa com uma credencial fixa configurada no backend.
- **Regra de negócio:** requisições administrativas exigem a credencial; a página pública não exige.
- **Critério de aceite:** sem a credencial correta, endpoints de escrita retornam 401; com a credencial, a edição é permitida.
- **Prioridade:** Must
- **Fase:** 1
- **Observação:** solução temporária da Fase 1. **Substituída na Fase 2 pela autenticação com Supabase Auth (RF-019 a RF-022).** O modo de credencial fixa permanece disponível apenas para desenvolvimento/testes (`CL_AUTH_MODE=static`).

### RF-012: Filtros de Conteúdo
- **Descrição:** filtrar links por data e por tipo de conteúdo.
- **Regra de negócio:** filtros combináveis; aplicáveis dentro de uma comunidade e/ou globalmente.
- **Critério de aceite:** ao aplicar filtros, apenas os links correspondentes são exibidos.
- **Prioridade:** Should
- **Fase:** 2

### RF-013: Pesquisa de Conteúdo
- **Descrição:** pesquisar por data, conteúdo (texto), autores e comunidades.
- **Regra de negócio:** a busca considera título/descrição dos links, autor e comunidade.
- **Critério de aceite:** uma consulta retorna resultados relevantes, ordenados, com indicação da comunidade de origem.
- **Prioridade:** Could
- **Fase:** 2

### RF-014: Identidade Visual de Referência (AWS Community Day Brasil)
- **Descrição:** o layout e a identidade visual do produto seguem como referência o site **awscommunityday.com.br**.
- **Regra de negócio:** o tema padrão e os componentes visuais adotam a paleta, a tipografia e os padrões de UI descritos na seção "Identidade Visual" abaixo.
- **Critério de aceite:**
  - Fundo escuro azul-marinho, superfícies em tom mais claro, acento laranja AWS.
  - Tipografia **Inter**; títulos fortes.
  - Header fixo translúcido; hero centralizado com CTA laranja; cards arredondados com *pill* de destaque.
- **Prioridade:** Should
- **Fase:** 1

### RF-015: Edição de Dados da Comunidade
- **Descrição:** permitir alterar os dados de uma comunidade já cadastrada: nome, descrição, tema e logo/avatar.
- **Regra de negócio:** o **slug é imutável** após a criação (é a URL pública e a chave multi-tenant). A edição é feita de forma **inline** na área administrativa.
- **Critério de aceite:**
  - [ ] Editar nome/descrição/tema/logo persiste e reflete na página pública.
  - [ ] O campo slug não é editável.
  - [ ] Tema inválido é rejeitado.
- **Prioridade:** Must
- **Fase:** 1

### RF-016: Edição de Seções
- **Descrição:** permitir alterar o **título** de uma seção existente, inline.
- **Regra de negócio:** a seção pertence a uma comunidade; o título é obrigatório.
- **Critério de aceite:**
  - [ ] Alterar o título da seção persiste e reflete na página pública.
- **Prioridade:** Must
- **Fase:** 1

### RF-017: Edição de Links e Movimentação entre Seções
- **Descrição:** permitir alterar os campos de um link (tipo, título, URL, emoji, foto de destaque, autor, embed) e **mover o link para outra seção** da mesma comunidade.
- **Regra de negócio:** a nova seção deve existir e pertencer à mesma comunidade (RN-002). Edição inline.
- **Critério de aceite:**
  - [ ] Alterar campos do link persiste e reflete na página pública.
  - [ ] Mover o link para outra seção o exibe na seção de destino.
  - [ ] Mover para seção inexistente é rejeitado.
- **Prioridade:** Must
- **Fase:** 1

### RF-018: Reordenação de Seções e Links
- **Descrição:** permitir alterar a ordem de exibição de seções e de links dentro de uma seção, por **dois mecanismos**: botões **mover para cima/baixo (↑/↓)** e **arrastar e soltar (drag-and-drop)**.
- **Regra de negócio:** a ordem é persistida no campo `order` de cada item; a página pública respeita essa ordem.
- **Critério de aceite:**
  - [ ] Reordenar via ↑/↓ atualiza a ordem e persiste.
  - [ ] Reordenar via arrastar e soltar atualiza a ordem e persiste.
  - [ ] A página pública exibe seções e links na nova ordem.
- **Prioridade:** Should
- **Fase:** 1

### RF-019: Autenticação de Administradores com Supabase Auth
- **Descrição:** os administradores autenticam-se por meio do **Supabase Auth** (serviço gerenciado), com **e-mail + senha** e com os **provedores sociais suportados pelo Supabase** (Google, GitHub e demais que forem habilitados no projeto).
- **Regra de negócio:** o Supabase emite um **JWT** (access token) após o login; o backend valida assinatura, emissor (`iss`), audiência (`aud=authenticated`) e expiração em toda requisição administrativa. A página pública continua sem autenticação.
- **Critério de aceite:**
  - [ ] Login com e-mail/senha e cadastro (sign-up) funcionam na tela própria.
  - [ ] Login social com ao menos Google e GitHub funciona (provedores configurados no projeto Supabase).
  - [ ] Requisição administrativa sem token válido retorna 401.
  - [ ] Token expirado ou com assinatura inválida retorna 401.
- **Prioridade:** Must
- **Fase:** 2
- **Decisão de stack:** escolhido por ser a opção gerenciada de menor custo em escala (free tier de 50 mil MAU; plano Pro US$ 25/mês inclui 100 mil MAU e cobra US$ 0,00325/MAU excedente — cerca de US$ 2.950/mês a 1 milhão de MAU, contra ~US$ 4.600 do Cognito Lite e ~US$ 9.500 do Auth0).

### RF-020: Tela de Login Própria
- **Descrição:** a autenticação usa uma **tela própria** no frontend Vue (não a UI hospedada do provedor), seguindo a identidade visual do produto (RF-014).
- **Regra de negócio:** a tela oferece login/cadastro por e-mail+senha, botões dos provedores sociais habilitados e recuperação de senha; usa o SDK `@supabase/supabase-js` com o fluxo **PKCE**. Após o login, o usuário é redirecionado à área administrativa.
- **Critério de aceite:**
  - [ ] Tela de login no padrão visual do tema `aws`.
  - [ ] Erros de autenticação exibidos de forma amigável.
  - [ ] Sessão persistida e renovada automaticamente pelo SDK; logout disponível no header.
- **Prioridade:** Must
- **Fase:** 2

### RF-021: Autorização por Comunidade (Administradores)
- **Descrição:** a autorização (quem pode editar qual comunidade) é feita **na aplicação**, com base na identidade autenticada (`sub` e `email` do JWT), concretizando o RF-002.
- **Regra de negócio:**
  - Quem cria a comunidade torna-se automaticamente seu administrador.
  - Um administrador pode **convidar outro administrador por e-mail**; o convite é efetivado no primeiro acesso autenticado do convidado (match pelo `email` do token), sem necessidade de chaves privilegiadas do Supabase no backend.
  - Toda operação de escrita em uma comunidade exige que o usuário seja administrador dela; caso contrário, **403**.
  - A listagem administrativa mostra apenas as comunidades do usuário.
- **Critério de aceite:**
  - [ ] Criador vira admin; outro usuário autenticado recebe 403 ao editar.
  - [ ] Após convite por e-mail, o convidado passa a editar a comunidade.
  - [ ] Admin pode listar e remover administradores (não pode remover o último).
- **Prioridade:** Must
- **Fase:** 2

### RF-022: Compatibilidade de Modos de Autenticação
- **Descrição:** o backend suporta dois modos, selecionados por configuração: `supabase` (produção) e `static` (credencial fixa, apenas dev/testes — RF-011).
- **Regra de negócio:** em `static`, o usuário autenticado é um administrador sintético de desenvolvimento; em `supabase`, a identidade vem do JWT. A lógica de autorização (RF-021) é a mesma nos dois modos.
- **Critério de aceite:**
  - [ ] Testes automatizados cobrem ambos os modos.
  - [ ] Modo padrão em produção é `supabase`.
- **Prioridade:** Should
- **Fase:** 2

---

## Identidade Visual (Referência: awscommunityday.com.br)

O design segue a linguagem visual do **AWS Community Day Brasil** (`awscommunityday.com.br`):

### Paleta de cores

| Token | Valor | Uso |
|-------|-------|-----|
| `background` | `#0f1729` | Fundo principal (azul-marinho escuro) |
| `surface` | `#1d283a` | Cards e superfícies elevadas |
| `text` | `#ffffff` | Texto principal |
| `muted` | `#94a3b8` | Texto secundário |
| `accent` | `#ff8800` | Cor de destaque AWS (CTAs, pills, links) |

### Tipografia
- Família **Inter** (com fallback sans-serif do sistema).
- Títulos em peso forte (700–800); *hero* com título grande e caixa alta.

### Padrões de UI
- **Header fixo** translúcido (fundo `rgba(15,23,41,0.8)` + blur), logo à esquerda e navegação à direita, borda inferior sutil.
- **Hero centralizado**: título grande, subtítulo em `muted`, botão CTA laranja arredondado.
- **Cards** com cantos arredondados (radius ~16px), possível imagem de destaque e **pill** de status em laranja.
- **Botões** primários em laranja com texto escuro; secundários com contorno.

> Esta identidade é materializada no tema **`aws`** (tema padrão do produto) e nos componentes do frontend.

---

## 3. Requisitos Não-Funcionais

### RNF-001: Escalabilidade Serverless
- **Categoria:** Disponibilidade / Escalabilidade
- **Descrição:** a arquitetura deve escalar automaticamente com a demanda, sem servidores fixos.
- **Métrica:** suportar picos de acesso sem degradação perceptível; escalonamento automático via Lambda.

### RNF-002: Performance de Página Pública
- **Categoria:** Performance
- **Descrição:** páginas públicas devem carregar rapidamente com apoio de CDN.
- **Métrica:** TTFB < 200 ms via CloudFront (conteúdo cacheável); renderização inicial < 2 s.

### RNF-003: Segurança Básica
- **Categoria:** Segurança
- **Descrição:** proteger endpoints de escrita, validar entradas, servir tudo sobre HTTPS.
- **Métrica:** 100% do tráfego em HTTPS; endpoints administrativos exigem credencial; validação de payloads.

### RNF-004: Responsividade
- **Categoria:** Usabilidade
- **Descrição:** interface pública e administrativa responsivas.
- **Métrica:** layout funcional em larguras de 320 px a 1920 px.

### RNF-005: Custo Sob Demanda
- **Categoria:** Custo/Operação
- **Descrição:** priorizar serviços com cobrança por uso (Lambda, DynamoDB on-demand, S3, CloudFront).
- **Métrica:** custo próximo de zero em baixo tráfego; crescimento proporcional ao uso.

### RNF-006: Isolamento Multi-Tenant
- **Categoria:** Segurança / Arquitetura
- **Descrição:** dados de cada comunidade isolados logicamente por identificador.
- **Métrica:** nenhuma requisição consegue ler/gravar dados de comunidade à qual não pertence.

---

## 4. Integrações

### INT-001: Frontend Vue ↔ API FastAPI
- **Direção:** Bidirecional
- **Protocolo:** API REST (JSON) sobre HTTPS
- **Dados trafegados:** comunidades, seções, links, temas, uploads (metadados)
- **Frequência:** Real-time (on-demand)
- **Fallback:** exibir estado de erro amigável no frontend em caso de falha da API

### INT-002: API ↔ DynamoDB
- **Direção:** Bidirecional
- **Protocolo:** SDK AWS (boto3)
- **Dados trafegados:** entidades de comunidade, seção, link, admin
- **Frequência:** Real-time
- **Fallback:** retry com backoff; retornar erro 5xx tratado

### INT-003: API ↔ S3 (imagens)
- **Direção:** Bidirecional
- **Protocolo:** SDK AWS / URLs pré-assinadas
- **Dados trafegados:** fotos de destaque e logos
- **Frequência:** On-demand (upload/leitura)
- **Fallback:** rejeitar upload inválido; usar imagem placeholder se ausente

### INT-004: Página Pública ↔ Provedores de Embed
- **Direção:** Unidirecional (leitura de embed)
- **Protocolo:** oEmbed / iframe por provedor (YouTube, Vimeo, Instagram, TikTok, LinkedIn, Meetup, AWS Builder Center, calendário)
- **Dados trafegados:** metadados/HTML de embed a partir da URL
- **Frequência:** On-demand na renderização
- **Fallback:** se o provedor não permitir embed, exibir link externo com ícone do tipo

### INT-005: Entrega via CloudFront + API Gateway
- **Direção:** Unidirecional (requisição do cliente)
- **Protocolo:** HTTPS
- **Dados trafegados:** assets do frontend e respostas de API
- **Frequência:** Real-time
- **Fallback:** páginas de erro padronizadas (4xx/5xx)

### INT-006: Frontend/Backend ↔ Supabase Auth (Fase 2)
- **Direção:** Bidirecional (frontend ↔ Supabase para login; backend ← Supabase para chaves de verificação)
- **Protocolo:** HTTPS — SDK `@supabase/supabase-js` no frontend (fluxo PKCE); no backend, validação do JWT via **JWKS** (`/auth/v1/.well-known/jwks.json`, chaves assimétricas) ou, para projetos legados, via **JWT secret** (HS256) configurado em variável de ambiente
- **Dados trafegados:** credenciais do usuário (somente frontend ↔ Supabase), access token JWT (frontend → backend no header `Authorization: Bearer`), chaves públicas (Supabase → backend, com cache)
- **Frequência:** Real-time; JWKS em cache (ex.: 1 h)
- **Fallback:** falha ao obter JWKS → responder 503 nas rotas administrativas (página pública não é afetada)
- **Configuração:** frontend `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`; backend `CL_AUTH_MODE=supabase`, `CL_SUPABASE_URL`, opcional `CL_SUPABASE_JWT_SECRET`

### Deploy e Domínio

- **Domínio de produção:** `awscommunity.com.br`
- Cada comunidade é acessível por slug no path: `https://awscommunity.com.br/{slug}`.
- **CloudFront** serve o frontend Vue (SPA) e faz cache; **API Gateway + Lambda** expõem a API sob o mesmo domínio (ex.: `/api/*` roteado para a API).
- **Certificado TLS** via AWS Certificate Manager (ACM) para o domínio `awscommunity.com.br` (e `www`), emitido em `us-east-1` para uso com CloudFront.
- **DNS:** registros gerenciados no provedor do domínio (ex.: Route 53 ou zona externa) apontando para a distribuição CloudFront.

---

## 5. Modelo de Dados (DynamoDB)

Modelagem orientada a acesso (single-table design recomendado). Diagrama lógico das entidades:

```mermaid
erDiagram
    COMMUNITY ||--o{ SECTION : contem
    SECTION ||--o{ LINK : contem
    COMMUNITY ||--o{ ADMIN_LINK : possui
    ADMIN ||--o{ ADMIN_LINK : administra

    COMMUNITY {
        string PK "COMMUNITY#slug"
        string SK "METADATA"
        string name
        string slug
        string description
        string theme
        string logo_url
        string created_at
    }
    SECTION {
        string PK "COMMUNITY#slug"
        string SK "SECTION#id"
        string title
        number order
    }
    LINK {
        string PK "COMMUNITY#slug"
        string SK "LINK#sectionId#id"
        string type
        string title
        string url
        string emoji
        string image_url
        string author
        boolean embed
        string created_at
        number order
    }
    ADMIN {
        string PK "ADMIN#id"
        string SK "METADATA"
        string name
    }
    ADMIN_LINK {
        string PK "ADMIN#id"
        string SK "COMMUNITY#slug"
    }
```

### Administradores e convites (Fase 2 — RF-021)

O vínculo admin ↔ comunidade é gravado em **duas direções** para permitir as duas consultas principais (comunidades de um usuário; admins de uma comunidade) sem GSI:

| Item | PK | SK | Atributos |
|------|----|----|-----------|
| Admin da comunidade | `COMMUNITY#{slug}` | `ADMIN#{sub}` | `email`, `added_at` |
| Comunidade do admin (espelho) | `USER#{sub}` | `COMMUNITY#{slug}` | — |
| Convite pendente | `COMMUNITY#{slug}` | `INVITE#{email}` | `invited_by`, `invited_at` |

`sub` é o identificador do usuário emitido pelo Supabase Auth (claim `sub` do JWT). O convite é efetivado quando um usuário autenticado cujo `email` coincide com o convite acessa a comunidade: o convite é convertido em admin (dupla gravação) e removido.

### Campos críticos

- **`slug`**: chave de acesso público e isolamento multi-tenant (único).
- **`type`**: define tratamento visual/embed (`video`, `site`, `calendario`, `pessoa`, `linkedin`, `instagram`, `tiktok`, `builder_center`, `meetup`).
- **`order`**: ordena seções e links na renderização.
- **`created_at`**: base para filtros/pesquisa por data (Fase 2).

### Índices para Fase 2 (busca/filtros)

- **GSI1** — por tipo de conteúdo: `GSI1PK = TYPE#{type}`, `GSI1SK = {created_at}` (filtro por tipo + data).
- **GSI2** — por autor: `GSI2PK = AUTHOR#{author}`, `GSI2SK = {created_at}`.
- Busca textual mais rica pode, se necessário, apoiar-se em serviço de busca dedicado em iteração posterior.

---

## 6. Regras de Negócio

### RN-001: Unicidade de Slug
- **Condição:** Se um novo slug for informado no cadastro/edição de comunidade.
- **Ação:** Então validar que não existe outra comunidade com o mesmo slug antes de persistir.
- **Exceção:** Caso já exista, rejeitar com mensagem "slug já em uso".

### RN-002: Vínculo de Link a Seção
- **Condição:** Se um link for criado ou movido.
- **Ação:** Então associá-lo a exatamente uma seção existente da mesma comunidade.
- **Exceção:** Caso a seção não exista/não pertença à comunidade, rejeitar a operação.

### RN-003: Embed com Fallback
- **Condição:** Se o link for de um tipo embeddável.
- **Ação:** Então tentar renderizar embed via oEmbed/regra do provedor.
- **Exceção:** Caso o provedor não permita/embed falhe, exibir como link externo com o ícone do tipo.

### RN-004: Autorização de Escrita (MVP)
- **Condição:** Se a requisição alterar dados (criar/editar/excluir).
- **Ação:** Então exigir a credencial fixa configurada no backend.
- **Exceção:** Caso a credencial esteja ausente/incorreta, retornar 401.
- **Fase 2:** substituída pela RN-006.

### RN-005: Validação de Upload de Imagem
- **Condição:** Se houver upload de foto de destaque/logo.
- **Ação:** Então validar formato (JPEG/PNG/WebP) e tamanho (≤ 5 MB) e armazenar em S3.
- **Exceção:** Caso inválido, rejeitar com mensagem específica.

### RN-006: Autenticação e Autorização por Comunidade (Fase 2)
- **Condição:** Se a requisição for a uma rota administrativa.
- **Ação:** Então validar o JWT do Supabase (assinatura, `iss`, `aud`, `exp`) e identificar o usuário (`sub`, `email`); para operações sobre uma comunidade, verificar que o usuário é administrador dela (efetivando convite pendente por e-mail, se houver).
- **Exceção:** Token ausente/inválido → **401**; usuário autenticado sem vínculo com a comunidade → **403**.

### RN-007: Último Administrador
- **Condição:** Se um administrador tentar remover um administrador de uma comunidade.
- **Ação:** Então permitir apenas se restar ao menos um administrador após a remoção.
- **Exceção:** Caso seja o último, rejeitar com **409** (a comunidade não pode ficar sem administradores).

---

## 7. Fases de Implementação

| Fase | Escopo | Entregáveis | Dependências |
|------|--------|-------------|--------------|
| 1 | Cadastro de comunidade, seções, links ricos, emojis, embeds, foto de destaque, temas, edição fácil, página pública, auth simplificada, edição/reordenação | RF-001 a RF-011, RF-014 a RF-018; RNF-001 a RNF-006; INT-001 a INT-005 | Conta AWS; stack Vue + FastAPI + DynamoDB provisionada |
| 2a | **Autenticação e autorização** com Supabase Auth: login e-mail/senha e social, tela própria, admins por comunidade e convites | RF-019 a RF-022; INT-006; RN-006, RN-007 | Projeto Supabase criado; provedores sociais (Google, GitHub…) configurados no Supabase |
| 2b | Filtros e pesquisa | RF-012, RF-013; GSIs de busca | Fase 2a concluída; volume de dados para busca |
| Futura | Analytics, domínio custom, monetização | A especificar | Definição de produto |

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Credencial fixa exposta (MVP) | Alta | Alto | Restrita a dev/testes (`CL_AUTH_MODE=static`); produção usa Supabase Auth (Fase 2a) |
| Dependência de fornecedor externo (Supabase) fora da AWS | Média | Médio | Backend valida JWT localmente (JWKS em cache) — indisponibilidade do Supabase afeta apenas novos logins, não as páginas públicas; dados de autorização ficam no DynamoDB |
| Rotação de chaves JWT do Supabase | Baixa | Médio | Validação via JWKS com cache e refetch em `kid` desconhecido |
| Provedores bloqueiam embed (Instagram/TikTok/LinkedIn) | Média | Médio | Fallback para link externo; testar oEmbed por provedor |
| Modelagem DynamoDB inadequada para busca (Fase 2) | Média | Médio | Definir padrões de acesso cedo; usar GSIs; avaliar serviço de busca dedicado se necessário |
| Cold start de Lambda afeta latência | Média | Baixo | Otimizar pacote; considerar provisioned concurrency em endpoints críticos |
| Slugs conflitantes/abuso de nomes | Baixa | Médio | Validação de unicidade (RN-001) e lista de reservados |
| Custos crescerem com tráfego alto | Baixa | Médio | DynamoDB on-demand, cache no CloudFront, monitorar via CloudWatch |

---

> Rastreabilidade: cada feature do `ideas.MD` foi mapeada em requisitos — cadastro de comunidade/usuário (RF-001, RF-002, RF-011), seções (RF-003), tipos de link (RF-004), emojis (RF-005), embeds (RF-006), foto de destaque (RF-007), fácil de atualizar (RF-008), destaque visual/temas (RF-009), página pública (RF-010), filtros (RF-012) e pesquisas (RF-013). A identidade visual segue como referência o site awscommunityday.com.br (RF-014). A edição e reordenação de conteúdo cobrem comunidade (RF-015), seções (RF-016), links e movimentação entre seções (RF-017) e reordenação por ↑/↓ e arrastar-e-soltar (RF-018). A Fase 2a cobre autenticação com Supabase Auth (RF-019), tela de login própria (RF-020), autorização por comunidade com convites (RF-021) e compatibilidade de modos (RF-022).
