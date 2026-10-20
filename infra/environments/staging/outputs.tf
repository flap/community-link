output "cloudfront_domain_name" {
  description = "Domínio público do CloudFront (ponto de entrada do projeto)."
  value       = module.edge.distribution_domain_name
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
  description = "Nome do bucket S3 da SPA."
  value       = module.spa_bucket.bucket_id
}

output "media_bucket_id" {
  description = "Nome do bucket S3 de mídia."
  value       = module.media_bucket.bucket_id
}
