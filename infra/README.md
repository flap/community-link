# Infra — Community Link (pastel) · Terraform

Infraestrutura como código do projeto, equivalente em **Terraform** ao deploy
serverless (o antigo SAM foi removido). Gerada pelo agente **agent-tofu** seguindo
a skill [`antonbabenko/terraform-skill`](https://github.com/antonbabenko/terraform-skill).

> **Esqueleto de demonstração.** Validado localmente com `fmt`/`validate`. NÃO
> executar `plan`/`apply` contra a AWS sem revisar e preencher os valores reais.

## Layout

```
infra/
├── environments/        # composições por ambiente (valores concretos)
│   ├── prod/
│   └── staging/
├── modules/             # módulos reutilizáveis (genéricos, parametrizados)
│   ├── data/            # DynamoDB single-table (PK/SK, PAY_PER_REQUEST, sem GSI)
│   ├── storage/         # bucket S3 privado (OAC) — usado p/ SPA e mídia
│   ├── compute/         # Lambda (FastAPI/Mangum) + API Gateway HTTP API + IAM
│   └── edge/            # CloudFront (3 origens, OAC, 2 CloudFront Functions)
└── examples/            # fixtures + documentação
    ├── minimal/         # só o módulo data
    └── complete/        # todos os módulos integrados
```

Hierarquia da skill: **resource module → infrastructure module → composition**.
`data`/`storage`/`edge` são resource modules; `compute` combina Lambda+API+IAM
(infrastructure); `environments/*` são as composições.

## Arquitetura de deploy

Ver o diagrama em [`../generated-diagrams/deploy-architecture.png`](../generated-diagrams/deploy-architecture.png).

```
Cliente → CloudFront (OAC, 2 Functions)
            ├── default  → S3 SPA
            ├── /media/* → S3 media (strip /media)
            └── /api/*   → HTTP API → Lambda (python3.12)
                                        ├── DynamoDB community-link
                                        ├── S3 media (links/*)
                                        └── SSM /community-link/beta/backend/*
Auth: Supabase (externo) — segredos no SSM/Secrets Manager.
```

## State remoto

Backend **S3** com `encrypt = true`. **Version floor:** o Terraform local é
**1.5.7 (< 1.10)**, então o locking nativo por arquivo (`use_lockfile`) não está
disponível — usamos **`dynamodb_table`**. Ao migrar para ≥ 1.10, troque para
`use_lockfile = true` (ver `environments/*/backend.tf`).

O bucket de state, a tabela de lock e a KMS são **bootstrap** (criados uma vez,
fora destas composições).

## Segredos

Nenhum segredo em `variables`/`tfvars`/state. Supabase (`VITE_SUPABASE_*`, chaves
JWT) e similares ficam no **SSM Parameter Store** (SecureString) sob
`/community-link/beta/*` e/ou no **Secrets Manager**; a Lambda os lê em runtime.

## Validação local

```bash
# Em cada environment/example:
terraform init -backend=false
terraform fmt -recursive
terraform validate
```

Ferramentas recomendadas pela skill (não instaladas neste ambiente):
`tflint`, `trivy config .`, `checkov -d .`, e `terraform test` (requer 1.6+).

## Requisitos

| Nome | Versão |
|------|--------|
| terraform | >= 1.5.0, < 2.0.0 (local: 1.5.7) |
| aws (provider) | ~> 5.0 |
