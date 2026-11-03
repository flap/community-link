# Role cross-account de DNS (Opção A) — APLICAR NA CONTA DE DNS (070008302080).
#
# Cria a IAM role que o ambiente prod (conta do app 390686807269) assume via o
# provider aliasado `aws.dns` para gerir os registros Route 53 da hosted zone
# awscommunity.com.br (validação do ACM + ALIAS do subdomínio).

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# Lookup da hosted zone para restringir a policy ao ARN exato da zona.
data "aws_route53_zone" "this" {
  name         = var.hosted_zone_name
  private_zone = false
}

# --- Trust policy: quem pode assumir a role -------------------------------
data "aws_iam_policy_document" "trust" {
  statement {
    sid     = "AllowAppAccountAssume"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = var.trusted_principal_arns
    }
  }
}

resource "aws_iam_role" "dns_manager" {
  name                 = var.role_name
  description          = "Cross-account DNS manager assumido pela conta do app para gerir Route 53 de ${var.hosted_zone_name}."
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = 3600

  tags = var.tags
}

# --- Permissões (least-privilege na zona) ---------------------------------
data "aws_iam_policy_document" "dns" {
  # Operações restritas à hosted zone específica.
  statement {
    sid    = "ManageRecordsInZone"
    effect = "Allow"
    actions = [
      "route53:ChangeResourceRecordSets",
      "route53:ListResourceRecordSets",
      "route53:GetHostedZone",
      # Exigido pelo data source aws_route53_zone (lê as tags da zona).
      "route53:ListTagsForResource",
    ]
    resources = [data.aws_route53_zone.this.arn]
  }

  # Estas ações da API não suportam restrição por recurso (precisam de "*").
  statement {
    sid    = "ListAndTrackChanges"
    effect = "Allow"
    actions = [
      "route53:ListHostedZones",
      "route53:ListHostedZonesByName",
      "route53:GetChange",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "dns" {
  name   = "${var.role_name}-route53"
  role   = aws_iam_role.dns_manager.id
  policy = data.aws_iam_policy_document.dns.json
}
