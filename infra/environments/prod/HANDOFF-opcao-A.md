# Handoff — Prod na Opção A (app em 390686807269, DNS em 070008302080)

Decisão do usuário: o ambiente **prod roda na conta 390686807269** (a mesma do
staging). A conta **070008302080** hospeda **apenas** a hosted zone Route 53 do
domínio `awscommunity.com.br`. O SSM de configuração fica **nesta** conta
(390686807269), junto da Lambda que o lê.

## Causa-raiz do loop em https://link.awscommunity.com.br/admin (diagnóstico)

O domínio apontava para uma distribuição CloudFront na conta 070008302080
(deploy de prod do agente paralelo). Dois defeitos de configuração:

1. `config_ssm_path = "/community-link/beta/backend"` — ambiente `beta` foi
   destruído; o path não existe em conta nenhuma. A Lambda subia sem
   `CL_SUPABASE_URL` / `CL_AUTH_MODE` / `CL_CORS_ORIGINS`, quebrando o fluxo de
   auth → loop `/admin ↔ /login`.
2. O prod lia o SSM da própria conta (070008302080) via
   `data.aws_caller_identity.current.account_id`, mas o SSM não existia lá.

## Ajustes JÁ FEITOS nesta sessão (conta 390686807269)

- `prod/terraform.tfvars`: buckets → `community-link-{spa,media}-prod-390686807269`;
  `config_ssm_path` → `/community-link/prod/backend`.
- `prod/variables.tf`: default de `config_ssm_path` → `/community-link/prod/backend`;
  nova variável `dns_account_role_arn` (role a assumir na conta de DNS).
- `prod/backend.tf`: state → bucket `community-link-tfstate` (desta conta),
  key `prod/community-link/terraform.tfstate`, lock `community-link-tflock`.
- **SSM de prod criado nesta conta** em `/community-link/prod/{backend,frontend}/*`
  (10 parâmetros; `VITE_SUPABASE_ANON_KEY` como SecureString;
  `CL_CORS_ORIGINS = https://link.awscommunity.com.br`).

## PENDENTE — precisa do dono do prod (agente paralelo) + credenciais das 2 contas

O cross-account DNS NÃO foi implementado aqui (não há credenciais da conta de DNS
neste shell para validar com `plan`). Para concluir a Opção A:

1. **Provider aliasado `aws.dns`** em `prod/main.tf` assumindo `var.dns_account_role_arn`
   na conta 070008302080 (onde está a hosted zone). O provider default
   permanece na conta do app (390686807269).
2. **Módulo `acm`** precisa de DOIS providers (`configuration_aliases`): o
   `aws_acm_certificate` + `aws_acm_certificate_validation` ficam na conta do
   app (o CloudFront exige o cert na mesma conta, us-east-1), mas os
   `aws_route53_record` de validação vão para a conta de DNS (provider `aws.dns`).
3. **Módulo `dns-alias`** recebe o provider `aws.dns` (registros ALIAS A/AAAA na
   conta de DNS).
4. `data.aws_route53_zone.this` usa o provider `aws.dns`.
5. Role cross-account na conta de DNS (ex.: `community-link-dns-manager`) com
   permissão de `route53:ChangeResourceRecordSets`/`ListHostedZones` na zona, e
   trust para a identidade que roda o Terraform na conta do app. Passar o ARN em
   `dns_account_role_arn`.
6. Remover/retirar de serviço a distribuição CloudFront de prod que ficou na
   conta 070008302080 (a que o domínio aponta hoje) — senão o alias colide:
   um CNAME/alias só pode estar ativo em uma distribuição por vez.
7. Rebuild do frontend lendo as `VITE_*` do SSM desta conta e deploy; garantir
   que o **Site URL** e **Redirect URL** no painel do Supabase são
   `https://link.awscommunity.com.br` (Redirect `/admin`).

## Validação esperada após o apply

- `link.awscommunity.com.br` resolve para a distribuição na conta 390686807269.
- `GET /api/health` 200; `/admin` sem token → `/login` (sem loop); após login,
  `/api/admin/me` 200 com CORS `https://link.awscommunity.com.br`.
