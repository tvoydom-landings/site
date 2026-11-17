"""Шаблоны страниц дома. Тема — поле "theme" в data/houses/<код>.json: "" — основная, "samara" — Samara."""
from __future__ import annotations

from . import default, samara
from .common import Mortgage, card

THEMES = {"": default.page, "samara": samara.page}

__all__ = ["THEMES", "Mortgage", "card", "render"]


def render(c: dict, imgs: list[dict], houses: list[dict], draft: bool, common: dict, mortgage: Mortgage) -> str:
    page = THEMES.get(c["theme"])
    if page is None:
        raise SystemExit(f"{c['code']}: неизвестная тема «{c['theme']}» — есть: {', '.join(repr(t) for t in THEMES)}")
    return page(c, imgs, houses, draft, common, mortgage)
