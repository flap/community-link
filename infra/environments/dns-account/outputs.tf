output "dns_manager_role_arn" {
  description = "ARN da role cross-account. Copie para prod/terraform.tfvars em dns_account_role_arn."
  value       = aws_iam_role.dns_manager.arn
}

output "hosted_zone_id" {
  description = "ID da hosted zone gerida."
  value       = data.aws_route53_zone.this.zone_id
}

output "hosted_zone_arn" {
  description = "ARN da hosted zone (escopo da policy)."
  value       = data.aws_route53_zone.this.arn
}
