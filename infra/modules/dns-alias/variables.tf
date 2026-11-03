variable "domain_name" {
  description = "FQDN a publicar, ex.: link.awscommunity.com.br."
  type        = string
}

variable "hosted_zone_id" {
  description = "ID da hosted zone pública no Route 53."
  type        = string
}

variable "distribution_domain_name" {
  description = "Domínio da distribuição CloudFront alvo (ex.: dxxxx.cloudfront.net)."
  type        = string
}

variable "distribution_hosted_zone_id" {
  description = "Hosted zone ID do CloudFront (constante Z2FDTNDATAQYW2)."
  type        = string
}
