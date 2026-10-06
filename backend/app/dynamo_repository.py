"""Implementação do repositório em DynamoDB (single-table design).

Chaves (conforme especificação técnica, seção 5):

* Comunidade:  PK=``COMMUNITY#{slug}``  SK=``METADATA``
* Seção:       PK=``COMMUNITY#{slug}``  SK=``SECTION#{id}``
* Link:        PK=``COMMUNITY#{slug}``  SK=``LINK#{sectionId}#{id}``
"""

from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

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
from .repository import ConflictError, NotFoundError, Repository


def _pk(slug: str) -> str:
    return f"COMMUNITY#{slug}"


def _user_pk(sub: str) -> str:
    return f"USER#{sub}"


class DynamoDBRepository(Repository):
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None) -> None:
        self._resource = boto3.resource(
            "dynamodb", region_name=region, endpoint_url=endpoint_url
        )
        self._table = self._resource.Table(table_name)

    # -- Communities --------------------------------------------------------
    def create_community(self, data: CommunityCreate) -> Community:
        community = Community(**data.model_dump())
        item = {"PK": _pk(community.slug), "SK": "METADATA", **community.model_dump()}
        try:
            self._table.put_item(
                Item=item, ConditionExpression="attribute_not_exists(PK)"
            )
        except ClientError as exc:  # pragma: no cover - depende da AWS
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ConflictError(f"slug '{community.slug}' já em uso") from exc
            raise
        return community

    def get_community(self, slug: str) -> Community | None:
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": "METADATA"})
        item = resp.get("Item")
        if not item:
            return None
        return Community(**_strip_keys(item))

    def list_communities(self) -> list[Community]:
        # Scan simples; para produção com muitos tenants, usar GSI dedicado.
        resp = self._table.scan(
            FilterExpression="SK = :meta",
            ExpressionAttributeValues={":meta": "METADATA"},
        )
        return [Community(**_strip_keys(i)) for i in resp.get("Items", [])]

    def update_community(self, slug: str, data: CommunityUpdate) -> Community:
        current = self.get_community(slug)
        if current is None:
            raise NotFoundError(f"comunidade '{slug}' não encontrada")
        updated = current.model_copy(update=data.model_dump(exclude_unset=True))
        self._table.put_item(
            Item={"PK": _pk(slug), "SK": "METADATA", **updated.model_dump()}
        )
        return updated

    def delete_community(self, slug: str) -> None:
        resp = self._table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": _pk(slug)},
        )
        items = resp.get("Items", [])
        if not items:
            raise NotFoundError(f"comunidade '{slug}' não encontrada")
        with self._table.batch_writer() as batch:
            for i in items:
                batch.delete_item(Key={"PK": i["PK"], "SK": i["SK"]})
                # remove o espelho USER#sub / COMMUNITY#slug dos administradores
                if str(i["SK"]).startswith("ADMIN#"):
                    sub = str(i["SK"]).split("#", 1)[1]
                    batch.delete_item(Key={"PK": _user_pk(sub), "SK": _pk(slug)})

    # -- Sections -----------------------------------------------------------
    def _ensure_community(self, slug: str) -> None:
        if self.get_community(slug) is None:
            raise NotFoundError(f"comunidade '{slug}' não encontrada")

    def create_section(self, slug: str, data: SectionCreate) -> Section:
        self._ensure_community(slug)
        section = Section(**data.model_dump())
        self._table.put_item(
            Item={"PK": _pk(slug), "SK": f"SECTION#{section.id}", **section.model_dump()}
        )
        return section

    def list_sections(self, slug: str) -> list[Section]:
        self._ensure_community(slug)
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": "SECTION#"},
        )
        sections = [Section(**_strip_keys(i)) for i in resp.get("Items", [])]
        return sorted(sections, key=lambda s: (s.order, s.title))

    def update_section(self, slug: str, section_id: str, data: SectionUpdate) -> Section:
        self._ensure_community(slug)
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": f"SECTION#{section_id}"})
        item = resp.get("Item")
        if not item:
            raise NotFoundError(f"seção '{section_id}' não encontrada")
        current = Section(**_strip_keys(item))
        updated = current.model_copy(update=data.model_dump(exclude_unset=True))
        self._table.put_item(
            Item={"PK": _pk(slug), "SK": f"SECTION#{section_id}", **updated.model_dump()}
        )
        return updated

    def delete_section(self, slug: str, section_id: str) -> None:
        self._ensure_community(slug)
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": f"SECTION#{section_id}"})
        if not resp.get("Item"):
            raise NotFoundError(f"seção '{section_id}' não encontrada")
        self._table.delete_item(Key={"PK": _pk(slug), "SK": f"SECTION#{section_id}"})
        # remove links órfãos
        links = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": f"LINK#{section_id}#"},
        )
        with self._table.batch_writer() as batch:
            for i in links.get("Items", []):
                batch.delete_item(Key={"PK": i["PK"], "SK": i["SK"]})

    # -- Links --------------------------------------------------------------
    def create_link(self, slug: str, data: LinkCreate) -> Link:
        self._ensure_community(slug)
        sec = self._table.get_item(
            Key={"PK": _pk(slug), "SK": f"SECTION#{data.section_id}"}
        )
        if not sec.get("Item"):
            raise NotFoundError(f"seção '{data.section_id}' não encontrada")
        link = Link(**data.model_dump())
        self._table.put_item(
            Item={
                "PK": _pk(slug),
                "SK": f"LINK#{link.section_id}#{link.id}",
                **link.model_dump(),
            }
        )
        return link

    def list_links(self, slug: str) -> list[Link]:
        self._ensure_community(slug)
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": "LINK#"},
        )
        links = [Link(**_strip_keys(i)) for i in resp.get("Items", [])]
        return sorted(links, key=lambda link_: (link_.order, link_.created_at))

    def _find_link_sk(self, slug: str, link_id: str) -> str | None:
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": "LINK#"},
        )
        for i in resp.get("Items", []):
            if i["SK"].endswith(f"#{link_id}"):
                return i["SK"]
        return None

    def update_link(self, slug: str, link_id: str, data: LinkUpdate) -> Link:
        self._ensure_community(slug)
        sk = self._find_link_sk(slug, link_id)
        if sk is None:
            raise NotFoundError(f"link '{link_id}' não encontrado")
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": sk})
        current = Link(**_strip_keys(resp["Item"]))
        payload = data.model_dump(exclude_unset=True)
        if "section_id" in payload:
            sec = self._table.get_item(
                Key={"PK": _pk(slug), "SK": f"SECTION#{payload['section_id']}"}
            )
            if not sec.get("Item"):
                raise NotFoundError(f"seção '{payload['section_id']}' não encontrada")
        updated = current.model_copy(update=payload)
        # se a seção mudou, a SK muda: remove a antiga e grava a nova
        new_sk = f"LINK#{updated.section_id}#{updated.id}"
        if new_sk != sk:
            self._table.delete_item(Key={"PK": _pk(slug), "SK": sk})
        self._table.put_item(
            Item={"PK": _pk(slug), "SK": new_sk, **updated.model_dump()}
        )
        return updated

    def delete_link(self, slug: str, link_id: str) -> None:
        self._ensure_community(slug)
        sk = self._find_link_sk(slug, link_id)
        if sk is None:
            raise NotFoundError(f"link '{link_id}' não encontrado")
        self._table.delete_item(Key={"PK": _pk(slug), "SK": sk})

    # -- Reordenação (RF-018) ----------------------------------------------
    def reorder_sections(self, slug: str, ordered_ids: list[str]) -> list[Section]:
        self._ensure_community(slug)
        current = {s.id: s for s in self.list_sections(slug)}
        unknown = [sid for sid in ordered_ids if sid not in current]
        if unknown:
            raise NotFoundError(f"seção(ões) inexistente(s): {', '.join(unknown)}")
        for position, sid in enumerate(ordered_ids):
            updated = current[sid].model_copy(update={"order": position})
            self._table.put_item(
                Item={"PK": _pk(slug), "SK": f"SECTION#{sid}", **updated.model_dump()}
            )
        return self.list_sections(slug)

    def reorder_links(self, slug: str, section_id: str, ordered_ids: list[str]) -> list[Link]:
        self._ensure_community(slug)
        sec = self._table.get_item(Key={"PK": _pk(slug), "SK": f"SECTION#{section_id}"})
        if not sec.get("Item"):
            raise NotFoundError(f"seção '{section_id}' não encontrada")
        current = {link.id: link for link in self.list_links(slug)}
        for lid in ordered_ids:
            link = current.get(lid)
            if link is None:
                raise NotFoundError(f"link '{lid}' não encontrado")
            if link.section_id != section_id:
                raise ConflictError(f"link '{lid}' não pertence à seção '{section_id}'")
        for position, lid in enumerate(ordered_ids):
            updated = current[lid].model_copy(update={"order": position})
            self._table.put_item(
                Item={
                    "PK": _pk(slug),
                    "SK": f"LINK#{section_id}#{lid}",
                    **updated.model_dump(),
                }
            )
        return [link for link in self.list_links(slug) if link.section_id == section_id]

    # -- Administradores e convites (RF-021) --------------------------------
    def add_admin(self, slug: str, sub: str, email: str | None) -> CommunityAdmin:
        self._ensure_community(slug)
        admin = CommunityAdmin(sub=sub, email=email)
        with self._table.batch_writer() as batch:
            batch.put_item(Item={"PK": _pk(slug), "SK": f"ADMIN#{sub}", **admin.model_dump()})
            batch.put_item(Item={"PK": _user_pk(sub), "SK": _pk(slug), "slug": slug})
        return admin

    def remove_admin(self, slug: str, sub: str) -> None:
        self._ensure_community(slug)
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": f"ADMIN#{sub}"})
        if not resp.get("Item"):
            raise NotFoundError(f"administrador '{sub}' não encontrado")
        with self._table.batch_writer() as batch:
            batch.delete_item(Key={"PK": _pk(slug), "SK": f"ADMIN#{sub}"})
            batch.delete_item(Key={"PK": _user_pk(sub), "SK": _pk(slug)})

    def list_admins(self, slug: str) -> list[CommunityAdmin]:
        self._ensure_community(slug)
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": "ADMIN#"},
        )
        admins = [CommunityAdmin(**_strip_keys(i)) for i in resp.get("Items", [])]
        return sorted(admins, key=lambda a: a.added_at)

    def is_admin(self, slug: str, sub: str) -> bool:
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": f"ADMIN#{sub}"})
        return bool(resp.get("Item"))

    def list_user_communities(self, sub: str) -> list[Community]:
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _user_pk(sub), ":s": "COMMUNITY#"},
        )
        communities: list[Community] = []
        for i in resp.get("Items", []):
            community = self.get_community(str(i["slug"]))
            if community is not None:
                communities.append(community)
        return sorted(communities, key=lambda c: c.created_at)

    def add_invite(self, slug: str, email: str, invited_by: str | None) -> AdminInvite:
        self._ensure_community(slug)
        invite = AdminInvite(email=email, invited_by=invited_by)
        self._table.put_item(
            Item={"PK": _pk(slug), "SK": f"INVITE#{invite.email}", **invite.model_dump()}
        )
        return invite

    def list_invites(self, slug: str) -> list[AdminInvite]:
        self._ensure_community(slug)
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": "INVITE#"},
        )
        invites = [AdminInvite(**_strip_keys(i)) for i in resp.get("Items", [])]
        return sorted(invites, key=lambda i: i.invited_at)

    def remove_invite(self, slug: str, email: str) -> None:
        self._ensure_community(slug)
        email = email.strip().lower()
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": f"INVITE#{email}"})
        if not resp.get("Item"):
            raise NotFoundError(f"convite para '{email}' não encontrado")
        self._table.delete_item(Key={"PK": _pk(slug), "SK": f"INVITE#{email}"})

    def has_invite(self, slug: str, email: str) -> bool:
        email = email.strip().lower()
        resp = self._table.get_item(Key={"PK": _pk(slug), "SK": f"INVITE#{email}"})
        return bool(resp.get("Item"))


def _strip_keys(item: dict) -> dict:
    """Remove atributos de chave (PK/SK) antes de hidratar o modelo."""
    return {k: v for k, v in item.items() if k not in ("PK", "SK")}
