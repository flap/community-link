# Composição do ambiente PROD — Community Link (pastel).
# Orquestra os módulos: data (DynamoDB), storage (S3 x2), compute (Lambda + HTTP API),
# edge (CloudFront + OAC + 2 Functions).

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# Provider aliasado para a CONTA DE DNS (Opção A).
#
# O app inteiro (S3, Lambda, DynamoDB, CloudFront, certificado ACM) é criado na
# conta default (app, 390686807269). APENAS os registros Route 53 (validação do
# ACM e ALIAS do subdomínio) são criados na conta de DNS (070008302080), onde
# vive a hosted zone awscommunity.com.br — assumindo var.dns_account_role_arn.
#
# Fallback: se dns_account_role_arn estiver vazio, este provider aponta para a
# própria conta default (útil quando a zona está na mesma conta, p.ex. testes).
provider "aws" {
  alias  = "dns"
  region = var.aws_region

  dynamic "assume_role" {
    for_each = var.dns_account_role_arn != "" ? [var.dns_account_role_arn] : []
    content {
      role_arn     = assume_role.value
      session_name = "community-link-prod-dns"
    }
  }

  default_tags {
    tags = var.tags
  }
}

data "aws_caller_identity" "current" {}

locals {
  # ARNs dos parâmetros SSM que a Lambda pode ler (least-privilege no prefixo backend).
  ssm_parameter_arns = [
    "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.config_ssm_path}",
    "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.config_ssm_path}/*",
  ]
}

# --- Dados ----------------------------------------------------------------
module "data" {
  source = "../../modules/data"

  table_name = var.dynamodb_table_name
  tags       = var.tags
}

# --- Storage (buckets privados) -------------------------------------------
module "spa_bucket" {
  source = "../../modules/storage"

  bucket_name = var.spa_bucket_name
  tags        = var.tags
}

module "media_bucket" {
  source = "../../modules/storage"

  bucket_name        = var.media_bucket_name
  versioning_enabled = true
  tags               = var.tags
}

# Policies OAC aplicadas aqui (após a distribuição existir) para quebrar o ciclo
# storage <-> edge. Só a distribuição CloudFront deste ambiente pode ler os objetos.
data "aws_iam_policy_document" "spa_oac" {
  statement {
    sid       = "AllowCloudFrontOACRead"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${module.spa_bucket.bucket_arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [module.edge.distribution_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "spa_oac" {
  bucket = module.spa_bucket.bucket_id
  policy = data.aws_iam_policy_document.spa_oac.json
}

data "aws_iam_policy_document" "media_oac" {
  statement {
    sid       = "AllowCloudFrontOACRead"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${module.media_bucket.bucket_arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [module.edge.distribution_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "media_oac" {
  bucket = module.media_bucket.bucket_id
  policy = data.aws_iam_policy_document.media_oac.json
}

# --- Compute (Lambda + HTTP API) ------------------------------------------
module "compute" {
  source = "../../modules/compute"

  function_name       = "${var.name_prefix}-api"
  lambda_package_path = var.lambda_package_path
  runtime             = "python3.12"
  handler             = "app.lambda_handler.handler"
  config_ssm_path     = var.config_ssm_path
  ssm_parameter_arns  = local.ssm_parameter_arns
  dynamodb_table_arn  = module.data.table_arn
  media_bucket_arn    = module.media_bucket.bucket_arn
  media_bucket_name   = module.media_bucket.bucket_id
  aws_region          = var.aws_region
  tags                = var.tags
}

# --- DNS: lookup da hosted zone (quando há domínio customizado) -----------
# A zona vive na CONTA DE DNS -> usa o provider aliasado aws.dns.
data "aws_route53_zone" "this" {
  provider     = aws.dns
  count        = var.domain_name != "" ? 1 : 0
  name         = var.hosted_zone_name
  private_zone = false
}

# --- ACM: certificado do domínio customizado (us-east-1) ------------------
# Cert na conta do app (provider default); registros de validação na conta de
# DNS (aws.dns). Não depende do CloudFront; o grafo fica linear: acm -> edge -> dns-alias.
module "acm" {
  source = "../../modules/acm"
  count  = var.domain_name != "" ? 1 : 0

  providers = {
    aws     = aws
    aws.dns = aws.dns
  }

  domain_name    = var.domain_name
  hosted_zone_id = data.aws_route53_zone.this[0].zone_id
  tags           = var.tags
}

# --- Edge (CloudFront) ----------------------------------------------------
module "edge" {
  source = "../../modules/edge"

  name_prefix                       = var.name_prefix
  spa_bucket_regional_domain_name   = module.spa_bucket.bucket_regional_domain_name
  media_bucket_regional_domain_name = module.media_bucket.bucket_regional_domain_name
  api_origin_domain_name            = replace(module.compute.http_api_endpoint, "https://", "")
  aliases                           = var.domain_name != "" ? [var.domain_name] : []
  acm_certificate_arn               = var.domain_name != "" ? module.acm[0].certificate_arn : ""
  tags                              = var.tags
}

# --- DNS: registros ALIAS A/AAAA apontando o domínio para o CloudFront ----
# Registros na CONTA DE DNS -> instancia o módulo com providers = { aws = aws.dns }.
module "dns_alias" {
  source = "../../modules/dns-alias"
  count  = var.domain_name != "" ? 1 : 0

  providers = {
    aws = aws.dns
  }

  domain_name                 = var.domain_name
  hosted_zone_id              = data.aws_route53_zone.this[0].zone_id
  distribution_domain_name    = module.edge.distribution_domain_name
  distribution_hosted_zone_id = module.edge.distribution_hosted_zone_id
}
