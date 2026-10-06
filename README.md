# Community Link

Portal agregador de links para comunidades — **SaaS multi-tenant** com foco em visual bonito e fácil manutenção. Cada comunidade tem uma página pública em `awscommunity.com.br/{slug}`, organizada em seções, com tipos de link ricos (vídeo, site, calendário, pessoas, LinkedIn, Instagram, TikTok, AWS Builder Center, Meetup), emojis, embeds e fotos de destaque.

> Estado atual: **Fase 1 (MVP) concluída; Fase 2a (autenticação) implementada.** Em produção a autenticação dos administradores usa **Supabase Auth** (e-mail+senha e login social) com tela própria; em desenvolvimento há um modo `static` com credencial fixa.

## Arquitetura

- **Frontend:** Vue 3 + Vite (SPA)
- **Backend:** Python + FastAPI
- **Persistência:** Amazon DynamoDB (single-table) — repositório em memória para dev/testes
- **Autenticação (Fase 2a):** Supabase Auth — e-mail+senha e provedores sociais (Google, GitHub…), fluxo PKCE, JWT validado no backend via JWKS; autorização por comunidade no DynamoDB (admins e convites por e-mail)
- **Deploy (alvo):** CloudFront + API Gateway + AWS Lambda, domínio `awscommunity.com.br`
- **Identidade visual:** referência em [awscommunityday.com.br](https://awscommunityday.com.br) (paleta azul-marinho + laranja AWS, tipografia Inter) — materializada no tema `aws` (padrão)

```
pastel/
├── backend/          # API FastAPI
│   ├── app/          # config, models, repository, routers, auth, embeds, themes
│   ├── scripts/      # seed de dados
│   └── tests/        # testes da API
├── frontend/         # Vue 3 + Vite
│   └── src/          # views (Home, Admin, Community), api client, estilos
└── docs/             # documentação do projeto (negócio, fluxos, spec, resumo)
```

## Como rodar (desenvolvimento)

Atalhos (na raiz do projeto), um em cada aba do terminal:

```bash
./run-backend.sh    # sobe a API em http://localhost:8080 (repositório em memória)
./run-frontend.sh   # sobe o frontend em http://localhost:5173
```

Ou manualmente:

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # ajuste CL_ADMIN_TOKEN se desejar
uvicorn app.main:app --reload --port 8080
```

- API: <http://localhost:8080/api/health>
- Docs (Swagger): <http://localhost:8080/docs>
- Repositório em memória por padrão (`CL_USE_IN_MEMORY_STORE=true`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: <http://localhost:5173> (proxy de `/api` para `http://localhost:8080`)
- Login: `/login` — sem Supabase configurado, informe a credencial fixa (`CL_ADMIN_TOKEN`)
- Área administrativa: `/admin` (redireciona para `/login` se não autenticado)
- Página pública: `/{slug}`

### Autenticação com Supabase (produção ou teste real)

1. Crie um projeto em <https://supabase.com> e habilite os provedores desejados em *Authentication → Providers* (e-mail/senha, Google, GitHub…). Em *URL Configuration*, adicione `http://localhost:5173/admin` e `https://awscommunity.com.br/admin` como *Redirect URLs*.
2. Frontend: copie `frontend/.env.example` para `frontend/.env` e preencha `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` e `VITE_SUPABASE_PROVIDERS`.
3. Backend: defina `CL_AUTH_MODE=supabase` e `CL_SUPABASE_URL` (mesma URL do projeto). O JWT é validado via JWKS; para projetos legados com segredo HS256, defina também `CL_SUPABASE_JWT_SECRET`.
4. Quem cria uma comunidade vira seu administrador; outros admins são convidados por e-mail na própria área administrativa e efetivados no primeiro login.

### Testes do backend

```bash
cd backend && source .venv/bin/activate
CL_USE_IN_MEMORY_STORE=true CL_ADMIN_TOKEN=test-token python -m pytest -q
```

## API (resumo)

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| GET | `/api/health` | Health check | Não |
| GET | `/api/themes` | Lista temas visuais | Não |
| GET | `/api/communities/{slug}` | Página pública (seções + links + embeds) | Não |
| GET | `/api/admin/me` | Identidade do usuário autenticado e modo de auth | Sim |
| GET/POST | `/api/admin/communities` | Lista (apenas as do usuário) / cria comunidades (criador vira admin) | Sim |
| GET/PATCH/DELETE | `/api/admin/communities/{slug}` | Detalhe/edita/exclui comunidade | Admin da comunidade |
| GET/POST | `/api/admin/communities/{slug}/admins` | Lista admins e convites / convida admin por e-mail | Admin da comunidade |
| DELETE | `/api/admin/communities/{slug}/admins/{sub}` | Remove admin (não o último) | Admin da comunidade |
| DELETE | `/api/admin/communities/{slug}/invites/{email}` | Cancela convite pendente | Admin da comunidade |
| GET/POST | `/api/admin/communities/{slug}/sections` | Seções | Sim |
| PATCH/DELETE | `/api/admin/communities/{slug}/sections/{id}` | Edita/exclui seção | Sim |
| GET/POST | `/api/admin/communities/{slug}/links` | Links | Sim |
| PATCH/DELETE | `/api/admin/communities/{slug}/links/{id}` | Edita/exclui link | Sim |
| POST | `/api/admin/uploads` | Upload de foto de destaque (JPEG/PNG/WebP ≤5MB) → `image_url` | Sim |
| GET | `/api/media/{nome}` | Serve imagem enviada (apenas dev; em prod via S3/CloudFront) | Não |

Autenticação: header `Authorization: Bearer <token>` — access token do Supabase (`CL_AUTH_MODE=supabase`) ou `CL_ADMIN_TOKEN` (`CL_AUTH_MODE=static`, dev).

## Documentação

- [Descritivo de Negócio](./docs/01-descritivo-negocio.md)
- [Fluxogramas de Processos](./docs/02-fluxograma-processos/README.md)
- [Especificação Técnica](./docs/03-especificacao-tecnica.md)
- [Resumo Executivo](./docs/04-resumo-executivo.md)
- [Estimativa de Custos AWS](https://calculator.aws/#/estimate?id=e89980819e4b691ff9037523670c7641b6e72d7c)

## Roadmap

- **Fase 1 (MVP):** comunidades, seções, links ricos, emojis, embeds, foto de destaque, temas, edição fácil, página pública.
- **Fase 2a (feita):** autenticação com Supabase Auth, tela de login própria, admins por comunidade e convites.
- **Fase 2b:** filtros (data, tipo) e pesquisa (data, conteúdo, autores, comunidades).
- **Futuro:** analytics, domínio customizado, monetização.
