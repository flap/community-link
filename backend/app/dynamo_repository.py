"""Implementação do repositório em DynamoDB (single-table design).

Chaves (conforme especificação técnica, seção 5):

* Comunidade:  PK=``COMMUNITY#{slug}``  SK=``METADATA``
* Seção:       PK=``COMMUNITY#{slug}``  SK=``SECTION#{id}``
* Link:        PK=``COMMUNITY#{slug}``  SK=``LINK#{sectionId}#{id}``
"""

from __future__ import annotations

import base64
import json

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .models import (
    AdminInvite,
    Community,
    CommunityAdmin,
    CommunityCreate,
    CommunityUpdate,
    Link,
    LinkCreate,
    LinkType,
    LinkUpdate,
    SearchResult,
    Section,
    SectionCreate,
    SectionUpdate,
)
from .repository import (
    DEFAULT_SEARCH_LIMIT,
    ConflictError,
    NotFoundError,
    Repository,
    SearchPage,
    _author_key,
    _clamp_limit,
    _date_to_upper,
    _matches_filters,
    _matches_q,
)


def _pk(slug: str) -> str:
    return f"COMMUNITY#{slug}"


def _user_pk(sub: str) -> str:
    return f"USER#{sub}"


# Atributos de chave e de índice removidos antes de hidratar o modelo Link.
_INDEX_ATTRS = ("GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK")


def _link_index_attrs(link: Link) -> dict:
    """Atributos de GSI de um Link (RF-012/RF-013 — Fase 2b).

    * GSI1 (por tipo): sempre presente (``type`` é obrigatório no Link).
    * GSI2 (por autor): *sparse* — presente SOMENTE quando há autor, para que
      links sem autor não apareçam no índice de autores.

    Convenção do sort key: ``{created_at}#{id}`` — ``created_at`` é ISO-8601
    (ordenável lexicograficamente = cronologicamente) e ``#{id}`` garante SK
    único e paginação estável quando dois links compartilham timestamp.
    """
    attrs = {
        "GSI1PK": f"TYPE#{link.type.value}",
        "GSI1SK": f"{link.created_at}#{link.id}",
    }
    author_key = _author_key(link.author)
    if author_key is not None:
        attrs["GSI2PK"] = f"AUTHOR#{author_key}"
        attrs["GSI2SK"] = f"{link.created_at}#{link.id}"
    return attrs


def _encode_cursor(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_cursor(cursor: str | None) -> dict:
    if not cursor:
        return {}
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:  # noqa: BLE001 - cursor opaco inválido => início
        return {}


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
                **_link_index_attrs(link),
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
        # put_item reescreve o item inteiro: se o author foi removido, os
        # atributos GSI2* simplesmente deixam de ser gravados (sem órfãos).
        self._table.put_item(
            Item={
                "PK": _pk(slug),
                "SK": new_sk,
                **updated.model_dump(),
                **_link_index_attrs(updated),
            }
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
                    **_link_index_attrs(updated),
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

    # -- Busca e filtros (RF-012 / RF-013 — Fase 2b) ------------------------
    def _result_from_item(self, item: dict, name_cache: dict[str, str]) -> SearchResult:
        slug = str(item["PK"]).split("#", 1)[1]
        link = Link(**_strip_keys(item))
        return SearchResult(
            community_slug=slug,
            community_name=self._community_name(slug, name_cache),
            section_id=link.section_id,
            link=link,
        )

    def _community_name(self, slug: str, name_cache: dict[str, str]) -> str:
        """Nome da comunidade com cache por request (evita N lookups)."""
        if slug in name_cache:
            return name_cache[slug]
        community = self.get_community(slug)
        name = community.name if community is not None else slug
        name_cache[slug] = name
        return name

    def query_by_type(
        self,
        type: LinkType,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Query no GSI1 (por tipo), com range opcional em created_at (desc)."""
        cond = Key("GSI1PK").eq(f"TYPE#{type.value}")
        cond = _apply_date_range(cond, "GSI1SK", date_from, date_to)
        return self._query_all(IndexName="GSI1", KeyConditionExpression=cond)

    def query_by_author(
        self,
        author: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Query no GSI2 (por autor normalizado), range opcional (desc)."""
        author_key = _author_key(author)
        if author_key is None:
            return []
        cond = Key("GSI2PK").eq(f"AUTHOR#{author_key}")
        cond = _apply_date_range(cond, "GSI2SK", date_from, date_to)
        return self._query_all(IndexName="GSI2", KeyConditionExpression=cond)

    def _query_all(self, **kwargs) -> list[dict]:
        """Query paginada (segue LastEvaluatedKey), sempre desc (mais recente)."""
        items: list[dict] = []
        start_key = None
        while True:
            params = dict(kwargs, ScanIndexForward=False)
            if start_key is not None:
                params["ExclusiveStartKey"] = start_key
            resp = self._table.query(**params)
            items.extend(resp.get("Items", []))
            start_key = resp.get("LastEvaluatedKey")
            if not start_key:
                break
        return items

    def _paginate(
        self, results: list[SearchResult], limit: int, cursor: str | None
    ) -> SearchPage:
        """Materializa em memória e pagina por offset (cursor opaco).

        Decisão de design (seção 2.5/7.2): para a busca global sem partição
        natural, materializar + paginar por offset é simples e barato no
        volume atual. Mesmo contrato externo que o restante.
        """
        offset = int(_decode_cursor(cursor).get("offset", 0) or 0)
        page = results[offset : offset + limit]
        next_cursor = (
            _encode_cursor({"offset": offset + limit})
            if offset + limit < len(results)
            else None
        )
        return SearchPage(items=page, next_cursor=next_cursor)

    def search_links_in_community(
        self,
        slug: str,
        *,
        q: str | None = None,
        type: LinkType | None = None,
        author: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        cursor: str | None = None,
    ) -> SearchPage:
        self._ensure_community(slug)
        limit = _clamp_limit(limit)
        # Escopo por comunidade: 1 query na tabela base + filtros em memória
        # (uma comunidade tem poucos links — mais simples/barato que GSI).
        resp = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :s)",
            ExpressionAttributeValues={":pk": _pk(slug), ":s": "LINK#"},
        )
        name_cache: dict[str, str] = {}
        results = [
            self._result_from_item(i, name_cache)
            for i in resp.get("Items", [])
        ]
        results = [
            r
            for r in results
            if _matches_filters(
                r.link, type=type, author=author, date_from=date_from, date_to=date_to
            )
            and _matches_q(r.link, q)
        ]
        results.sort(key=lambda r: (r.link.created_at, r.link.id), reverse=True)
        return self._paginate(results, limit, cursor)

    def search_links_global(
        self,
        *,
        q: str | None = None,
        type: LinkType | None = None,
        author: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        cursor: str | None = None,
    ) -> SearchPage:
        limit = _clamp_limit(limit)
        name_cache: dict[str, str] = {}

        # Dispatch (seção 3.4): type -> GSI1; author (sem type) -> GSI2;
        # nenhum dos dois -> fan-out por tipo (9 LinkType) + merge.
        if type is not None:
            items = self.query_by_type(type, date_from=date_from, date_to=date_to)
        elif author is not None:
            items = self.query_by_author(author, date_from=date_from, date_to=date_to)
        else:
            items = []
            for lt in LinkType:
                items.extend(
                    self.query_by_type(lt, date_from=date_from, date_to=date_to)
                )

        results = [self._result_from_item(i, name_cache) for i in items]
        # Filtros residuais em memória (author quando veio via GSI1; q sempre;
        # type quando veio via GSI2). community_name entra no match de q.
        results = [
            r
            for r in results
            if _matches_filters(
                r.link, type=type, author=author, date_from=date_from, date_to=date_to
            )
            and _matches_q(r.link, q, community_name=r.community_name)
        ]
        results.sort(key=lambda r: (r.link.created_at, r.link.id), reverse=True)
        return self._paginate(results, limit, cursor)


def _apply_date_range(cond, sk_name: str, date_from: str | None, date_to: str | None):
    """Acrescenta ao KeyCondition um range em created_at via o sort key composto.

    O SK é ``{created_at}#{id}``. Para capturar todos os ids de um ``to`` usamos
    o sufixo ``\uffff`` (``:to = to + "\uffff"``), garantindo limite superior
    inclusivo mesmo no SK composto.
    """
    key = Key(sk_name)
    if date_from is not None and date_to is not None:
        return cond & key.between(date_from, _date_to_upper(date_to))
    if date_from is not None:
        return cond & key.gte(date_from)
    if date_to is not None:
        return cond & key.lte(_date_to_upper(date_to))
    return cond


def _strip_keys(item: dict) -> dict:
    """Remove atributos de chave (PK/SK) e de índice (GSI*) antes de hidratar."""
    skip = ("PK", "SK", *_INDEX_ATTRS)
    return {k: v for k, v in item.items() if k not in skip}
