# State remoto S3 com locking (ambiente staging).
#
# VERSION FLOOR: runtime local Terraform 1.5.7 (< 1.10) => sem `use_lockfile`.
# Locking via `dynamodb_table`. Migrar para `use_lockfile` em Terraform >= 1.10.

terraform {
  backend "s3" {
    bucket         = "community-link-tfstate"
    key            = "staging/community-link/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "community-link-tflock"
    # use_lockfile = true   # habilitar somente em Terraform >= 1.10 (remover dynamodb_table)
  }
}
