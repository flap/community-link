output "fqdn" {
  description = "FQDN publicado (registro ALIAS A)."
  value       = aws_route53_record.alias_a.fqdn
}
