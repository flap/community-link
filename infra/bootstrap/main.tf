# Bootstrap do backend de state remoto (Terraform).
#
# Cria os recursos que os backends S3 dos ambientes (prod/staging) referenciam:
#   - Bucket S3 de state: versionado, criptografado (SSE-S3), acesso público bloqueado.
#   - Tabela DynamoDB de lock: PAY_PER_REQUEST, chave de hash `LockID`.
#
# CHICKEN-AND-EGG: esta composição NÃO pode guardar seu próprio state no bucket
# que ela cria. Por isso usa STATE LOCAL (ver backend ausente de propósito).
# O arquivo terraform.tfstate resultante fica neste diretório e é commitado
# (contém apenas o bucket/tabela de bootstrap — sem segredos). Alternativamente,
# migre-o para o próprio bucket depois de criado com `terraform init -migrate-state`.

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# --- Bucket S3 de state ---------------------------------------------------
resource "aws_s3_bucket" "state" {
  bucket = var.state_bucket_name

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Impede uploads sem criptografia e acesso não-TLS.
data "aws_iam_policy_document" "state" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = data.aws_iam_policy_document.state.json
}

# --- Tabela DynamoDB de lock ----------------------------------------------
resource "aws_dynamodb_table" "lock" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}
