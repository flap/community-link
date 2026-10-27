# Valores específicos do ambiente PROD.
# NENHUM segredo aqui — Supabase e afins vivem no SSM Parameter Store / Secrets Manager.
# Os nomes de bucket precisam ser globalmente únicos; ajuste conforme a conta.

aws_region          = "us-east-1"
name_prefix         = "community-link-prod"
dynamodb_table_name = "community-link"

# Domínio customizado (link padrão do projeto). Deixe domain_name = "" para
# desativar ACM/Route 53 e usar apenas o domínio *.cloudfront.net.
domain_name      = "link.awscommunity.com.br"
hosted_zone_name = "awscommunity.com.br"

spa_bucket_name   = "community-link-spa-prod-390686807269"
media_bucket_name = "community-link-media-prod-390686807269"

config_ssm_path     = "/community-link/prod/backend"
lambda_package_path = "../../artifacts/backend.zip"

tags = {
  Project     = "community-link"
  Environment = "prod"
  ManagedBy   = "Terraform"
}
