#!/usr/bin/env python3
"""Сборка сайта лендингов: шаблон + данные → готовые страницы.

    python3 build.py --draft            черновик (_site/): полоса «Черновик», жёлтые пометки, закрыт от поисковиков
    python3 build.py                    чистовая — то, что уходит на сервер

Только стандартная библиотека Python 3.10+, без установки пакетов. Результат в _site/:
    shared/                     общие стили, шрифты, калькулятор (+ calc/rates.mjs из data/mortgage.json)
    <код>/index.html, img/      страница дома — адрес постоянный: домен/<код>/ (на него ведут QR-коды)
    _catalog/                   превью домов без своего лендинга (лента «Другие дома в продаже»)
    index.html, robots.txt
Перед записью сборка проверяет страницы (check): только свои файлы и относительные пути.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from template import Mortgage, card, render  # noqa: E402
from template.common import e, rub  # noqa: E402

DATA, PHOTOS, SHARED = ROOT / "data", ROOT / "photos", ROOT / "shared"
RATES_HEADER = "// Создан из data/mortgage.json при сборке сайта — руками не править.\n"



def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise SystemExit(f"{path.relative_to(ROOT)}: ошибка в JSON, строка {err.lineno}: {err.msg}") from None


def houses() -> list[dict]:
    return [load_json(p) for p in sorted((DATA / "houses").glob("*.json"))]


def check(code: str, html: str) -> list[str]:
    problems = []
    if re.search(r'<(script|link)[^>]+(src|href)="https?://', html):
        problems.append(f"{code}: внешний скрипт или стиль — всё своё должно лежать в shared/")
    if re.search(r'(src|href)="/(?!/)', html):
        problems.append(f"{code}: путь от корня домена — нужны относительные (сайт открывается и из подпапки)")
    return problems


def others(d: dict, all_houses: list[dict], catalog: list[dict]) -> list[dict]:
    """«Другие дома в продаже» по возрастанию цены: дом со своим лендингом — ссылка на его страницу,
    без лендинга — на пост в Telegram (data/catalog.json); без ссылки дом не показываем."""
    pages = {h["code"]: h for h in all_houses}
    out = []
    for o in sorted(catalog, key=lambda h: h["price"]):
        if o["code"] == d["code"]:
            continue
        h = pages.get(o["code"])
        if h:
            hero = next((p for p in h.get("photos", []) if p.get("hero")), None)
            href, pic = f"../{o['code']}/", f"../{o['code']}/img/{hero['n']:02d}-s.jpg" if hero else None
        else:
            href, pic = o.get("telegram"), f"../_catalog/{o['code']}.jpg" if o.get("pic") else None
        if href:
            out.append({"href": href, "pic": pic, "price": o["price"], "address": o["address"],
                        "place": o["village"], "area": o["area"]})
    return out


def index_page(all_houses: list[dict], draft: bool) -> str:
    items = "".join(f'<li><a href="{e(h["code"])}/">{e(h.get("address", h["name"]))}, {e(h.get("village", ""))}</a>'
                    f' — {rub(h["price"])} ₽</li>' for h in sorted(all_houses, key=lambda h: h["price"])
                    if h["status"] == "в продаже")
    robots = '<meta name="robots" content="noindex">' if draft else ""
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Дома в продаже</title>{robots}
<style>body{{font:17px/1.6 system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 16px;background:#fff;color:#111}}
a{{color:#b20710}}</style></head>
<body><h1>Дома в продаже</h1><ul>{items or "<li>Сейчас нет домов в продаже</li>"}</ul></body></html>
"""


def build(out: Path, draft: bool) -> list[str]:
    common = load_json(DATA / "common.json")
    program = load_json(DATA / "mortgage.json")
    mortgage = Mortgage(program)
    all_houses = houses()
    catalog = load_json(DATA / "catalog.json") if (DATA / "catalog.json").exists() else []
    pages, problems = {}, []
    for d in all_houses:
        c = card(d)
        html = render(c, d.get("photos", []), others(d, all_houses, catalog), draft, common, mortgage)
        problems += check(d["code"], html)
        if not (PHOTOS / d["code"]).is_dir() and d.get("photos"):
            problems.append(f"{d['code']}: нет папки photos/{d['code']}/")
        pages[d["code"]] = html
    if problems:
        return problems
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SHARED, out / "shared")
    (out / "shared/calc/rates.mjs").write_text(
        RATES_HEADER + f"export const PROGRAM = {json.dumps(program, ensure_ascii=False, indent=2)};\n", encoding="utf-8")
    if (PHOTOS / "_catalog").is_dir():
        shutil.copytree(PHOTOS / "_catalog", out / "_catalog")
    for code, html in pages.items():
        if (PHOTOS / code).is_dir():
            shutil.copytree(PHOTOS / code, out / code / "img")
        (out / code).mkdir(parents=True, exist_ok=True)
        (out / code / "index.html").write_text(html, encoding="utf-8")
    (out / "index.html").write_text(index_page(all_houses, draft), encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\n" + ("Disallow: /\n" if draft else "Allow: /\n"), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draft", action="store_true", help="черновик: пометки и noindex")
    ap.add_argument("--out", default="_site", help="куда собрать (по умолчанию _site)")
    a = ap.parse_args()
    out = (ROOT / a.out).resolve()
    problems = build(out, a.draft)
    if problems:
        sys.exit("Сборка остановлена:\n- " + "\n- ".join(problems))
    print(f"{'черновик' if a.draft else 'чистовая'}: {len(houses())} дом(а) → {out}")


if __name__ == "__main__":
    main()
