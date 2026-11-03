# Ambiente `dns-account` — Role cross-account de DNS (Opção A)

Esta composição é aplicada **na conta de DNS `070008302080`** (a que hospeda a
hosted zone Route 53 de `awscommunity.com.br`). Ela cria a IAM role
`community-link-dns-manager` que o ambiente `prod` (rodando na conta do app
`390686807269`) assume via o provider aliasado `aws.dns` para:

- criar/alterar os registros **CNAME de validação do ACM**; e
- criar os registros **ALIAS A/AAAA** de `link.awscommunity.com.br` apontando
  para a distribuição CloudFront na conta do app.

A permissão é de **least-privilege**: apenas `route53:ChangeResourceRecordSets`,
`route53:ListResourceRecordSets`, `route53:GetHostedZone` na zona específica;
`route53:ListHostedZones*` e `route53:GetChange` a nível de conta (exigidos pela
API, não suportam restrição por recurso).

> **Separação de contas:** NÃO pode fazer parte da composição `prod` — aquela
> composição autentica na conta do app. Esta roda com credenciais da conta de
> DNS. Por isso vive em um diretório próprio com state próprio.

## Pré-requisitos

- Credenciais/perfil da conta `070008302080` com permissão de IAM + Route 53.
- A hosted zone pública `awscommunity.com.br` já existente nessa conta.

## Uso

```bash
cd infra/environments/dns-account

# Autentique na CONTA DE DNS (070008302080). Ex.: export AWS_PROFILE=dns-account
terraform init                       # backend S3 (ver backend.tf) — ajuste se necessário
terraform fmt -recursive
terraform validate

terraform plan -out=dns.tfplan       # REVISAR o diff
terraform apply dns.tfplan           # cria a role + policy
terraform output dns_manager_role_arn
```

Copie o ARN de saída para `infra/environments/prod/terraform.tfvars`
(`dns_account_role_arn`). O default já é
`arn:aws:iam::070008302080:role/community-link-dns-manager`.

## Trust policy

A role confia na **conta do app inteira** (`arn:aws:iam::390686807269:root`),
delegando a decisão de quem pode assumir às policies de IAM da conta do app.
Se preferir granularidade, troque o principal pelo ARN exato da role/identidade
que roda o Terraform (ex.: a role do SSO `AWSReservedSSO_AdministratorAccess_*`
ou a role de CI/OIDC) em `var.trusted_principal_arns`.

## Segurança / rollback

- `terraform plan -destroy` + aprovação antes de remover a role.
- Remover a role quebra o `plan`/`apply` do ambiente `prod` (o provider `aws.dns`
  não conseguirá assumir). Mantenha-a enquanto o domínio for gerido via IaC.
