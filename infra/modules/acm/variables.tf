variable "domain_name" {
  description = "Domínio (FQDN) para o certificado, ex.: link.awscommunity.com.br."
  type        = string
}

variable "hosted_zone_id" {
  description = "ID da hosted zone pública no Route 53 onde criar o registro de validação DNS."
  type        = string
}

variable "tags" {
  description = "Tags aplicadas ao certificado ACM."
  type        = map(string)
  default     = {}
}
