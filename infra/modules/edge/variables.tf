variable "name_prefix" {
  description = "Prefixo de nomenclatura dos recursos de borda (ex.: community-link-prod)."
  type        = string
}

variable "spa_bucket_regional_domain_name" {
  description = "Domínio regional do bucket S3 da SPA (origem default)."
  type        = string
}

variable "media_bucket_regional_domain_name" {
  description = "Domínio regional do bucket S3 de mídia (origem /media/*)."
  type        = string
}

variable "api_origin_domain_name" {
  description = "Domínio do API Gateway HTTP API (origem /api/*), sem esquema nem path."
  type        = string
}

variable "media_path_prefix" {
  description = "Prefixo de caminho público para a mídia (ver CL_MEDIA_BASE_URL)."
  type        = string
  default     = "/media"
}

variable "price_class" {
  description = "Price class da distribuição CloudFront."
  type        = string
  default     = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class deve ser PriceClass_100, PriceClass_200 ou PriceClass_All."
  }
}

variable "tags" {
  description = "Tags aplicadas aos recursos."
  type        = map(string)
  default     = {}
}
