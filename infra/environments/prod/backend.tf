# State remoto S3 com locking.
#
# VERSION FLOOR: o runtime local é Terraform 1.5.7 (< 1.10), portanto o locking
# nativo via arquivo (`use_lockfile`) NÃO está disponível. Usamos `dynamodb_table`
# para o lock. Ao atualizar o runtime para >= 1.10, migre para `use_lockfile`
# (passe os dois durante a transição e remova `dynamodb_table` depois).
#
# Valores sensíveis/variáveis (key, dynamodb_table) podem vir via -backend-config.
# Este esqueleto NÃO configura backend real; `terraform init -backend=false`.

terraform {
  backend "s3" {
    bucket         = "community-link-tfstate"
    key            = "prod/community-link/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "community-link-tflock"
    # use_lockfile = true   # habilitar somente em Terraform >= 1.10 (remover dynamodb_table)
  }
}
