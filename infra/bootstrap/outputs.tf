output "state_bucket_name" {
  description = "Nome do bucket S3 de state remoto."
  value       = aws_s3_bucket.state.id
}

output "state_bucket_arn" {
  description = "ARN do bucket S3 de state remoto."
  value       = aws_s3_bucket.state.arn
}

output "lock_table_name" {
  description = "Nome da tabela DynamoDB de lock."
  value       = aws_dynamodb_table.lock.name
}
