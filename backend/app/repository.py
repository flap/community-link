"""Camada de persistência do Community Link.

Fornece uma abstração de repositório com duas implementações:

* ``InMemoryRepository`` — armazenamento em memória (dev/testes).
* ``DynamoDBRepository`` — single-table design em DynamoDB (produção).

O modelo de dados segue o descrito na especificação técnica (seção 5):

* Comunidade:  PK=``COMMUNITY#{slug}``  SK=``METADATA``
* Seção:       PK=``COMMUNITY#{slug}``  SK=``SECTION#{id}``
* Link:        PK=``COMMUNITY#{slug}``  SK=``LINK#{sectionId}#{id}``
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod

from .models import (
    AdminInvite,
    Community,
    CommunityAdmin,
    CommunityCreate,
    CommunityUpdate,
    Link,
    LinkCreate,
    LinkUpdate,
    Section,
    SectionCreate,
    SectionUpdate,
)


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class Repository(ABC):
    # Communities
    @abstractmethod
    def create_community(self, data: CommunityCreate) -> Community: ...

    @abstractmethod
    def get_community(self, slug: str) -> Community | None: ...

    @abstractmethod
    def list_communities(self) -> list[Community]: ...

    @abstractmethod
    def update_community(self, slug: str, data: CommunityUpdate) -> Community: ...

    @abstractmethod
    def delete_community(self, slug: str) -> None: ...

    # Sections
    @abstractmethod
    def create_section(self, slug: str, data: SectionCreate) -> Section: ...

    @abstractmethod
    def list_sections(self, slug: str) -> list[Section]: ...

    @abstractmethod
    def update_section(self, slug: str, section_id: str, data: SectionUpdate) -> Section: ...

    @abstractmethod
    def delete_section(self, slug: str, section_id: str) -> None: ...

    # Links
    @abstractmethod
    def create_link(self, slug: str, data: LinkCreate) -> Link: ...

    @abstractmethod
    def list_links(self, slug: str) -> list[Link]: ...

    @abstractmethod
    def update_link(self, slug: str, link_id: str, data: LinkUpdate) -> Link: ...

    @abstractmethod
    def delete_link(self, slug: str, link_id: str) -> None: ...

    # Reordenação (RF-018)
    @abstractmethod
    def reorder_sections(self, slug: str, ordered_ids: list[str]) -> list[Section]: ...

    @abstractmethod
    def reorder_links(self, slug: str, section_id: str, ordered_ids: list[str]) -> list[Link]: ...

    # Administradores e convites (RF-021)
    @abstractmethod
    def add_admin(self, slug: str, sub: str, email: str | None) -> CommunityAdmin: ...

    @abstractmethod
    def remove_admin(self, slug: str, sub: str) -> None: ...

    @abstractmethod
    def list_admins(self, slug: str) -> list[CommunityAdmin]: ...

    @abstractmethod
    def is_admin(self, slug: str, sub: str) -> bool: ...

    @abstractmethod
    def list_user_communities(self, sub: str) -> list[Community]: ...

    @abstractmethod
    def add_invite(self, slug: str, email: str, invited_by: str | None) -> AdminInvite: ...

    @abstractmethod
    def list_invites(self, slug: str) -> list[AdminInvite]: ...

    @abstractmethod
    def remove_invite(self, slug: str, email: str) -> None: ...

    @abstractmethod
    def has_invite(self, slug: str, email: str) -> bool: ...


class InMemoryRepository(Repository):
    """Implementação em memória, thread-safe, para desenvolvimento e testes."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._communities: dict[str, Community] = {}
        self._sections: dict[str, dict[str, Section]] = {}
        self._links: dict[str, dict[str, Link]] = {}
        # RF-021: admins por comunidade (slug -> sub -> admin) e convites (slug -> email -> convite)
        self._admins: dict[str, dict[str, CommunityAdmin]] = {}
        self._invites: dict[str, dict[str, AdminInvite]] = {}

    # -- Communities --------------------------------------------------------
    def create_community(self, data: CommunityCreate) -> Community:
        with self._lock:
            if data.slug in self._communities:
                raise ConflictError(f"slug '{data.slug}' já em uso")
            community = Community(**data.model_dump())
            self._communities[community.slug] = community
            self._sections[community.slug] = {}
            self._links[community.slug] = {}
            self._admins[community.slug] = {}
            self._invites[community.slug] = {}
            return community

    def get_community(self, slug: str) -> Community | None:
        return self._communities.get(slug)

    def list_communities(self) -> list[Community]:
        return sorted(self._communities.values(), key=lambda c: c.created_at)

    def update_community(self, slug: str, data: CommunityUpdate) -> Community:
        with self._lock:
            community = self._communities.get(slug)
            if community is None:
                raise NotFoundError(f"comunidade '{slug}' não encontrada")
            updated = community.model_copy(
                update={k: v for k, v in data.model_dump(exclude_unset=True).items()}
            )
            self._communities[slug] = updated
            return updated

    def delete_community(self, slug: str) -> None:
        with self._lock:
            if slug not in self._communities:
                raise NotFoundError(f"comunidade '{slug}' não encontrada")
            self._communities.pop(slug, None)
            self._sections.pop(slug, None)
            self._links.pop(slug, None)
            self._admins.pop(slug, None)
            self._invites.pop(slug, None)

    # -- Sections -----------------------------------------------------------
    def _ensure_community(self, slug: str) -> None:
        if slug not in self._communities:
            raise NotFoundError(f"comunidade '{slug}' não encontrada")

    def create_section(self, slug: str, data: SectionCreate) -> Section:
        with self._lock:
            self._ensure_community(slug)
            section = Section(**data.model_dump())
            self._sections[slug][section.id] = section
            return section

    def list_sections(self, slug: str) -> list[Section]:
        self._ensure_community(slug)
        return sorted(self._sections[slug].values(), key=lambda s: (s.order, s.title))

    def update_section(self, slug: str, section_id: str, data: SectionUpdate) -> Section:
        with self._lock:
            self._ensure_community(slug)
            section = self._sections[slug].get(section_id)
            if section is None:
                raise NotFoundError(f"seção '{section_id}' não encontrada")
            updated = section.model_copy(
                update={k: v for k, v in data.model_dump(exclude_unset=True).items()}
            )
            self._sections[slug][section_id] = updated
            return updated

    def delete_section(self, slug: str, section_id: str) -> None:
        with self._lock:
            self._ensure_community(slug)
            if section_id not in self._sections[slug]:
                raise NotFoundError(f"seção '{section_id}' não encontrada")
            self._sections[slug].pop(section_id, None)
            # remove links órfãos da seção
            orphans = [
                lid for lid, link in self._links[slug].items()
                if link.section_id == section_id
            ]
            for lid in orphans:
                self._links[slug].pop(lid, None)

    # -- Links --------------------------------------------------------------
    def create_link(self, slug: str, data: LinkCreate) -> Link:
        with self._lock:
            self._ensure_community(slug)
            if data.section_id not in self._sections[slug]:
                raise NotFoundError(f"seção '{data.section_id}' não encontrada")
            link = Link(**data.model_dump())
            self._links[slug][link.id] = link
            return link

    def list_links(self, slug: str) -> list[Link]:
        self._ensure_community(slug)
        return sorted(self._links[slug].values(), key=lambda link_: (link_.order, link_.created_at))

    def update_link(self, slug: str, link_id: str, data: LinkUpdate) -> Link:
        with self._lock:
            self._ensure_community(slug)
            link = self._links[slug].get(link_id)
            if link is None:
                raise NotFoundError(f"link '{link_id}' não encontrado")
            payload = data.model_dump(exclude_unset=True)
            if "section_id" in payload and payload["section_id"] not in self._sections[slug]:
                raise NotFoundError(f"seção '{payload['section_id']}' não encontrada")
            updated = link.model_copy(update=payload)
            self._links[slug][link_id] = updated
            return updated

    def delete_link(self, slug: str, link_id: str) -> None:
        with self._lock:
            self._ensure_community(slug)
            if link_id not in self._links[slug]:
                raise NotFoundError(f"link '{link_id}' não encontrado")
            self._links[slug].pop(link_id, None)

    # -- Reordenação (RF-018) ----------------------------------------------
    def reorder_sections(self, slug: str, ordered_ids: list[str]) -> list[Section]:
        with self._lock:
            self._ensure_community(slug)
            existing = self._sections[slug]
            unknown = [sid for sid in ordered_ids if sid not in existing]
            if unknown:
                raise NotFoundError(f"seção(ões) inexistente(s): {', '.join(unknown)}")
            for position, sid in enumerate(ordered_ids):
                existing[sid] = existing[sid].model_copy(update={"order": position})
            return self.list_sections(slug)

    def reorder_links(self, slug: str, section_id: str, ordered_ids: list[str]) -> list[Link]:
        with self._lock:
            self._ensure_community(slug)
            if section_id not in self._sections[slug]:
                raise NotFoundError(f"seção '{section_id}' não encontrada")
            links = self._links[slug]
            for lid in ordered_ids:
                link = links.get(lid)
                if link is None:
                    raise NotFoundError(f"link '{lid}' não encontrado")
                if link.section_id != section_id:
                    raise ConflictError(
                        f"link '{lid}' não pertence à seção '{section_id}'"
                    )
            for position, lid in enumerate(ordered_ids):
                links[lid] = links[lid].model_copy(update={"order": position})
            return [link for link in self.list_links(slug) if link.section_id == section_id]

    # -- Administradores e convites (RF-021) --------------------------------
    def add_admin(self, slug: str, sub: str, email: str | None) -> CommunityAdmin:
        with self._lock:
            self._ensure_community(slug)
            admin = CommunityAdmin(sub=sub, email=email)
            self._admins[slug][sub] = admin
            return admin

    def remove_admin(self, slug: str, sub: str) -> None:
        with self._lock:
            self._ensure_community(slug)
            if sub not in self._admins[slug]:
                raise NotFoundError(f"administrador '{sub}' não encontrado")
            self._admins[slug].pop(sub, None)

    def list_admins(self, slug: str) -> list[CommunityAdmin]:
        self._ensure_community(slug)
        return sorted(self._admins[slug].values(), key=lambda a: a.added_at)

    def is_admin(self, slug: str, sub: str) -> bool:
        return sub in self._admins.get(slug, {})

    def list_user_communities(self, sub: str) -> list[Community]:
        slugs = [s for s, admins in self._admins.items() if sub in admins]
        return sorted(
            (self._communities[s] for s in slugs if s in self._communities),
            key=lambda c: c.created_at,
        )

    def add_invite(self, slug: str, email: str, invited_by: str | None) -> AdminInvite:
        with self._lock:
            self._ensure_community(slug)
            invite = AdminInvite(email=email, invited_by=invited_by)
            self._invites[slug][invite.email] = invite
            return invite

    def list_invites(self, slug: str) -> list[AdminInvite]:
        self._ensure_community(slug)
        return sorted(self._invites[slug].values(), key=lambda i: i.invited_at)

    def remove_invite(self, slug: str, email: str) -> None:
        with self._lock:
            self._ensure_community(slug)
            email = email.strip().lower()
            if email not in self._invites[slug]:
                raise NotFoundError(f"convite para '{email}' não encontrado")
            self._invites[slug].pop(email, None)

    def has_invite(self, slug: str, email: str) -> bool:
        return email.strip().lower() in self._invites.get(slug, {})


_repository: Repository | None = None


def get_repository() -> Repository:
    """Retorna o repositório configurado (singleton)."""
    global _repository
    if _repository is not None:
        return _repository

    from .config import get_settings

    settings = get_settings()
    if settings.use_in_memory_store:
        _repository = InMemoryRepository()
    else:
        from .dynamo_repository import DynamoDBRepository

        _repository = DynamoDBRepository(
            table_name=settings.dynamodb_table,
            region=settings.aws_region,
            endpoint_url=settings.dynamodb_endpoint_url,
        )
    return _repository
