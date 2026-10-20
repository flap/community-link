# Módulo `edge` — CloudFront (3 origens, OAC, 2 Functions)

Cria uma única distribuição CloudFront que serve o projeto inteiro:

| Comportamento | Origem | Observação |
|---------------|--------|------------|
| `default`     | S3 SPA (OAC)   | CloudFront Function `spa_fallback` → `/index.html` |
| `/media/*`    | S3 media (OAC) | CloudFront Function `media_strip` remove o prefixo `/media` |
| `/api/*`      | API Gateway HTTP API | Sem cache (`CachingDisabled`) |

## Descrição

- **OAC** (`aws_cloudfront_origin_access_control`) para as duas origens S3 — os
  buckets permanecem privados; o módulo `storage` consome o `distribution_arn`
  para liberar a leitura.
- **2 CloudFront Functions** (viewer-request): SPA fallback e strip do `/media`.
- Managed cache/origin-request policies referenciadas por ID well-known:
  - `CachingOptimized` (SPA/media), `CachingDisabled` + `AllViewerExceptHostHeader` (API).
- Certificado CloudFront padrão (trocar por ACM ao usar domínio custom).

## Uso

```hcl
module "edge" {
  source = "../../modules/edge"

  name_prefix                       = "community-link-prod"
  spa_bucket_regional_domain_name   = module.spa_bucket.bucket_regional_domain_name
  media_bucket_regional_domain_name = module.media_bucket.bucket_regional_domain_name
  api_origin_domain_name            = replace(module.compute.http_api_endpoint, "https://", "")
  tags                              = { Environment = "prod" }
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
| `name_prefix` | Prefixo de nomenclatura. | `string` | n/a |
| `spa_bucket_regional_domain_name` | Domínio da origem SPA. | `string` | n/a |
| `media_bucket_regional_domain_name` | Domínio da origem media. | `string` | n/a |
| `api_origin_domain_name` | Domínio do HTTP API (sem esquema/path). | `string` | n/a |
| `media_path_prefix` | Prefixo público da mídia. | `string` | `/media` |
| `price_class` | Price class da distribuição. | `string` | `PriceClass_100` |
| `tags` | Tags. | `map(string)` | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| `distribution_id` | ID da distribuição. |
| `distribution_arn` | ARN (para policies OAC dos buckets). |
| `distribution_domain_name` | Domínio público. |
