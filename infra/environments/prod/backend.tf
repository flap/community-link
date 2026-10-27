# State remoto S3 com locking.
#
# ARQUITETURA (Opção A): o ambiente prod roda na conta 390686807269 (mesma do
# staging); a conta 070008302080 hospeda APENAS a hosted zone Route 53 do
# domínio awscommunity.com.br. Portanto o state fica no bucket desta conta.
#
# VERSION FLOOR: o runtime local é Terraform 1.5.7 (< 1.10), portanto o locking
# nativo via arquivo (`use_lockfile`) NÃO está disponível. Usamos `dynamodb_table`
# para o lock. Ao atualizar o runtime para >= 1.10, migre para `use_lockfile`.

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
