"""Configuração da aplicação via variáveis de ambiente.

No MVP (Fase 1) a autenticação administrativa usa uma credencial fixa
(``ADMIN_TOKEN``) — solução temporária para testes, a ser substituída por
um mecanismo de autenticação completo em iteração futura.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CL_", env_file=".env", extra="ignore")

    # Identidade da aplicação
    app_name: str = "Community Link"
    public_domain: str = "awscommunity.com.br"

    # Autenticação simplificada (MVP): credencial fixa no backend
    admin_token: str = "dev-admin-token-change-me"

    # DynamoDB
    dynamodb_table: str = "community-link"
    aws_region: str = "us-east-1"
    # Endpoint local opcional (ex.: DynamoDB Local em http://localhost:8000)
    dynamodb_endpoint_url: str | None = None
    # Usa um repositório em memória em vez do DynamoDB (útil para dev/testes)
    use_in_memory_store: bool = True

    # S3 (fotos de destaque / logos)
    s3_bucket: str | None = None
    # Prefixo público para servir imagens (em dev, servidas pela própria API)
    media_base_url: str = "/api/media"
    # Diretório local de uploads (usado quando não há bucket S3 configurado)
    media_dir: str = "./media"
    # Limite de upload (5 MB) e formatos aceitos (RN-005)
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    # CORS
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
