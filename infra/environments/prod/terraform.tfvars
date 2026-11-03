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

# Opção A — cross-account DNS: role a assumir na conta que hospeda a hosted zone
# Route 53 de awscommunity.com.br (conta de DNS 070008302080). O provider aws.dns
# assume esta role para criar os registros de validação do ACM e o ALIAS do
# subdomínio. A role precisa existir e confiar na identidade que roda o Terraform
# na conta do app (390686807269). Ver infra/modules/dns-account-role/.
dns_account_role_arn = "arn:aws:iam::070008302080:role/community-link-dns-manager"

tags = {
  Project     = "community-link"
  Environment = "prod"
  ManagedBy   = "Terraform"
}
