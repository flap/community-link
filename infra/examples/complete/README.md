# Exemplo `complete`

Fia todos os módulos (`data` + `storage` ×2 + `compute` + `edge`) reproduzindo a
composição de um ambiente real, com valores de exemplo. Documenta como os
módulos se integram (OAC, origens do CloudFront, least-privilege IAM).

```bash
terraform init -backend=false
terraform validate
```

> `terraform plan`/`apply` exigiriam um `backend-example.zip` real e credenciais
> AWS — fora do escopo deste esqueleto de demonstração.
