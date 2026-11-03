# Módulo `acm`

Emite um certificado **ACM** com validação **DNS** e cria o registro de validação
na hosted zone do **Route 53**, aguardando a emissão (`ISSUED`) via
`aws_acm_certificate_validation`.

> **Região:** para uso no CloudFront, instancie este módulo com um provider `aws`
> em `us-east-1`. O ambiente `prod` já é `us-east-1`.

## Providers (cross-account — Opção A)

O módulo declara `configuration_aliases = [aws, aws.dns]`:

| Provider | Conta | Recursos |
|----------|-------|----------|
| `aws` (default) | app | `aws_acm_certificate`, `aws_acm_certificate_validation` (cert em us-east-1 para o CloudFront). |
| `aws.dns` | DNS | `aws_route53_record.validation` (CNAME de validação na hosted zone). |

Instancie passando ambos:

```hcl
module "acm" {
  source    = "../../modules/acm"
  providers = { aws = aws, aws.dns = aws.dns }
  # ...
}
```

Quando a zona está na mesma conta, aponte `aws.dns` para o provider default.

Não depende do CloudFront — assim o grafo fica linear:
`acm` → `edge` (consome `certificate_arn`) → `dns-alias`.

## Inputs

| Nome | Descrição |
|------|-----------|
| `domain_name` | FQDN do certificado (ex.: `link.awscommunity.com.br`). |
| `hosted_zone_id` | ID da hosted zone pública do Route 53. |
| `tags` | Tags do certificado. |

## Outputs

| Nome | Descrição |
|------|-----------|
| `certificate_arn` | ARN do certificado **validado**. |
