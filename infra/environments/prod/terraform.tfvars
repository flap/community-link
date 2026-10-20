# Valores específicos do ambiente PROD.
# NENHUM segredo aqui — Supabase e afins vivem no SSM Parameter Store / Secrets Manager.
# Os nomes de bucket precisam ser globalmente únicos; ajuste conforme a conta.

aws_region          = "us-east-1"
name_prefix         = "community-link-prod"
dynamodb_table_name = "community-link"

spa_bucket_name   = "community-link-spa-prod-REPLACE-ME"
media_bucket_name = "community-link-media-prod-REPLACE-ME"

config_ssm_path     = "/community-link/beta/backend"
lambda_package_path = "../../artifacts/backend.zip"

tags = {
  Project     = "community-link"
  Environment = "prod"
  ManagedBy   = "Terraform"
}
