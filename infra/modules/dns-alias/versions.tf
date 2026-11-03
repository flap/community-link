terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      # Opção A — cross-account DNS: os registros ALIAS vivem na conta de DNS
      # (070008302080), onde está a hosted zone awscommunity.com.br. O módulo é
      # instanciado com providers = { aws = aws.dns }.
      configuration_aliases = [aws]
    }
  }
}
