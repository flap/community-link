output "distribution_id" {
  description = "ID da distribuição CloudFront."
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "ARN da distribuição (usar nas policies OAC dos buckets S3)."
  value       = aws_cloudfront_distribution.this.arn
}

output "distribution_domain_name" {
  description = "Domínio público da distribuição (ex.: dxxxx.cloudfront.net)."
  value       = aws_cloudfront_distribution.this.domain_name
}

output "distribution_hosted_zone_id" {
  description = "Hosted zone ID do CloudFront (constante Z2FDTNDATAQYW2), usado em registros ALIAS do Route 53."
  value       = aws_cloudfront_distribution.this.hosted_zone_id
}
