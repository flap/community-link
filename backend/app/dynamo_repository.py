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
    Community,
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


def _strip_keys(item: dict) -> dict:
    """Remove atributos de chave (PK/SK) antes de hidratar o modelo."""
    return {k: v for k, v in item.items() if k not in ("PK", "SK")}
