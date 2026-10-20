# Borda: 1 distribuição CloudFront com 3 origens (SPA, media, API HTTP),
# OAC para os buckets S3 e 2 CloudFront Functions:
#   - spa_fallback  (viewer-request no default): reescreve rotas da SPA p/ /index.html
#   - media_strip   (viewer-request em /media/*): remove o prefixo /media antes de ir ao S3
#
# As origens S3 são privadas (ver módulo storage): só esta distribuição lê, via OAC.

locals {
  spa_origin_id   = "spa-s3"
  media_origin_id = "media-s3"
  api_origin_id   = "api-http"
}

# --- Origin Access Control (OAC) para as origens S3 -----------------------
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.name_prefix}-oac"
  description                       = "OAC para buckets S3 privados (SPA + media)"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# --- CloudFront Functions -------------------------------------------------
resource "aws_cloudfront_function" "spa_fallback" {
  name    = "${var.name_prefix}-spa-fallback"
  runtime = "cloudfront-js-2.0"
  comment = "Reescreve rotas da SPA sem extensao para /index.html"
  publish = true
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      var uri = request.uri;
      // Se nao for arquivo (sem ponto) e nao terminar em barra, serve a SPA.
      if (uri !== '/' && uri.indexOf('.') === -1) {
        request.uri = '/index.html';
      } else if (uri.endsWith('/')) {
        request.uri = '/index.html';
      }
      return request;
    }
  JS
}

resource "aws_cloudfront_function" "media_strip" {
  name    = "${var.name_prefix}-media-strip"
  runtime = "cloudfront-js-2.0"
  comment = "Remove o prefixo /media antes de encaminhar ao bucket de midia"
  publish = true
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      // Remove o primeiro segmento "/media" -> objeto real em links/<uuid>.<ext>
      request.uri = request.uri.replace(/^\/media/, '');
      if (request.uri === '') {
        request.uri = '/';
      }
      return request;
    }
  JS
}

# --- Distribuicao ---------------------------------------------------------
resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  comment             = "${var.name_prefix} — SPA + media + API"
  default_root_object = "index.html"
  price_class         = var.price_class
  is_ipv6_enabled     = true

  # Origem 1: SPA (S3 privado via OAC)
  origin {
    origin_id                = local.spa_origin_id
    domain_name              = var.spa_bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  # Origem 2: media (S3 privado via OAC)
  origin {
    origin_id                = local.media_origin_id
    domain_name              = var.media_bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  # Origem 3: API HTTP (custom origin HTTPS)
  origin {
    origin_id   = local.api_origin_id
    domain_name = var.api_origin_domain_name

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Comportamento default: SPA
  default_cache_behavior {
    target_origin_id       = local.spa_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # CachingOptimized (managed policy well-known id)
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_fallback.arn
    }
  }

  # /api/* -> HTTP API (sem cache, repassa tudo)
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = local.api_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # CachingDisabled (managed policy well-known id)
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    # AllViewerExceptHostHeader (managed origin request policy)
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"
  }

  # /media/* -> bucket de midia (strip do prefixo /media via CloudFront Function)
  ordered_cache_behavior {
    path_pattern           = "${var.media_path_prefix}/*"
    target_origin_id       = local.media_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.media_strip.arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = var.tags
}
