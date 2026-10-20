# Módulo `data` — DynamoDB single-table

Cria a tabela DynamoDB single-table do Community Link, conforme
`backend/app/dynamo_repository.py`.

## Descrição

- Chaves: `PK` (HASH) + `SK` (RANGE), ambas `String`.
- Cobrança: `PAY_PER_REQUEST` (on-demand).
- **Sem GSI/LSI** — o acesso é por `PK` + `begins_with(SK, ...)`.
- Criptografia em repouso habilitada (chave gerenciada AWS).
- PITR e deletion protection ativáveis (ligados por padrão).

## Uso

```hcl
module "data" {
  source = "../../modules/data"

  table_name = "community-link"
  tags       = { Environment = "prod" }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0, < 2.0.0 |
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `table_name` | Nome da tabela DynamoDB single-table. | `string` | n/a |
| `point_in_time_recovery_enabled` | Habilita PITR. | `bool` | `true` |
| `deletion_protection_enabled` | Protege a tabela contra exclusão. | `bool` | `true` |
| `tags` | Tags aplicadas aos recursos. | `map(string)` | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| `table_name` | Nome da tabela (para `CL_DYNAMODB_TABLE`). |
| `table_arn` | ARN da tabela (para políticas IAM). |
