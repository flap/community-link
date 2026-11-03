output "certificate_arn" {
  description = "ARN do certificado ACM já validado (pronto para o CloudFront)."
  value       = aws_acm_certificate_validation.this.certificate_arn
}
