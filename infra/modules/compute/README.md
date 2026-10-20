# Módulo `compute` — Lambda + API Gateway HTTP API

Infraestrutura serverless da API: função Lambda (FastAPI empacotado com Mangum,
handler `app.lambda_handler.handler`, runtime `python3.12`) exposta por um
API Gateway **HTTP API** com rota `$default`.

## Descrição

- IAM de execução **least-privilege**:
  - DynamoDB restrito ao ARN da tabela única.
  - S3 `PutObject`/`GetObject` restrito ao prefixo `links/*` do bucket de mídia.
  - SSM `GetParametersByPath`/`GetParameter(s)` restrito aos ARNs informados.
  - KMS `Decrypt` apenas quando uma CMK é informada (SecureString).
  - Logs restritos ao Log Group da própria função.
- Log Group explícito com retenção configurável.
- `$default` route + `$default` stage com `auto_deploy`.
- `aws_lambda_permission` autoriza o HTTP API a invocar a função.

> A config completa é lida de SSM no cold start (ver `backend/app/lambda_handler.py`);
> só `CONFIG_SSM_PATH`, `AWS_REGION_NAME` e `MEDIA_BUCKET` entram como env vars.
> **Nenhum segredo** é passado por variável/tfvars/state.

## Uso

```hcl
module "compute" {
  source = "../../modules/compute"

  function_name       = "community-link-api-prod"
  lambda_package_path = "${path.module}/../../artifacts/backend.zip"
  config_ssm_path     = "/community-link/beta/backend"
  ssm_parameter_arns  = ["arn:aws:ssm:us-east-1:123456789012:parameter/community-link/beta/backend/*"]
  dynamodb_table_arn  = module.data.table_arn
  media_bucket_arn    = module.media_bucket.bucket_arn
  media_bucket_name   = module.media_bucket.bucket_id
  tags                = { Environment = "prod" }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0, < 2.0.0 |
| aws | ~> 5.0 |

## Inputs (principais)

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `function_name` | Nome da Lambda. | `string` | n/a |
| `lambda_package_path` | Caminho do .zip do backend. | `string` | n/a |
| `runtime` | Runtime da Lambda. | `string` | `python3.12` |
| `handler` | Entrypoint. | `string` | `app.lambda_handler.handler` |
| `config_ssm_path` | Prefixo SSM lido no cold start. | `string` | n/a |
| `ssm_parameter_arns` | ARNs SSM legíveis (least-privilege). | `list(string)` | n/a |
| `dynamodb_table_arn` | ARN da tabela DynamoDB. | `string` | n/a |
| `media_bucket_arn` | ARN do bucket de mídia. | `string` | n/a |
| `media_bucket_name` | Nome do bucket de mídia. | `string` | n/a |
| `kms_key_arn` | CMK para SecureString (opcional). | `string` | `""` |
| `log_retention_days` | Retenção de logs. | `number` | `14` |

## Outputs

| Name | Description |
|------|-------------|
| `function_name` / `function_arn` | Identificadores da Lambda. |
| `http_api_id` / `http_api_endpoint` | Identificadores do HTTP API. |
| `lambda_role_arn` | ARN da role de execução. |
