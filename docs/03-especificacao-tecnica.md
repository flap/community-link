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
- **Descrição:** permitir enviar uma imagem de destaque para um link.
- **Regra de negócio:** imagens são armazenadas em S3; formatos JPEG/PNG/WebP; tamanho máximo definido (ex.: 5 MB).
- **Critério de aceite:** a imagem enviada é exibida como destaque do link na página pública; arquivo inválido é rejeitado com mensagem.
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
- **Observação:** solução temporária, a ser substituída por autenticação real.

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

### RN-005: Validação de Upload de Imagem
- **Condição:** Se houver upload de foto de destaque/logo.
- **Ação:** Então validar formato (JPEG/PNG/WebP) e tamanho (≤ 5 MB) e armazenar em S3.
- **Exceção:** Caso inválido, rejeitar com mensagem específica.

---

## 7. Fases de Implementação

| Fase | Escopo | Entregáveis | Dependências |
|------|--------|-------------|--------------|
| 1 | Cadastro de comunidade, seções, links ricos, emojis, embeds, foto de destaque, temas, edição fácil, página pública, auth simplificada | RF-001 a RF-011; RNF-001 a RNF-006; INT-001 a INT-005 | Conta AWS; stack Vue + FastAPI + DynamoDB provisionada |
| 2 | Filtros e pesquisa | RF-012, RF-013; GSIs de busca | Fase 1 concluída; volume de dados para busca |
| Futura | Autenticação completa, analytics, domínio custom, monetização | A especificar | Definição de produto |

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Credencial fixa exposta (MVP) | Alta | Alto | Restringir ao ambiente de teste; priorizar autenticação real antes de produção aberta |
| Provedores bloqueiam embed (Instagram/TikTok/LinkedIn) | Média | Médio | Fallback para link externo; testar oEmbed por provedor |
| Modelagem DynamoDB inadequada para busca (Fase 2) | Média | Médio | Definir padrões de acesso cedo; usar GSIs; avaliar serviço de busca dedicado se necessário |
| Cold start de Lambda afeta latência | Média | Baixo | Otimizar pacote; considerar provisioned concurrency em endpoints críticos |
| Slugs conflitantes/abuso de nomes | Baixa | Médio | Validação de unicidade (RN-001) e lista de reservados |
| Custos crescerem com tráfego alto | Baixa | Médio | DynamoDB on-demand, cache no CloudFront, monitorar via CloudWatch |

---

> Rastreabilidade: cada feature do `ideas.MD` foi mapeada em requisitos — cadastro de comunidade/usuário (RF-001, RF-002, RF-011), seções (RF-003), tipos de link (RF-004), emojis (RF-005), embeds (RF-006), foto de destaque (RF-007), fácil de atualizar (RF-008), destaque visual/temas (RF-009), página pública (RF-010), filtros (RF-012) e pesquisas (RF-013).
