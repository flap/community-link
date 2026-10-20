# Ambiente `prod` — Community Link (pastel)

Composição Terraform que monta o deploy completo de produção na AWS
(`us-east-1`): DynamoDB + S3 (SPA/media) + Lambda/HTTP API + CloudFront.

## Arquitetura

```
CloudFront (1 distribuição, OAC, 2 Functions)
├── default  → S3 SPA        (frontend/dist)
├── /media/* → S3 media      (links/*)        [strip /media]
└── /api/*   → API Gateway HTTP API → Lambda (FastAPI/Mangum, python3.12)
                                        ├── DynamoDB `community-link`
                                        ├── S3 media (put_object links/*)
                                        └── SSM /community-link/beta/backend/* (cold start)
```

## State remoto

Backend S3 com `encrypt = true` e **locking via DynamoDB** (`dynamodb_table`).
O runtime local é **Terraform 1.5.7 (< 1.10)**, portanto `use_lockfile` (locking
nativo por arquivo) não está disponível — ver `backend.tf`. Ao migrar para
Terraform ≥ 1.10, troque para `use_lockfile = true`.

> Os recursos de bootstrap do backend (bucket de state, tabela de lock, KMS) NÃO
> fazem parte desta composição — devem ser criados uma única vez à parte
> (ver [State Management](../../../README.md) ou o padrão da skill).

## Uso (sem deploy real — esqueleto de demonstração)

```bash
# Validação local (sem backend e sem credenciais):
terraform init -backend=false
terraform fmt -recursive
terraform validate

# Fluxo real (NÃO executado nesta demonstração):
#   terraform init                       # com backend S3 real
#   terraform plan  -out=prod.tfplan     # artefato revisável
#   terraform apply prod.tfplan          # aplica o plan aprovado
```

## Segredos

Supabase (`VITE_SUPABASE_*`, chaves JWT) e demais segredos **não** entram em
`variables`/`tfvars`/state. Ficam no SSM Parameter Store (SecureString) sob
`/community-link/beta/*` e/ou no Secrets Manager; a Lambda os lê em runtime.

## Inputs principais

Ver `variables.tf`. Ajuste `spa_bucket_name` e `media_bucket_name` (globais únicos)
e `lambda_package_path` (artefato construído em CI).
