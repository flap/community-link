# Exemplo MÍNIMO: apenas a tabela DynamoDB (módulo `data`).
# Serve como fixture de teste e documentação do contrato mínimo do módulo.

provider "aws" {
  region = "us-east-1"
}

module "data" {
  source = "../../modules/data"

  table_name = "community-link-example"

  tags = {
    Project = "community-link"
    Example = "minimal"
  }
}

output "table_name" {
  description = "Nome da tabela criada no exemplo."
  value       = module.data.table_name
}
