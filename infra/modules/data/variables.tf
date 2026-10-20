variable "table_name" {
  description = "Nome da tabela DynamoDB single-table (ex.: community-link)."
  type        = string

  validation {
    condition     = length(var.table_name) > 0 && length(var.table_name) <= 255
    error_message = "table_name deve ter entre 1 e 255 caracteres."
  }
}

variable "point_in_time_recovery_enabled" {
  description = "Habilita Point-in-Time Recovery (recomendado em produção)."
  type        = bool
  default     = true
}

variable "deletion_protection_enabled" {
  description = "Protege a tabela contra exclusão acidental via API."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos do módulo."
  type        = map(string)
  default     = {}
}
