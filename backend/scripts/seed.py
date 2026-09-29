"""Popula o repositório com uma comunidade de exemplo (dev).

Uso:
    cd backend && python -m scripts.seed
"""

import os

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")

from app.models import (  # noqa: E402
    CommunityCreate,
    LinkCreate,
    LinkType,
    SectionCreate,
)
from app.repository import get_repository  # noqa: E402


def run() -> None:
    repo = get_repository()
    community = repo.create_community(
        CommunityCreate(
            name="AWS Community Brasil",
            slug="aws-community-br",
            description="Comunidade de builders AWS no Brasil.",
            theme="aws",
        )
    )
    eventos = repo.create_section(community.slug, SectionCreate(title="Eventos", order=0))
    redes = repo.create_section(community.slug, SectionCreate(title="Redes Sociais", order=1))

    repo.create_link(
        community.slug,
        LinkCreate(
            section_id=eventos.id,
            type=LinkType.meetup,
            title="Próximo Meetup",
            url="https://www.meetup.com/",
            emoji="📅",
        ),
    )
    repo.create_link(
        community.slug,
        LinkCreate(
            section_id=redes.id,
            type=LinkType.linkedin,
            title="LinkedIn",
            url="https://www.linkedin.com/",
            emoji="💼",
        ),
    )
    print(f"Seed concluído: comunidade '{community.slug}' criada.")


if __name__ == "__main__":
    run()
