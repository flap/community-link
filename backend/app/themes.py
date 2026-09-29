"""Temas visuais disponíveis (RF-009).

A personalização é limitada a este conjunto de padrões — não é um editor livre.
Cada tema expõe tokens simples que o frontend aplica na página pública.
"""

THEMES: dict[str, dict] = {
    "aws": {
        "label": "AWS Community Day",
        "background": "#0f1729",
        "surface": "#1d283a",
        "text": "#ffffff",
        "muted": "#94a3b8",
        "accent": "#ff8800",
    },
    "default": {
        "label": "Padrão (Escuro)",
        "background": "#0f172a",
        "surface": "#1e293b",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
    },
    "light": {
        "label": "Claro",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#0f172a",
        "muted": "#64748b",
        "accent": "#2563eb",
    },
    "sunset": {
        "label": "Sunset",
        "background": "#1a1025",
        "surface": "#2d1b3d",
        "text": "#fdf4ff",
        "muted": "#c4b5d4",
        "accent": "#f97316",
    },
    "forest": {
        "label": "Forest",
        "background": "#0b1f16",
        "surface": "#12362a",
        "text": "#ecfdf5",
        "muted": "#9fc7b4",
        "accent": "#34d399",
    },
}

DEFAULT_THEME = "aws"


def theme_exists(name: str) -> bool:
    return name in THEMES
