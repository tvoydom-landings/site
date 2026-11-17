"""Общее для шаблонов: экранирование, рубли, пометки черновика, тексты ипотеки из data/mortgage.json,
дом из data/houses/<код>.json в том виде, в каком его ждут шаблоны."""
from __future__ import annotations

import html

e = html.escape


def rub(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def num_text(x: float) -> str:
    """20.1 → «20,1», 10.0 → «10»."""
    return f"{x:g}".replace(".", ",")


def years(n: int) -> str:
    word = "год" if n % 10 == 1 and n % 100 != 11 else "года" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "лет"
    return f"{n} {word}"


def need(text: str, draft: bool) -> str:
    """Жёлтая пометка «чего не хватает» — только в черновике."""
    return f'<p class="need">Нужно: {e(text)}</p>' if draft else ""


# ---------------------------------------------------------------- ипотека: тексты из data/mortgage.json

class Mortgage:
    """Цифры семейной ипотеки для текстов страницы. Сам расчёт — в shared/calc/mortgage.mjs по тем же данным."""

    def __init__(self, m: dict):
        self.m = m
        rates = list(m["rateByChildrenPercent"].values())
        self.max_kids = len(rates)
        self.rate_range = f"от {num_text(min(rates))} до {num_text(max(rates))} %"
        self.subsidy_years = m["subsidyYears"]
        self.special = num_text(m["specialRatePercent"])
        share = m["specialFromDownPercent"]
        self.special_down = "от половины цены" if share == 50 else f"от {num_text(share)} % цены"
        self.min_down = num_text(m["minDownPercent"])

    def kids_buttons(self) -> str:
        return "".join(f'<button type="button" data-kids="{k}" aria-pressed="false">'
                       f'{f"{k}+" if k == self.max_kids else k}</button>' for k in range(1, self.max_kids + 1))

    def special_note(self) -> str:
        return (f"Ставка не выше {self.special} % при любом числе детей — если взнос {self.special_down} "
                "(маткапитал и сертификаты засчитываются) или в семье ребёнок с инвалидностью.")

    def subsidy_note(self) -> str:
        return (f"Расчёт предварительный и не является офертой. Семейная ипотека: ставка субсидируется "
                f"{years(self.subsidy_years)}, затем растёт на {num_text(self.m['rateStepPercent'])} п.п. "
                "Окончательные условия определяет банк.")

    def after_head(self) -> str:
        return f"После {years(self.subsidy_years)}"


# ---------------------------------------------------------------- дом

AREAS = (("total", "Общая площадь"), ("first_floor", "Первый этаж"), ("attic", "Мансарда"), ("plot", "Участок"))


def card(d: dict) -> dict:
    """data/houses/<код>.json → словарь для шаблонов (ключи — как в карточке объекта)."""
    post = {"Посёлок": d.get("village", ""), "Адрес": d.get("address", ""), "Тип": d.get("type", ""),
            "Отделка": d.get("finishing", "")}
    post.update({label: d.get("areas", {}).get(key, "") for key, label in AREAS})
    return {
        "name": d["name"], "code": d["code"], "status": d["status"], "price": d["price"], "updated": d.get("updated", ""),
        "post": {k: v for k, v in post.items() if v}, "utilities": d.get("utilities", []),
        "kn": [(k["label"], k["number"]) for k in d.get("cadastral", [])],
        "finish": d.get("finish", []), "layout": d.get("layout", []),
        "about": {a["title"]: a["text"] for a in d.get("about", [])},
        "rooms": d.get("rooms", []), "nearby": d.get("nearby", []),
        "included": d.get("included", []), "included_finish": d.get("included_finish", []),
        "brand": d.get("brand", ""), "phone": d.get("phone", ""), "theme": d.get("theme", ""),
        "project": d.get("project", ""), "map": d.get("map", ""),
        "location": d.get("location") or {"name": "", "distances": [], "text": []},
        "telegram": d.get("telegram"),
    }
