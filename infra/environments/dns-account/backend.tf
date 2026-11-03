# State da composição dns-account.
#
# Esta composição roda na CONTA DE DNS (070008302080), separada do state do app.
# O state fica no bucket DAQUELA conta (nunca no bucket da conta do app):
# community-link-tfstate-070008302080 (versionado, SSE-S3, public-access-block,
# deny-non-TLS, prevent_destroy — criado por infra/bootstrap/), com lock na
# tabela DynamoDB community-link-tflock da mesma conta.
#
# VERSION FLOOR: runtime local Terraform 1.5.7 (< 1.10) => sem `use_lockfile`.
# Locking via `dynamodb_table`. Migrar para `use_lockfile` em Terraform >= 1.10.

terraform {
  backend "s3" {
    bucket         = "community-link-tfstate-070008302080"
    key            = "dns-account/community-link/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "community-link-tflock"
    # use_lockfile = true   # habilitar somente em Terraform >= 1.10 (remover dynamodb_table)
  }
}
