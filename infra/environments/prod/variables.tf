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
  default     = "/community-link/beta/backend"
}

variable "lambda_package_path" {
  description = "Caminho do artefato .zip do backend (construído em CI antes do apply)."
  type        = string
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
