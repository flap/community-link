# Ambiente `staging` — Community Link (pastel)

Mesma topologia do `prod`, com dimensionamento reduzido para um ambiente de
homologação:

- DynamoDB **sem** PITR e **sem** deletion protection.
- Bucket de mídia **sem** versionamento.
- Logs da Lambda com retenção de 7 dias.
- State S3 em `staging/community-link/terraform.tfstate` (locking via DynamoDB).

Essas diferenças são decisões da **composição** (não dos módulos), exatamente
como recomenda a skill: módulos genéricos, valores por ambiente na composição.

## Uso (sem deploy real)

```bash
terraform init -backend=false
terraform fmt -recursive
terraform validate
```

Ver o README de `prod` para o fluxo completo de state remoto e segredos — as
regras são idênticas, mudando apenas os valores específicos do ambiente.
