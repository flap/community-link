# Bootstrap do backend de state

Composição Terraform que cria, **uma única vez**, os recursos de state remoto
referenciados pelos `backend.tf` dos ambientes (`prod`/`staging`):

| Recurso | Nome padrão | Config |
|---------|-------------|--------|
| Bucket S3 de state | `community-link-tfstate-070008302080` | versionado, SSE-S3, acesso público bloqueado, deny non-TLS |
| Tabela DynamoDB de lock | `community-link-tflock` | `PAY_PER_REQUEST`, hash key `LockID` |

## Chicken-and-egg (state local)

Esta composição **não** guarda seu próprio state no bucket que cria — usa
**state local** (`terraform.tfstate` neste diretório). Esse arquivo contém apenas
os recursos de bootstrap (sem segredos) e pode ser commitado, ou migrado para o
próprio bucket depois com `terraform init -migrate-state`.

Os recursos têm `prevent_destroy = true` para evitar remoção acidental do state
de todos os ambientes.

## Uso

```bash
cd infra/bootstrap
terraform init            # state local (sem bloco backend)
terraform plan -out=bootstrap.tfplan
terraform apply bootstrap.tfplan
```

Depois disso, os ambientes podem inicializar o backend remoto:

```bash
cd ../environments/prod
terraform init            # agora encontra o bucket + tabela de lock
```

## Inputs

| Nome | Descrição | Default |
|------|-----------|---------|
| `aws_region` | Região dos recursos. | `us-east-1` |
| `state_bucket_name` | Nome do bucket de state. | `community-link-tfstate-070008302080` |
| `lock_table_name` | Nome da tabela de lock. | `community-link-tflock` |
| `tags` | Tags. | ver `variables.tf` |
