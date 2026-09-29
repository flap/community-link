"""Temas visuais disponíveis (RF-009).

A personalização é limitada a este conjunto de padrões — não é um editor livre.
Cada tema expõe tokens simples que o frontend aplica na página pública.
"""

THEMES: dict[str, dict] = {
    "default": {
        "label": "Padrão (Escuro)",
        "background": "#0f172a",
        "surface": "#1e293b",
        "text": "#f8fafc",
        "accent": "#38bdf8",
    },
    "light": {
        "label": "Claro",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#0f172a",
        "accent": "#2563eb",
    },
    "sunset": {
        "label": "Sunset",
        "background": "#1a1025",
        "surface": "#2d1b3d",
        "text": "#fdf4ff",
        "accent": "#f97316",
    },
    "forest": {
        "label": "Forest",
        "background": "#0b1f16",
        "surface": "#12362a",
        "text": "#ecfdf5",
        "accent": "#34d399",
    },
    "aws": {
        "label": "AWS",
        "background": "#161e2d",
        "surface": "#232f3e",
        "text": "#ffffff",
        "accent": "#ff9900",
    },
}

DEFAULT_THEME = "default"


def theme_exists(name: str) -> bool:
    return name in THEMES
