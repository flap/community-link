# DynamoDB single-table design (ver backend/app/dynamo_repository.py).
# Chaves: PK (HASH) + SK (RANGE). Cobrança on-demand (PAY_PER_REQUEST).
# SEM GSI/LSI — o acesso é por PK + begins_with(SK), conforme o repositório.

resource "aws_dynamodb_table" "community_link" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery_enabled
  }

  # Criptografia em repouso com chave gerenciada pela AWS (SSE padrão).
  server_side_encryption {
    enabled = true
  }

  deletion_protection_enabled = var.deletion_protection_enabled

  tags = var.tags
}
