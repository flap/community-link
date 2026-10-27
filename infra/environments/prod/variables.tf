variable "aws_region" {
  description = "Região AWS da implantação."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefixo de nomenclatura para os recursos deste ambiente."
  type        = string
  default     = "community-link-prod"
}

variable "dynamodb_table_name" {
  description = "Nome da tabela DynamoDB single-table."
  type        = string
  default     = "community-link"
}

variable "spa_bucket_name" {
  description = "Nome globalmente único do bucket S3 da SPA."
  type        = string
}

variable "media_bucket_name" {
  description = "Nome globalmente único do bucket S3 de mídia."
  type        = string
}

variable "config_ssm_path" {
  description = "Prefixo SSM lido pela Lambda no cold start."
  type        = string
  default     = "/community-link/prod/backend"
}

variable "lambda_package_path" {
  description = "Caminho do artefato .zip do backend (construído em CI antes do apply)."
  type        = string
}

variable "domain_name" {
  description = "Domínio customizado (FQDN) do projeto. Vazio desativa ACM/Route 53 e mantém apenas o domínio *.cloudfront.net."
  type        = string
  default     = ""
}

variable "hosted_zone_name" {
  description = "Nome da hosted zone pública no Route 53 que contém o domínio (ex.: awscommunity.com.br). Obrigatório quando domain_name é definido."
  type        = string
  default     = ""
}

# ARQUITETURA (Opção A): o app roda nesta conta (390686807269), mas a hosted
# zone Route 53 do domínio vive na conta de DNS (070008302080). O provider
# aliasado `aws.dns` assume esta role para criar os registros de validação do
# ACM e o ALIAS do subdomínio na conta de DNS. Vazio => usa a conta default
# (útil quando a zona está na mesma conta, p.ex. em testes).
variable "dns_account_role_arn" {
  description = "ARN da IAM role a assumir na conta que hospeda a hosted zone Route 53 (conta de DNS). Ex.: arn:aws:iam::070008302080:role/community-link-dns-manager."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags comuns a todos os recursos."
  type        = map(string)
  default = {
    Project     = "community-link"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
