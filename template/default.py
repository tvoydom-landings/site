"""Основная тема лендинга (тёмная, «как Netflix»): дизайн-система Продажника.

Страница дома: data/houses/<код>.json → <код>/index.html. Общие стили — shared/default/, калькулятор и
просмотр фото — shared/landing.js, цифры ипотеки — data/mortgage.json, общие условия — data/common.json.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import quote

from .common import Mortgage, e, need, rub


def hero(c: dict, img: dict | None, base: str, M: Mortgage) -> str:
    p = c["post"]
    place = " · ".join(x for x in (p.get("Посёлок", ""), "Северский район") if x)
    bg = (f'<img class="hero-img" src="{base}/img/{img["n"]:02d}.jpg" alt="Фасад: {e(p.get("Адрес", ""))}" '
          f'fetchpriority="high">' if img else "")
    status = {"в продаже": "В продаже", "задаток": "Задаток", "продан": "Продан"}.get(c["status"], c["status"])
    badges = [f'<span class="badge badge-sale">{e(status)}</span>'] if status else []
    badges += [f'<span class="badge">{e(x)}</span>' for x in (p.get("Отделка"), p.get("Тип")) if x]
    show = '<a class="btn btn-dark" href="#contacts">Записаться на показ</a>'
    return f"""<section class="hero">{bg}<div class="wrap">
<p class="hero-place">{e(place)}</p>
<h1>{e(p.get("Адрес", c["name"]))}</h1>
<div class="badges">{"".join(badges)}</div>
<p class="price">{rub(c["price"])} ₽</p>
<p class="price-note">Семейная ипотека · ставка {M.rate_range} — зависит от числа детей</p>
<div class="hero-actions"><a class="btn btn-red" href="#calc">Рассчитать платёж для вашей семьи</a>{show}</div>
</div></section>"""


def facts(c: dict) -> str:
    p = c["post"]
    tiles = [(p.get(k), label) for k, label in (("Общая площадь", "общая площадь"), ("Первый этаж", "первый этаж"),
                                                ("Мансарда", "мансарда"), ("Участок", "участок"))]
    tiles_html = "".join(f'<div class="tile"><b>{e(v)}</b><span>{e(label)}</span></div>' for v, label in tiles if v)
    util = "".join(f"<li>{e(u)}</li>" for u in c["utilities"])
    return f"""<section><div class="wrap"><h2>Коротко о доме</h2>
<div class="tiles">{tiles_html}</div><ul class="utilities">{util}</ul></div></section>"""


def plans(c: dict, imgs: list[dict], base: str, draft: bool) -> str:
    figs = "".join(f'<figure><img src="{base}/img/{i["n"]:02d}.jpg" alt="Планировка" loading="lazy" '
                   f'width="{i["w"]}" height="{i["h"]}"><figcaption>{e(i["what"])}'
                   + (f' · <a href="{base}/img/{i["pdf"]}" download>скачать PDF</a>' if i["pdf"] else "")
                   + "</figcaption></figure>" for i in imgs if i["kind"] == "plan")
    rooms = "".join(f"<li>{e(r)}</li>" for r in c["layout"])
    body = f'<div class="plans">{figs}</div>' if figs else need("планировка — прислать в @SK_images_bot", draft)
    return f"""<section id="plan"><div class="wrap"><h2>Планировка</h2>{body}
<ul class="rooms">{rooms}</ul></div></section>"""


def calc(c: dict, M: Mortgage) -> str:
    kids = M.kids_buttons()
    return f"""<section id="calc"><div class="wrap"><div class="calc" data-price="{c["price"]}">
<h2>Сколько будет платёж</h2>
<p class="calc-lead">Семейная ипотека: ставка и сумма кредита зависят от числа детей. Выберите свой вариант.</p>
<div class="calc-grid"><div>
<div class="field"><span class="label">Детей в семье</span><div class="kids" role="group" aria-label="Детей в семье">{kids}</div></div>
<div class="field"><label class="check"><input type="checkbox" id="disabled"> В семье есть ребёнок с инвалидностью</label></div>
<div class="field" id="f-down"><label for="down">Первоначальный взнос</label>
<div class="money"><input id="down" inputmode="numeric" autocomplete="off"><span class="unit">₽</span></div>
<input type="range" id="down-range" aria-label="Первоначальный взнос"><p class="hint" id="down-hint"></p></div>
<div class="field" id="f-loan"><label for="loan">Сумма кредита</label>
<div class="money"><input id="loan" inputmode="numeric" autocomplete="off"><span class="unit">₽</span></div>
<p class="hint" id="loan-hint"></p></div>
<div class="field"><label for="term">Срок: <span id="term-label"></span></label>
<input type="range" id="term" min="12" step="12" aria-label="Срок кредита"></div>
</div>
<div class="result" aria-live="polite">
<p class="result-label">Ежемесячный платёж</p>
<p class="result-pay"><span id="pay">—</span> <small>₽/мес.</small></p>
<p class="muted" id="pay-sub"></p>
<ul class="result-lines"><li><span>Ставка</span><span id="r-rate"></span></li><li><span>Взнос</span><span id="r-down"></span></li>
<li><span>Кредит</span><span id="r-loan"></span></li><li><span>Срок</span><span id="r-term"></span></li></ul>
<p class="after15" id="after15" hidden></p><p class="special" id="special" hidden></p>
</div></div>
<p class="table-title">Для вашей семьи — платёж при минимальном взносе</p>
<div class="table-wrap"><table class="kids-table">
<thead><tr><th>Детей</th><th>Ставка</th><th class="wide">Кредит до</th><th>Взнос от</th><th>Платёж</th><th class="wide">{M.after_head()}</th></tr></thead>
<tbody id="kids-rows"></tbody></table></div>
<p class="calc-note">{M.special_note()}</p>
<p class="calc-note">{M.subsidy_note()}</p>
</div></div></section>"""


def location(c: dict, draft: bool, common: dict) -> str:
    p = c["post"]
    q = f'{common["region"]}, {p.get("Посёлок", "")}, {p.get("Адрес", "")}'
    widget = f"https://yandex.ru/map-widget/v1/?text={quote(q)}&z=16"
    return f"""<section id="map"><div class="wrap"><h2>Расположение</h2>
<div class="map"><iframe src="{e(widget)}" title="Расположение дома на Яндекс Карте" loading="lazy" allowfullscreen></iframe></div>
<div class="map-actions"><a class="btn btn-dark" href="https://yandex.ru/maps/?text={quote(q)}" target="_blank" rel="noopener">Открыть в Яндекс Картах</a></div>
{need("«что рядом» по посёлку: школа, сад, магазины, остановка, трасса, Краснодар — с расстояниями", draft)}
</div></section>"""


def documents(c: dict) -> str:
    cad = "".join(f'<button type="button" data-copy="{n}"><span>{e(label)}<br><code>{n}</code></span>'
                  f'<span class="copied">копировать</span></button>' for label, n in c["kn"])
    return f"""<section id="docs"><div class="wrap"><h2>Документы и собственность</h2>
<ul class="checks">
<li><b>Мы первый собственник.</b> Дом построен нами — у него нет прежних владельцев и истории.</li>
<li><b>Участок в собственности,</b> отмежёван, ИЖС — постоянная прописка.</li>
<li><b>Обременений и прописанных нет.</b> Выписку ЕГРН даём до задатка — или закажите сами по номеру.</li>
<li><b>Всё это прописано в договоре.</b></li>
</ul>
<div class="cad">{cad}</div>
<p class="hint">Проверить участок — на публичной кадастровой карте <a href="https://nspd.gov.ru/map" target="_blank" rel="noopener">nspd.gov.ru</a></p>
<details class="more"><summary>Документы на объект</summary><p class="muted">Договор купли-продажи участка, топосъёмка,
схема планировочной организации участка, уведомления о соответствии планируемого и построенного дома, технический план.</p></details>
</div></section>"""


def included(c: dict, draft: bool) -> str:
    main = "".join(f"<li>{e(x)}</li>" for x in c["included"])
    finish = "".join(f"<li>{e(x)}</li>" for x in c["included_finish"])
    body = (f'<ul class="checks">{main}</ul>' + (f'<h3 style="margin:20px 0 8px">Внутренняя отделка</h3>'
                                                 f'<ul class="utilities">{finish}</ul>' if finish else "")
            if main or finish else need("раздел «Что входит в цену» в карточке объекта", draft))
    return f"""<section><div class="wrap"><h2>Что входит в цену</h2>
<p style="margin-bottom:16px">Всё перечисленное входит в {rub(c["price"])} ₽ и в сумму кредита — доплат после сделки нет.</p>
{body}</div></section>"""


def how_to_buy(common: dict, M: Mortgage) -> str:
    ways = [("Семейная ипотека", f'{M.rate_range.capitalize()} по числу детей. <a href="#calc">Рассчитать</a>')]
    ways += [(e(w["title"]), e(w["text"])) for w in common["ways"]]
    cards = "".join(f'<div class="way"><h3>{t}</h3><p class="muted">{d}</p></div>' for t, d in ways)
    return f"""<section><div class="wrap"><h2>Как купить</h2>
<p style="margin-bottom:16px">Продаём напрямую как первый собственник — поэтому дом проходит по семейной ипотеке.
У частного владельца готовый дом по ней купить нельзя.</p>
<div class="ways">{cards}</div><p class="hint" style="margin-top:12px">Банки: {e(common["banks"])}.</p></div></section>"""


def deal(common: dict) -> str:
    d = common["deal"]
    rows = "".join(f"<tr><td>{e(x['what'])}</td><td>{e(x['sum'])}</td></tr>" for x in d["costs"])
    return f"""<section><div class="wrap"><h2>Как проходит сделка</h2>
<ol class="steps">
<li><b>Сопровождение бесплатно</b> — договоры, документы для банка, электронная регистрация.</li>
<li><b>Задаток {e(d["deposit"])}.</b> Банк отказал — возвращаем полностью, это прописано в договоре.</li>
<li><b>Опека</b> — если в сделке доли детей, поможем подать документы с первого раза.</li>
<li><b>Ваши расходы:</b> {e(d["costs_summary"])}.</li>
</ol>
<details class="more"><summary>Расходы подробно</summary><table class="costs">{rows}</table></details>
</div></section>"""


def about(c: dict, draft: bool) -> str:
    blocks = []
    for title, text in c["about"].items():
        extra = ""
        if title.startswith("Отделка") and c["finish"]:
            extra = "<ul>" + "".join(f"<li>{e(x)}</li>" for x in c["finish"]) + "</ul>"
        blocks.append(f"<div><h3>{e(title)}</h3><p>{e(text)}</p>{extra}</div>")
    body = f'<div class="about">{"".join(blocks)}</div>' if blocks else need("описание дома — 3 абзаца", draft)
    return f'<section><div class="wrap"><h2>О доме</h2>{body}</div></section>'


def gallery(imgs: list[dict], base: str, draft: bool) -> str:
    photos = [i for i in imgs if i["kind"] == "photo"]
    if not photos:
        return f'<section id="photos"><div class="wrap"><h2>Фото</h2>{need("фото оригиналами — в @SK_images_bot", draft)}</div></section>'
    items = "".join(f'<button type="button" data-full="{base}/img/{i["n"]:02d}.jpg"><img src="{base}/img/{i["n"]:02d}-s.jpg" '
                    f'alt="{e(i["what"])}" loading="lazy"></button>' for i in photos)
    return f"""<section id="photos"><div class="wrap"><h2>Фото</h2><div class="gallery">{items}</div></div></section>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Фото"><img alt="">
<button class="lb-close" type="button" aria-label="Закрыть">✕</button><button class="lb-prev" type="button" aria-label="Назад">‹</button>
<button class="lb-next" type="button" aria-label="Вперёд">›</button><p class="lb-count"></p></div>"""


def others(houses: list[dict]) -> str:
    cards = []
    for o in houses:
        pic = f'<img src="{o["pic"]}" alt="" loading="lazy">' if o["pic"] else '<span class="noimg">⌂</span>'
        cards.append(f'<a class="house" href="{e(o["href"])}">{pic}<div><b>{e(o["address"])}</b>'
                     f'<span>{e(o["place"])} · {e(o["area"])}</span><br><b>{rub(o["price"])} ₽</b></div></a>')
    if not cards:
        return ""
    return f'<section><div class="wrap"><h2>Другие дома в продаже</h2><div class="shelf">{"".join(cards)}</div></div></section>'


def contacts(draft: bool) -> str:
    return f"""<section id="contacts"><div class="wrap"><h2>Посмотреть дом</h2>
<p class="muted" style="margin-bottom:16px">Покажем в любой день — напишите или позвоните.</p>
{need("контакты для кнопок: телефон, MAX, WhatsApp, Telegram", draft)}</div></section>"""


def page(c: dict, imgs: list[dict], houses: list[dict], draft: bool, common: dict, M: Mortgage) -> str:
    base = "."                       # фото дома — в его папке (img/), общие стили и калькулятор — ../shared/
    hero_img = next((i for i in imgs if i["hero"]), next((i for i in imgs if i["kind"] == "photo"), None))
    p = c["post"]
    title = f'{p.get("Адрес", c["name"])}, {p.get("Посёлок", "")} — дом {p.get("Общая площадь", "")}, {rub(c["price"])} ₽'
    updated = date.fromisoformat(c["updated"]).strftime("%d.%m.%Y") if c["updated"] else date.today().strftime("%d.%m.%Y")
    bar = '<div class="draft-bar">Черновик — не опубликовано. Жёлтым отмечено, чего не хватает.</div>' if draft else ""
    stats = f"<p>{e(common['experience'])}</p>"
    preload = (f'<link rel="preload" as="image" href="{base}/img/{hero_img["n"]:02d}.jpg">' if hero_img else "")
    sticky = '<div class="sticky"><a class="btn btn-red" href="#calc">Рассчитать платёж</a></div>'
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(title)}. Готовый дом, семейная ипотека — расчёт платежа на странице.">
{'<meta name="robots" content="noindex">' if draft else ""}
<meta name="theme-color" content="#000000">
<link rel="preload" as="font" type="font/woff2" href="../shared/default/fonts/inter-cyrillic-900.woff2" crossorigin>
{preload}<link rel="stylesheet" href="../shared/default/landing.css">
<script type="module" src="../shared/landing.js"></script>
</head><body>
{bar}
<main>
{hero(c, hero_img, base, M)}
{facts(c)}
{plans(c, imgs, base, draft)}
{calc(c, M)}
{location(c, draft, common)}
{documents(c)}
{included(c, draft)}
{how_to_buy(common, M)}
{deal(common)}
{about(c, draft)}
{gallery(imgs, base, draft)}
{others(houses)}
{contacts(draft)}
</main>
<footer><div class="wrap">{stats}<p>Цена актуальна на {e(updated)}. Информация не является публичной офертой.</p></div></footer>
{sticky}
</body></html>
"""
