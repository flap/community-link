output "table_name" {
  description = "Nome da tabela DynamoDB (usar em CL_DYNAMODB_TABLE)."
  value       = aws_dynamodb_table.community_link.name
}

output "table_arn" {
  description = "ARN da tabela DynamoDB (usar em políticas IAM da Lambda)."
  value       = aws_dynamodb_table.community_link.arn
}
