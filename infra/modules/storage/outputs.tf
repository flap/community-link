output "bucket_id" {
  description = "ID (nome) do bucket S3."
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN do bucket S3 (para políticas IAM)."
  value       = aws_s3_bucket.this.arn
}

output "bucket_regional_domain_name" {
  description = "Domínio regional do bucket (usar como origem do CloudFront)."
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}
