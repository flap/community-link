variable "aws_region" {
  description = "Região AWS onde criar o bucket de state e a tabela de lock."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Nome do bucket S3 de state remoto (deve bater com o backend.tf dos ambientes). Nomes de bucket são globais; sufixo com account id garante unicidade."
  type        = string
  default     = "community-link-tfstate-070008302080"
}

variable "lock_table_name" {
  description = "Nome da tabela DynamoDB de lock (deve bater com o backend.tf dos ambientes)."
  type        = string
  default     = "community-link-tflock"
}

variable "tags" {
  description = "Tags aplicadas aos recursos de bootstrap."
  type        = map(string)
  default = {
    Project   = "community-link"
    Component = "tfstate-bootstrap"
    ManagedBy = "Terraform"
  }
}
