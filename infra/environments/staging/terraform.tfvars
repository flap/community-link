# Valores específicos do ambiente STAGING.
# NENHUM segredo aqui — Supabase e afins vivem no SSM Parameter Store / Secrets Manager.

aws_region          = "us-east-1"
name_prefix         = "community-link-staging"
dynamodb_table_name = "community-link-staging"

spa_bucket_name   = "community-link-spa-staging-390686807269"
media_bucket_name = "community-link-media-staging-390686807269"

config_ssm_path     = "/community-link/staging/backend"
lambda_package_path = "../../artifacts/backend.zip"

tags = {
  Project     = "community-link"
  Environment = "staging"
  ManagedBy   = "Terraform"
}
