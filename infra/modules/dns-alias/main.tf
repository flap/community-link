# Registros ALIAS (A + AAAA) do Route 53 apontando um domínio para o CloudFront.
# Consome a distribuição já criada (module.edge), fechando a cadeia:
#   acm (cert) -> edge (distribuição) -> dns-alias (estes registros).

resource "aws_route53_record" "alias_a" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.distribution_domain_name
    zone_id                = var.distribution_hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "alias_aaaa" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = var.distribution_domain_name
    zone_id                = var.distribution_hosted_zone_id
    evaluate_target_health = false
  }
}
