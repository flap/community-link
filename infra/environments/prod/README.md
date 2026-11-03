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
                                        └── SSM /community-link/prod/backend/* (cold start)
```

## Domínio customizado (`link.awscommunity.com.br`) — cross-account (Opção A)

O link padrão é servido por domínio customizado no CloudFront, todo via IaC.
**Opção A:** o app inteiro roda nesta conta (app, `390686807269`); a hosted zone
`awscommunity.com.br` vive em **outra conta** (DNS, `070008302080`). Os registros
Route 53 (validação do ACM e ALIAS do subdomínio) são criados na conta de DNS via
o provider aliasado `aws.dns`, que assume `var.dns_account_role_arn`.

A cadeia é montada por três módulos, nesta ordem (resolvida pelo grafo — sem ciclo):

```
module.acm        → cert ACM (us-east-1) na CONTA DO APP (provider aws)
                    + CNAME de validação na CONTA DE DNS (provider aws.dns)
module.edge       → CloudFront com aliases + viewer_certificate (ACM, SNI)  [conta do app]
module.dns_alias  → ALIAS A/AAAA: link.awscommunity.com.br → CloudFront      [conta de DNS]
```

Controlado em `terraform.tfvars`:

```hcl
domain_name          = "link.awscommunity.com.br"  # "" desativa e usa *.cloudfront.net
hosted_zone_name     = "awscommunity.com.br"        # hosted zone na conta de DNS
dns_account_role_arn = "arn:aws:iam::070008302080:role/community-link-dns-manager"
```

### Pré-requisito: role cross-account na conta de DNS

Antes de qualquer `plan`/`apply` do prod, a role `community-link-dns-manager`
precisa existir na conta `070008302080` e confiar na identidade que roda o
Terraform na conta do app. Crie-a com a composição
[`../dns-account`](../dns-account/README.md) (aplicada com credenciais da conta
de DNS). Sem ela, o provider `aws.dns` falha em `sts:AssumeRole` e o plan não
completa.

### Colisão de alias (CNAMEAlreadyExists)

Um alias de CloudFront (`link.awscommunity.com.br`) só pode estar ativo em **uma**
distribuição por vez. Hoje o domínio aponta para a distribuição do deploy antigo
na conta de DNS (`070008302080`). **Antes** do apply que cria a nova distribuição
nesta conta com esse alias, o alias deve ser removido da distribuição antiga
(desassociar o CNAME ou `plan -destroy` daquela stack, com aprovação). Caso
contrário o apply falha com `CNAMEAlreadyExists`.

- O certificado **precisa** estar em `us-east-1` — este ambiente já roda lá.
- Outputs: `custom_domain_url`, `acm_certificate_arn`, `cloudfront_domain_name`.

> Pré-requisito da aplicação: `https://link.awscommunity.com.br` como **Site URL**
> e `https://link.awscommunity.com.br/admin` nas **Redirect URLs** do Supabase,
> e no CORS do backend (`CL_CORS_ORIGINS`, já no SSM de prod).

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
`/community-link/prod/*` e/ou no Secrets Manager; a Lambda os lê em runtime.

## Inputs principais

Ver `variables.tf`. Ajuste `spa_bucket_name` e `media_bucket_name` (globais únicos)
e `lambda_package_path` (artefato construído em CI).
