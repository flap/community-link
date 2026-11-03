# Módulo `dns-alias`

Publica os registros **ALIAS A e AAAA** no Route 53 apontando um domínio para
uma distribuição CloudFront existente. Separado do módulo `acm` para manter o
grafo linear (`acm` → `edge` → `dns-alias`) e evitar ciclo entre `edge` e DNS.

## Provider (cross-account — Opção A)

O módulo declara `configuration_aliases = [aws]`. Como a hosted zone vive na
conta de DNS, a composição o instancia com o provider aliasado `aws.dns`:

```hcl
module "dns_alias" {
  source    = "../../modules/dns-alias"
  providers = { aws = aws.dns }
  # ...
}
```

## Inputs

| Nome | Descrição |
|------|-----------|
| `domain_name` | FQDN a publicar. |
| `hosted_zone_id` | ID da hosted zone pública. |
| `distribution_domain_name` | Domínio do CloudFront (`dxxxx.cloudfront.net`). |
| `distribution_hosted_zone_id` | Hosted zone ID do CloudFront (`Z2FDTNDATAQYW2`). |

## Outputs

| Nome | Descrição |
|------|-----------|
| `fqdn` | FQDN publicado. |
