"""Geração de embeds a partir da URL do link (RF-006).

Aplica regras por provedor para produzir uma URL/HTML de embed quando possível.
Se o provedor não for suportado ou a URL não casar, retorna ``None`` e o
frontend exibe o link como externo (fallback — RN-003).
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from .models import LinkType


def build_embed(link_type: LinkType, url: str) -> dict | None:
    """Retorna um dict de embed ({'kind', 'src'}) ou None se não embeddável."""
    if link_type == LinkType.video:
        return _video_embed(url)
    if link_type == LinkType.meetup:
        # Meetup não expõe iframe estável; tratado como link externo rico.
        return None
    return None


def _video_embed(url: str) -> dict | None:
    yt = _youtube_id(url)
    if yt:
        return {"kind": "youtube", "src": f"https://www.youtube.com/embed/{yt}"}
    vimeo = _vimeo_id(url)
    if vimeo:
        return {"kind": "vimeo", "src": f"https://player.vimeo.com/video/{vimeo}"}
    return None


def _youtube_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtube.com" in host:
        if parsed.path == "/watch":
            vals = parse_qs(parsed.query).get("v")
            return vals[0] if vals else None
        m = re.match(r"^/(embed|shorts)/([\w-]+)", parsed.path)
        if m:
            return m.group(2)
    if "youtu.be" in host:
        return parsed.path.lstrip("/") or None
    return None


def _vimeo_id(url: str) -> str | None:
    parsed = urlparse(url)
    if "vimeo.com" in parsed.netloc.lower():
        m = re.match(r"^/(\d+)", parsed.path)
        if m:
            return m.group(1)
    return None
