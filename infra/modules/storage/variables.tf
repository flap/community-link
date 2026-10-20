variable "bucket_name" {
  description = "Nome globalmente único do bucket S3 privado."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name deve seguir as regras de nomenclatura de bucket S3 (minúsculas, 3-63 chars)."
  }
}

variable "versioning_enabled" {
  description = "Habilita versionamento de objetos no bucket."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos do módulo."
  type        = map(string)
  default     = {}
}
