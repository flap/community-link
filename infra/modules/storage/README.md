# Módulo `storage` — Bucket S3 privado (OAC)

Cria um bucket S3 **privado**, acessível apenas via CloudFront com Origin Access
Control (OAC). Reutilizável para o bucket da SPA (`frontend/dist`) e para o
bucket de mídia (uploads em `links/*`, ver `backend/app/storage.py`).

## Descrição

- Public access block total (bucket nunca público).
- `BucketOwnerEnforced` (ACLs desabilitadas).
- Criptografia em repouso (SSE-S3 / AES256) com bucket key.
- Versionamento opcional.
- **A policy de leitura OAC é aplicada na composição** (`environments/*`), não
  aqui — isso evita um ciclo de dependência com o módulo `edge` (o edge precisa
  do domínio do bucket; a policy do bucket precisa do ARN da distribuição).

## Uso

```hcl
module "spa_bucket" {
  source = "../../modules/storage"

  bucket_name = "community-link-spa-prod"
  tags        = { Environment = "prod" }
}

# Policy OAC aplicada na composição, após a distribuição existir:
resource "aws_s3_bucket_policy" "spa_oac" {
  bucket = module.spa_bucket.bucket_id
  policy = data.aws_iam_policy_document.spa_oac.json # condiciona em module.edge.distribution_arn
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0, < 2.0.0 |
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `bucket_name` | Nome globalmente único do bucket. | `string` | n/a |
| `versioning_enabled` | Habilita versionamento. | `bool` | `false` |
| `tags` | Tags aplicadas aos recursos. | `map(string)` | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| `bucket_id` | Nome do bucket. |
| `bucket_arn` | ARN do bucket. |
| `bucket_regional_domain_name` | Domínio regional (origem CloudFront). |
