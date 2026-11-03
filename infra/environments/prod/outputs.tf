output "cloudfront_domain_name" {
  description = "Domínio público do CloudFront (ponto de entrada do projeto)."
  value       = module.edge.distribution_domain_name
}

output "custom_domain_url" {
  description = "URL pública do domínio customizado (vazio se não configurado)."
  value       = var.domain_name != "" ? "https://${var.domain_name}" : ""
}

output "acm_certificate_arn" {
  description = "ARN do certificado ACM do domínio customizado (vazio se não configurado)."
  value       = var.domain_name != "" ? module.acm[0].certificate_arn : ""
}

output "http_api_endpoint" {
  description = "Endpoint do API Gateway HTTP API (origem /api/* do CloudFront)."
  value       = module.compute.http_api_endpoint
}

output "dynamodb_table_name" {
  description = "Nome da tabela DynamoDB."
  value       = module.data.table_name
}

output "spa_bucket_id" {
  description = "Nome do bucket S3 da SPA (destino do build frontend/dist)."
  value       = module.spa_bucket.bucket_id
}

output "media_bucket_id" {
  description = "Nome do bucket S3 de mídia (uploads em links/*)."
  value       = module.media_bucket.bucket_id
}
