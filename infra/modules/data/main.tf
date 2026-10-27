# DynamoDB single-table design (ver backend/app/dynamo_repository.py).
# Chaves: PK (HASH) + SK (RANGE). Cobrança on-demand (PAY_PER_REQUEST).
# GSIs de busca (RF-012/RF-013 — Fase 2b):
#   GSI1: GSI1PK=TYPE#{type}       GSI1SK={created_at}#{id}   (por tipo + data)
#   GSI2: GSI2PK=AUTHOR#{author}   GSI2SK={created_at}#{id}   (por autor, sparse)
# Ambos ProjectionType=ALL (resultado de busca carrega o link completo + origem).

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

  # Atributos de índice de busca (Fase 2b).
  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  attribute {
    name = "GSI2PK"
    type = "S"
  }

  attribute {
    name = "GSI2SK"
    type = "S"
  }

  # GSI1 — busca por tipo com range/ordenação por data (RF-012).
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  # GSI2 — busca por autor (sparse: só links com autor) (RF-013).
  global_secondary_index {
    name            = "GSI2"
    hash_key        = "GSI2PK"
    range_key       = "GSI2SK"
    projection_type = "ALL"
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
