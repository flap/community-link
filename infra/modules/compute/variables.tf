variable "function_name" {
  description = "Nome da função Lambda (FastAPI via Mangum)."
  type        = string
}

variable "lambda_package_path" {
  description = <<-EOT
    Caminho local do artefato .zip do backend (handler app.lambda_handler.handler).
    Em CI o pacote é construído antes do apply. No esqueleto um placeholder é aceito;
    não há deploy real nesta demonstração.
  EOT
  type        = string
}

variable "runtime" {
  description = "Runtime da Lambda."
  type        = string
  default     = "python3.12"

  validation {
    condition     = can(regex("^python3\\.(1[0-9]|9)$", var.runtime))
    error_message = "runtime deve ser uma versão python3.x suportada."
  }
}

variable "handler" {
  description = "Entrypoint da Lambda (módulo.objeto)."
  type        = string
  default     = "app.lambda_handler.handler"
}

variable "memory_size" {
  description = "Memória da Lambda em MB."
  type        = number
  default     = 512
}

variable "timeout" {
  description = "Timeout da Lambda em segundos."
  type        = number
  default     = 30
}

variable "config_ssm_path" {
  description = "Prefixo SSM lido no cold start (ex.: /community-link/beta/backend)."
  type        = string
}

variable "ssm_parameter_arns" {
  description = "ARNs dos parâmetros SSM que a Lambda pode ler (least-privilege)."
  type        = list(string)
}

variable "dynamodb_table_arn" {
  description = "ARN da tabela DynamoDB para a policy de acesso da Lambda."
  type        = string
}

variable "media_bucket_arn" {
  description = "ARN do bucket S3 de mídia (put_object em links/*)."
  type        = string
}

variable "media_bucket_name" {
  description = "Nome do bucket S3 de mídia (env var MEDIA_BUCKET da Lambda)."
  type        = string
}

variable "aws_region" {
  description = "Região AWS dos recursos."
  type        = string
  default     = "us-east-1"
}

variable "kms_key_arn" {
  description = <<-EOT
    ARN da chave KMS usada para decriptar SecureString no SSM, se aplicável.
    Vazio = chave gerenciada pela AWS (alias/aws/ssm), que não exige permissão kms explícita.
  EOT
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "Retenção dos logs do CloudWatch Log Group da Lambda."
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos do módulo."
  type        = map(string)
  default     = {}
}
