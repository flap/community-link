terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      # Dois providers aliasados (Opção A — cross-account DNS):
      #   aws     → conta do app (390686807269): certificado ACM em us-east-1,
      #             para o CloudFront usar via SNI.
      #   aws.dns → conta de DNS (070008302080): registros CNAME de validação,
      #             pois a hosted zone awscommunity.com.br vive lá.
      configuration_aliases = [aws, aws.dns]
    }
  }
}
