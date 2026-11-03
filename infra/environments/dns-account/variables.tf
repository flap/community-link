variable "aws_region" {
  description = "Região AWS para o endpoint de IAM/Route 53 (IAM é global; us-east-1 é um bom default)."
  type        = string
  default     = "us-east-1"
}

variable "role_name" {
  description = "Nome da IAM role cross-account que a conta do app assume para gerir DNS."
  type        = string
  default     = "community-link-dns-manager"
}

variable "hosted_zone_name" {
  description = "Nome da hosted zone pública gerida (ex.: awscommunity.com.br). Usado para restringir a policy à zona específica."
  type        = string
  default     = "awscommunity.com.br"
}

variable "trusted_principal_arns" {
  description = "ARNs das identidades (contas/roles) autorizadas a assumir a role. Default: a conta do app inteira (delega a autorização fina às policies de IAM daquela conta)."
  type        = list(string)
  default     = ["arn:aws:iam::390686807269:root"]

  validation {
    condition     = length(var.trusted_principal_arns) > 0
    error_message = "Informe ao menos um principal confiável para a trust policy."
  }
}

variable "tags" {
  description = "Tags comuns aos recursos."
  type        = map(string)
  default = {
    Project     = "community-link"
    Environment = "dns-account"
    ManagedBy   = "Terraform"
  }
}
