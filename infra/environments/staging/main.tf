# Composição do ambiente STAGING — Community Link (pastel).
# Mesma topologia de prod, com valores reduzidos (sem PITR/deletion protection,
# sem versionamento de mídia) — decisões específicas do ambiente ficam aqui,
# na composição, não nos módulos.

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

data "aws_caller_identity" "current" {}

locals {
  ssm_parameter_arns = [
    "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.config_ssm_path}",
    "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.config_ssm_path}/*",
  ]
}

module "data" {
  source = "../../modules/data"

  table_name                     = var.dynamodb_table_name
  point_in_time_recovery_enabled = false
  deletion_protection_enabled    = false
  tags                           = var.tags
}

module "spa_bucket" {
  source = "../../modules/storage"

  bucket_name = var.spa_bucket_name
  tags        = var.tags
}

module "media_bucket" {
  source = "../../modules/storage"

  bucket_name = var.media_bucket_name
  tags        = var.tags
}

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

module "compute" {
  source = "../../modules/compute"

  function_name       = "${var.name_prefix}-api"
  lambda_package_path = var.lambda_package_path
  runtime             = "python3.12"
  handler             = "app.lambda_handler.handler"
  memory_size         = 512
  timeout             = 20
  config_ssm_path     = var.config_ssm_path
  ssm_parameter_arns  = local.ssm_parameter_arns
  dynamodb_table_arn  = module.data.table_arn
  media_bucket_arn    = module.media_bucket.bucket_arn
  media_bucket_name   = module.media_bucket.bucket_id
  aws_region          = var.aws_region
  log_retention_days  = 7
  tags                = var.tags
}

module "edge" {
  source = "../../modules/edge"

  name_prefix                       = var.name_prefix
  spa_bucket_regional_domain_name   = module.spa_bucket.bucket_regional_domain_name
  media_bucket_regional_domain_name = module.media_bucket.bucket_regional_domain_name
  api_origin_domain_name            = replace(module.compute.http_api_endpoint, "https://", "")
  tags                              = var.tags
}
