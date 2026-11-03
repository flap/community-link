# Certificado ACM com validação DNS via Route 53 (cross-account — Opção A).
#
# IMPORTANTE:
#   - O certificado (aws_acm_certificate + aws_acm_certificate_validation) vive na
#     CONTA DO APP, em us-east-1 (provider default `aws`), porque o CloudFront exige
#     o cert na mesma conta da distribuição, em us-east-1. O ambiente prod já roda lá.
#   - Os registros CNAME de validação DNS vão para a CONTA DE DNS (provider `aws.dns`),
#     pois a hosted zone awscommunity.com.br está naquela conta.
#
# Este módulo NÃO depende do CloudFront, o que mantém a ordem do grafo:
#   acm (cert) -> edge (distribuição) -> dns-alias (registros ALIAS).

resource "aws_acm_certificate" "this" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "validation" {
  # Registros de validação na conta de DNS (hosted zone awscommunity.com.br lá).
  provider = aws.dns

  for_each = {
    for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id         = var.hosted_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 300
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "this" {
  certificate_arn         = aws_acm_certificate.this.arn
  validation_record_fqdns = [for r in aws_route53_record.validation : r.fqdn]
}
