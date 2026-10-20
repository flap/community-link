"""Fonte única de normalização nome→slug e resolução de disponibilidade.

Funções puras (sem dependência de FastAPI ou do repositório) usadas tanto pela
geração da sugestão de slug (RF-001) quanto, de forma consistente, replicadas no
frontend. A validação de slug (``models.validate_slug``) reutiliza as constantes
``SLUG_PATTERN`` e ``RESERVED_SLUGS`` daqui para evitar divergência.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

SLUG_MAX_LENGTH = 60  # espelha CommunityBase.slug max_length
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
# Slugs reservados para rotas/infra; não podem ser usados por comunidades.
RESERVED_SLUGS = frozenset({"api", "admin", "static", "assets", "www"})

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(name: str, *, max_length: int = SLUG_MAX_LENGTH) -> str:
    """Normaliza um texto livre em um slug base URL-safe.

    Passos (ordem fixa, replicada bit a bit pelo frontend):
      1. NFKD + remoção de marcas de acento (unicodedata)
      2. lower()
      3. troca de todo caractere fora de [a-z0-9] por '-'
      4. colapso de hífens repetidos (coberto pelo '+' do passo 3)
      5. strip de hífens nas pontas
      6. truncagem para max_length, com novo strip de hífen à direita

    Retorna string possivelmente vazia (ex.: entrada só com símbolos).
    Garante: resultado vazio OU casa com SLUG_PATTERN.
    """
    nfkd = unicodedata.normalize("NFKD", name or "")
    without_marks = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    lowered = without_marks.lower()
    hyphenated = _NON_ALNUM.sub("-", lowered).strip("-")
    if len(hyphenated) > max_length:
        hyphenated = hyphenated[:max_length].rstrip("-")
    return hyphenated


def resolve_available_slug(
    base: str,
    exists: Callable[[str], bool],
    *,
    max_length: int = SLUG_MAX_LENGTH,
) -> str:
    """Retorna o primeiro slug livre a partir de ``base``.

    - Se ``base`` está livre, retorna ``base``.
    - Senão tenta ``base-2``, ``base-3``, ... (começa em 2, convenção amigável).
    - Respeita ``max_length``: trunca ``base`` para caber o sufixo ``-N``.

    ``exists`` deve reportar colisão (``True`` quando o candidato já está em uso).
    Slugs reservados são tratados como ocupados, de modo que a sugestão nunca
    devolva um slug que a validação rejeitaria por ser reservado.
    """
    if not base:
        return base

    def taken(candidate: str) -> bool:
        return candidate in RESERVED_SLUGS or exists(candidate)

    if not taken(base):
        return base

    n = 2
    while True:
        suffix = f"-{n}"
        trimmed = base
        if len(trimmed) + len(suffix) > max_length:
            trimmed = trimmed[: max_length - len(suffix)].rstrip("-")
        candidate = f"{trimmed}{suffix}"
        if not taken(candidate):
            return candidate
        n += 1
