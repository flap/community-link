output "function_name" {
  description = "Nome da função Lambda."
  value       = aws_lambda_function.api.function_name
}

output "function_arn" {
  description = "ARN da função Lambda."
  value       = aws_lambda_function.api.arn
}

output "http_api_id" {
  description = "ID do API Gateway HTTP API."
  value       = aws_apigatewayv2_api.http.id
}

output "http_api_endpoint" {
  description = "Endpoint base do HTTP API (origem /api/* do CloudFront)."
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "lambda_role_arn" {
  description = "ARN da role de execução da Lambda."
  value       = aws_iam_role.lambda_exec.arn
}
