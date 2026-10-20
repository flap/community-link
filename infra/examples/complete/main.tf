# Exemplo COMPLETO: fia todos os módulos (data + storage x2 + compute + edge),
# reproduzindo a composição de um ambiente real, com valores de exemplo.
# Serve como documentação de integração e fixture de teste.

provider "aws" {
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

locals {
  config_ssm_path = "/community-link/beta/backend"
  ssm_parameter_arns = [
    "arn:aws:ssm:us-east-1:${data.aws_caller_identity.current.account_id}:parameter${local.config_ssm_path}",
    "arn:aws:ssm:us-east-1:${data.aws_caller_identity.current.account_id}:parameter${local.config_ssm_path}/*",
  ]
  tags = {
    Project = "community-link"
    Example = "complete"
  }
}

module "data" {
  source = "../../modules/data"

  table_name = "community-link-example"
  tags       = local.tags
}

module "spa_bucket" {
  source = "../../modules/storage"

  bucket_name = "community-link-spa-example"
  tags        = local.tags
}

module "media_bucket" {
  source = "../../modules/storage"

  bucket_name        = "community-link-media-example"
  versioning_enabled = true
  tags               = local.tags
}

module "compute" {
  source = "../../modules/compute"

  function_name       = "community-link-api-example"
  lambda_package_path = "${path.module}/backend-example.zip"
  config_ssm_path     = local.config_ssm_path
  ssm_parameter_arns  = local.ssm_parameter_arns
  dynamodb_table_arn  = module.data.table_arn
  media_bucket_arn    = module.media_bucket.bucket_arn
  media_bucket_name   = module.media_bucket.bucket_id
  tags                = local.tags
}

module "edge" {
  source = "../../modules/edge"

  name_prefix                       = "community-link-example"
  spa_bucket_regional_domain_name   = module.spa_bucket.bucket_regional_domain_name
  media_bucket_regional_domain_name = module.media_bucket.bucket_regional_domain_name
  api_origin_domain_name            = replace(module.compute.http_api_endpoint, "https://", "")
  tags                              = local.tags
}

output "cloudfront_domain_name" {
  description = "Domínio público do CloudFront."
  value       = module.edge.distribution_domain_name
}
