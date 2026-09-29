# Community Link

Portal agregador de links para comunidades — **SaaS multi-tenant** com foco em visual bonito e fácil manutenção. Cada comunidade tem uma página pública em `awscommunity.com.br/{slug}`, organizada em seções, com tipos de link ricos (vídeo, site, calendário, pessoas, LinkedIn, Instagram, TikTok, AWS Builder Center, Meetup), emojis, embeds e fotos de destaque.

> Estado atual: **Fase 1 (MVP)**. A autenticação administrativa usa uma **credencial fixa** no backend (temporária, para testes).

## Arquitetura

- **Frontend:** Vue 3 + Vite (SPA)
- **Backend:** Python + FastAPI
- **Persistência:** Amazon DynamoDB (single-table) — repositório em memória para dev/testes
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
- Área administrativa: `/admin` (informe o token = `CL_ADMIN_TOKEN`)
- Página pública: `/{slug}`

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
| GET/POST | `/api/admin/communities` | Lista/cria comunidades | Sim |
| GET/PATCH/DELETE | `/api/admin/communities/{slug}` | Detalhe/edita/exclui comunidade | Sim |
| GET/POST | `/api/admin/communities/{slug}/sections` | Seções | Sim |
| PATCH/DELETE | `/api/admin/communities/{slug}/sections/{id}` | Edita/exclui seção | Sim |
| GET/POST | `/api/admin/communities/{slug}/links` | Links | Sim |
| PATCH/DELETE | `/api/admin/communities/{slug}/links/{id}` | Edita/exclui link | Sim |

Autenticação (MVP): header `Authorization: Bearer <CL_ADMIN_TOKEN>`.

## Documentação

- [Descritivo de Negócio](./docs/01-descritivo-negocio.md)
- [Fluxogramas de Processos](./docs/02-fluxograma-processos/README.md)
- [Especificação Técnica](./docs/03-especificacao-tecnica.md)
- [Resumo Executivo](./docs/04-resumo-executivo.md)
- [Estimativa de Custos AWS](https://calculator.aws/#/estimate?id=e89980819e4b691ff9037523670c7641b6e72d7c)

## Roadmap

- **Fase 1 (MVP):** comunidades, seções, links ricos, emojis, embeds, foto de destaque, temas, edição fácil, página pública.
- **Fase 2:** filtros (data, tipo) e pesquisa (data, conteúdo, autores, comunidades).
- **Futuro:** autenticação completa, analytics, domínio customizado, monetização.
