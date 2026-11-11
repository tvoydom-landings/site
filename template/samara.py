"""Тема «Samara» — вёрстка старого лендинга «Капелла Плюс» владельца (только Пшеничная 58, «theme": "samara»).

Стили — shared/samara/samara.css, эффекты — shared/samara/samara.js. Калькулятор, копирование КН, карта и
просмотр фото — общий shared/landing.js (те же id и data-атрибуты, что в основной теме). Порядок разделов:
текст, калькулятор, расположение, документы, покупка и сделка, потом описание и фото.
Тексты про климат и природу — про Ильский: тема используется только для дома в Ильском.
"""
from __future__ import annotations

import re
from datetime import date

from .common import Mortgage, e, need, rub

ICONS = (("Краснодар", "🏙"), ("мор", "🌊"), ("Новороссийск", "⚓"), ("Геленджик", "🏖"), ("Анап", "🏖"),
         ("школ", "🏫"), ("сад", "🏫"), ("улиц", "🛣"), ("дорог", "🛣"), ("трасс", "🛣"), ("станц", "🚆"))
STAT_LABELS = (("Общая площадь", "Общая площадь", "м²"), ("Первый этаж", "Первый этаж", "м²"),
               ("Мансарда", "Мансарда", "м²"), ("Участок", "Участок", "сот."))
SPEC_LABELS = (("электрич", "Электричество"), ("газ", "Отопление и кухня"), ("скважин", "Вода"),
               ("водопровод", "Вода"), ("лос", "Канализация"), ("септик", "Канализация"))
ARROW = ('<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" '
         'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
COPY_ICON = ('<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="5" y="5" width="9" height="9" rx="1.5" '
             'stroke="currentColor" stroke-width="1.5"/><path d="M11 5V3.5A1.5 1.5 0 0 0 9.5 2h-6A1.5 1.5 0 0 0 2 3.5v6A1.5 '
             '1.5 0 0 0 3.5 11H5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>')


def num(text: str) -> str | None:
    """«199,9 м²» → «199.9» (для data-to счётчика)."""
    m = re.search(r"\d+(?:[.,]\d+)?", text or "")
    return m.group().replace(",", ".") if m else None


def img_url(base: str, i: dict, small: bool = False) -> str:
    return f'{base}/img/{i["n"]:02d}{"-s" if small else ""}.jpg'


def label_of(i: dict) -> tuple[str, str]:
    """Подпись картинки: «природа: Гора Собербаш | Главная вершина района» → (заголовок, подзаголовок)."""
    text = re.sub(r"^\s*(природа|баннер|о доме)\s*:\s*", "", re.sub(r"\s*\((главное|баннер)\)\s*", " ", i["what"])).strip()
    title, _, sub = text.partition("|")
    return title.strip(), sub.strip()


def title_html(c: dict) -> str:
    """Проект «Капелла Плюс» → «Капелла<br><em>Плюс</em>», как в исходнике; без проекта — адрес."""
    words = (c["project"] or c["post"].get("Адрес", c["name"])).split()
    if len(words) < 2:
        return e(" ".join(words))
    return f'{e(" ".join(words[:-1]))}<br><em>{e(words[-1])}</em>'


# ---------------------------------------------------------------- разделы

def nav(c: dict) -> str:
    logo = e(c["brand"] or c["post"].get("Адрес", ""))
    return f"""<nav id="navbar">
  <a href="#" class="nav-logo">{logo}</a>
  <ul class="nav-links">
    <li><a href="#plan">Планировка</a></li>
    <li><a href="#calc">Ипотека</a></li>
    <li><a href="#location">Расположение</a></li>
    <li><a href="#gallery">Фото</a></li>
    <li><a href="#calc" class="nav-cta-btn">Рассчитать платёж</a></li>
  </ul>
</nav>"""


def hero(c: dict, img: dict | None, base: str, M: Mortgage) -> str:
    p = c["post"]
    bg = f' style="background-image:url(\'{img_url(base, img)}\')"' if img else ""
    badge = " &nbsp;·&nbsp; ".join(e(x) for x in (p.get("Отделка"), "ИЖС", p.get("Посёлок")) if x)
    facts = [p.get("Адрес"), p.get("Общая площадь"), p.get("Участок")] + [x for x in c["layout"] if "спал" in x]
    sub = ' <span class="dot">·</span> '.join(e(x) for x in facts if x)
    second = '<a href="#contact" class="btn-ghost">Записаться на просмотр</a>'
    return f"""<section class="hero">
  <div class="hero-bg" id="heroBg"{bg}></div>
  <div class="hero-overlay"></div>
  <div class="hero-content">
    <div class="hero-badge"><span class="hero-badge-dot"></span>{badge}</div>
    <h1 class="hero-title">{title_html(c)}</h1>
    <p class="hero-subtitle">{sub}</p>
    <p class="hero-price">{rub(c["price"])} ₽</p>
    <p class="hero-price-note">Семейная ипотека · ставка {M.rate_range} — зависит от числа детей</p>
    <div class="hero-actions">
      <a href="#calc" class="btn-primary">Рассчитать платёж для вашей семьи {ARROW}</a>
      {second}
    </div>
  </div>
  <div class="scroll-hint"><span>Прокрутите</span><div class="scroll-line"></div></div>
</section>"""


def stats(c: dict) -> str:
    p, items = c["post"], []
    for key, label, unit in STAT_LABELS:
        n = num(p.get(key, ""))
        if n:
            note = {"Общая площадь": "по ЕГРН", "Мансарда": "под отделку"}.get(key, "")
            items.append((n, unit, label, note))
    bedrooms = next((num(x) for x in c["layout"] if "спал" in x), None)
    if bedrooms:
        items.append((bedrooms, "спал.", "Спальни", ""))
    power = next((num(u) for u in c["utilities"] if "лектрич" in u), None)
    if power:
        items.append((power, "кВт", "Электричество", ""))
    cells = "".join(f"""
      <div class="stat fu">
        <div class="stat-num"><span class="cnt" data-to="{n}">0</span><span class="u">&thinsp;{e(u)}</span></div>
        <div class="stat-lbl">{e(label)}</div>{f'<div class="stat-note">{e(note)}</div>' if note else ""}
      </div>""" for n, u, label, note in items[:6])
    return f"""<section class="stats-strip">
  <div class="container"><div class="stats-row">{cells}
  </div></div>
</section>"""


def plan(c: dict, imgs: list[dict], base: str, draft: bool) -> str:
    plans = [i for i in imgs if i["kind"] == "plan"]
    pic = (f'<div class="fp-img-sticky fu"><img src="{img_url(base, plans[0])}" alt="Планировка" loading="lazy"></div>'
           if plans else f'<div>{need("планировка — прислать в @SK_images_bot", draft)}</div>')
    rooms = []
    for n, r in enumerate(c["rooms"]):
        name, _, rest = r.partition(" — ")
        area, _, desc = rest.partition(" — ")
        rooms.append(f"""
        <div class="room{' on' if n == 0 else ''} fu">
          <div class="room-hd"><span class="room-name">{e(name)}</span><span class="room-m2">{e(area)}</span></div>
          {f'<p class="room-desc">{e(desc)}</p>' if desc else ""}
        </div>""")
    intro = c["about"].get("Что за дом", "")
    note = '<p class="cad-hint" style="margin-top:14px">Площади — по техпаспорту. Рисунок планировки — проектный.</p>' if plans else ""
    return f"""<section class="floorplan" id="plan">
  <div class="container">
    <div class="stag fu">Планировка</div>
    <h2 class="stitle fu">Продуманное<br><em>пространство</em></h2>
    <p class="floorplan-intro-text fu">{e(intro)}</p>
    <div class="fp-grid">
      {pic}
      <div><div class="rooms">{"".join(rooms)}</div>{note}</div>
    </div>
  </div>
</section>"""


def calc(c: dict, M: Mortgage) -> str:
    kids = M.kids_buttons()
    return f"""<section class="section paper" id="calc">
  <div class="container">
    <div class="stag fu">Ипотека</div>
    <h2 class="stitle fu">Сколько будет<br><em>платёж</em></h2>
    <p class="section-lead fu">Семейная ипотека: ставка и сумма кредита зависят от числа детей. Выберите свой вариант —
    расчёт обновится сразу.</p>
    <div class="calc fu" data-price="{c["price"]}">
      <div class="calc-grid" style="margin-top:0"><div>
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
    </div>
  </div>
</section>"""


def location(c: dict, draft: bool) -> str:
    v = c["location"]
    paras = "".join(f"<p>{e(t)}</p>" for t in v["text"]) or need(f"текст о посёлке — Посёлки/{v['name']}.md", draft)
    cards = []
    for line in v["distances"] + c["nearby"]:
        value, _, label = line.partition(" — ")
        m = re.match(r"([\d–\-.,]+)\s*(.*)", value)
        if not m:
            continue
        icon = next((i for word, i in ICONS if word.lower() in label.lower()), "📍")
        cards.append(f'<div class="dist-card"><div class="dist-icon">{icon}</div><div class="dist-val">{e(m.group(1))} '
                     f'<span class="du">{e(m.group(2))}</span></div><div class="dist-lbl">{e(label)}</div></div>')
    return f"""<section class="location" id="location">
  <div class="container">
    <div class="location-grid">
      <div>
        <div class="stag fu">Расположение</div>
        <h2 class="stitle fu">Тёплый юг<br>в <em>40 минутах</em></h2>
        <div class="sbody fu" style="margin-top: 28px;">{paras}</div>
      </div>
      <div><div class="dist-grid fu">{"".join(cards)}</div></div>
    </div>
  </div>
</section>"""


def winter(imgs: list[dict], base: str) -> str:
    banner = next((i for i in imgs if i["kind"] == "banner"), None)
    if not banner:
        return ""
    return f"""<section class="winter">
  <div class="winter-bg" id="winterBg" style="background-image:url('{img_url(base, banner)}')"></div>
  <div class="winter-ov"></div>
  <div class="winter-cnt fu">
    <div class="winter-badge">Климат</div>
    <h2 class="winter-title">Мягкие зимы —<br>снег здесь редкий гость</h2>
    <p class="winter-sub">Тёплый сезон с апреля по октябрь. Короткая зима без лишних хлопот.</p>
  </div>
</section>"""


def mapblock(c: dict, imgs: list[dict], base: str, common: dict) -> str:
    p = c["post"]
    cad_img = next((i for i in imgs if i["kind"] == "cadastre"), None)
    kn = "".join(f"""
        <div>
          <div class="cad-lbl">Кадастровый номер — {e(label.lower())}</div>
          <button type="button" class="cad-num cad-copy" data-copy="{n}"><span>{n}</span><span class="copied">копировать</span></button>
        </div>""" for label, n in c["kn"])
    pic = (f'<div class="cad-img"><img src="{img_url(base, cad_img)}" alt="Кадастровая карта — участок" loading="lazy"></div>'
           if cad_img else "")
    widget = c["map"] or ""
    # карта сразу активна (решение владельца 2026-11-08); грузится, когда до неё долистали
    frame = (f'<div class="map map-frame"><iframe src="{e(widget)}" title="Расположение дома на Яндекс Карте" '
             f'loading="lazy" allowfullscreen></iframe></div>' if widget else "")
    return f"""<section class="mapblock">
  <div class="container">
    <div class="map-grid fu">
      {frame}
      <div class="cadastral">
        <div>
          <div class="cad-lbl">Адрес объекта</div>
          <div class="cad-addr" style="margin-top:8px;">{e(common["region"])},<br>{e(p.get("Посёлок", ""))}, {e(p.get("Адрес", ""))}</div>
        </div>{kn}
        {pic}
        <div class="cad-hint">Категория: земли населённых пунктов<br>Вид использования: ИЖС · Собственность<br>
        Проверить — на <a href="https://nspd.gov.ru/map" target="_blank" rel="noopener" style="text-decoration:underline">nspd.gov.ru</a></div>
      </div>
    </div>
  </div>
</section>"""


def documents() -> str:
    return """<section class="section paper" id="docs">
  <div class="container">
    <div class="stag fu">Документы</div>
    <h2 class="stitle fu">Чистая <em>история</em></h2>
    <p class="section-lead fu">Дом построен нами, все документы получены.</p>
    <ul class="checks fu">
      <li><b>Мы первый собственник.</b> Дом построен нами — у него нет прежних владельцев и истории.</li>
      <li><b>Участок в собственности,</b> отмежёван, ИЖС — постоянная прописка.</li>
      <li><b>Обременений и прописанных нет.</b> Выписку ЕГРН даём до задатка — или закажите сами по номеру.</li>
      <li><b>Всё это прописано в договоре.</b></li>
    </ul>
    <details class="more"><summary>Документы на объект</summary><p>Договор купли-продажи участка, топосъёмка,
    схема планировочной организации участка, уведомления о соответствии планируемого и построенного дома,
    технический план, технический паспорт.</p></details>
  </div>
</section>"""


def included(c: dict, draft: bool) -> str:
    main = "".join(f"<li>{e(x)}</li>" for x in c["included"])
    finish = "".join(f"<li>{e(x)}</li>" for x in c["included_finish"])
    body = (f"""<div class="incl-grid fu">
      <ul class="checks incl-main">{main}</ul>
      <div class="incl-finish"><div class="cad-lbl" style="color:var(--stone)">Внутренняя отделка</div><ul>{finish}</ul></div>
    </div>""" if main or finish else need("раздел «Что входит в цену» в карточке объекта", draft))
    return f"""<section class="section sand">
  <div class="container">
    <div class="stag fu">Цена</div>
    <h2 class="stitle fu">Что входит <em>в цену</em></h2>
    <p class="section-lead fu">Всё перечисленное входит в {rub(c["price"])} ₽ и в сумму кредита — доплат после сделки нет.</p>
    {body}
  </div>
</section>"""


def how_to_buy(common: dict, M: Mortgage) -> str:
    ways = [("Семейная ипотека", f'{M.rate_range.capitalize()} по числу детей. <a href="#calc">Рассчитать →</a>')]
    ways += [(e(w["title"]), e(w["text"])) for w in common["ways"]]
    cards = "".join(f'<div class="way"><h3>{t}</h3><p>{d}</p></div>' for t, d in ways)
    return f"""<section class="section sand">
  <div class="container">
    <div class="stag fu">Покупка</div>
    <h2 class="stitle fu">Как <em>купить</em></h2>
    <p class="section-lead fu">Продаём напрямую как первый собственник — поэтому дом проходит по семейной ипотеке.
    У частного владельца готовый дом по ней купить нельзя.</p>
    <div class="ways fu">{cards}</div>
    <p class="cad-hint" style="margin-top:16px">Банки: {e(common["banks"])}.</p>
  </div>
</section>"""


def deal(common: dict) -> str:
    d = common["deal"]
    rows = "".join(f"<tr><td>{e(x['what'])}</td><td>{e(x['sum'])}</td></tr>" for x in d["costs"])
    return f"""<section class="section paper">
  <div class="container">
    <div class="stag fu">Сделка</div>
    <h2 class="stitle fu">Как проходит <em>сделка</em></h2>
    <ol class="steps fu" style="margin-top:48px">
      <li><b>Сопровождение бесплатно</b> — договоры, документы для банка, электронная регистрация.</li>
      <li><b>Задаток {e(d["deposit"])}.</b> Банк отказал — возвращаем полностью, это прописано в договоре.</li>
      <li><b>Опека</b> — если в сделке доли детей, поможем подать документы с первого раза.</li>
      <li><b>Ваши расходы:</b> {e(d["costs_summary"])}.</li>
    </ol>
    <details class="more"><summary>Расходы подробно</summary><table class="costs">{rows}</table></details>
  </div>
</section>"""


def about(c: dict, imgs: list[dict], base: str, draft: bool) -> str:
    specs = []
    for u in c["utilities"]:
        label = next((l for word, l in SPEC_LABELS if word in u.lower()), "Коммуникации")
        specs.append((label, re.sub(r"^(Электричество|Без газа:)\s*", "", u).strip() or u))
    specs += [("Отделка", f) for f in c["finish"][:4]]
    spec_html = "".join(f'<div class="spec"><div class="spec-lbl">{e(l)}</div><div class="spec-val">{e(v)}</div></div>'
                        for l, v in specs)
    paras = "".join(f'<p class="sbody" style="margin-bottom:14px">{e(t)}</p>'
                    for k, t in c["about"].items() if not k.startswith("Что за дом"))
    pic = next((i for i in imgs if i["kind"] == "about"), None)
    pic_html = (f'<div class="about-img fu"><img src="{img_url(base, pic)}" alt="{e(label_of(pic)[0])}" loading="lazy"></div>'
                if pic else "")
    return f"""<section class="about" id="about">
  <div class="container">
    <div class="about-grid">
      <div>
        <div class="stag fu">О доме</div>
        <h2 class="stitle fu">Дом,<br>готовый <em>к жизни</em></h2>
        <div style="margin-top: 24px;" class="fu">{paras or need("описание дома", draft)}</div>
        <div class="specs fu">{spec_html}</div>
      </div>
      {pic_html}
    </div>
  </div>
</section>"""


def gallery(imgs: list[dict], base: str, draft: bool) -> str:
    photos = [i for i in imgs if i["kind"] == "photo"]
    cards = "".join(f"""
    <button type="button" class="gcard fu" data-full="{img_url(base, i)}">
      <img src="{img_url(base, i, small=True)}" alt="{e(label_of(i)[0])}" loading="lazy">
      <div class="gcard-ov"><span class="gcard-lbl">{e(label_of(i)[0])}</span></div>
    </button>""" for i in photos)
    body = (f'<div class="gallery-scroll" id="galleryScroll">{cards}\n  </div>' if photos
            else f'<div class="container">{need("фото — в @SK_images_bot", draft)}</div>')
    return f"""<section class="gallery" id="gallery">
  <div class="gallery-hd fu">
    <div class="stag">Фото</div>
    <h2 class="gallery-title">Посмотри<br>на <em style="font-style:italic;font-weight:300">дом</em></h2>
    <p class="gallery-sub">Настоящие фото · {len(photos)} снимков · листайте вбок</p>
  </div>
  {body}
</section>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Фото"><img alt="">
<button class="lb-close" type="button" aria-label="Закрыть">✕</button><button class="lb-prev" type="button" aria-label="Назад">‹</button>
<button class="lb-next" type="button" aria-label="Вперёд">›</button><p class="lb-count"></p></div>"""


def nature(imgs: list[dict], base: str) -> str:
    pics = [i for i in imgs if i["kind"] == "nature"]
    if not pics:
        return ""
    cards = "".join(f"""
      <div class="ncard"><img src="{img_url(base, i)}" alt="{e(label_of(i)[0])}" loading="lazy">
        <div class="ncard-ov"><div class="ncard-title">{e(label_of(i)[0])}</div><div class="ncard-sub">{e(label_of(i)[1])}</div></div>
      </div>""" for i in pics[:2])
    return f"""<section class="nature" id="nature">
  <div class="container">
    <div class="nature-hd">
      <div class="stag fu">Природа</div>
      <h2 class="stitle fu">Вид, который<br>не <em>надоедает</em></h2>
      <p class="sbody fu" style="margin-top:14px;">Предгорья Кавказа рядом. Гора Собербаш — главная вершина округи — видна прямо из посёлка.</p>
    </div>
    <div class="nature-grid fu">{cards}
    </div>
    <div class="nature-quote fu"><p class="nature-quote-text">«Рядом Крабовое ущелье, рыбалка на реке,<br>
    прогулки и грибные места — жизнь спокойная,<br>без городской суеты, но до большого города рукой подать»</p></div>
  </div>
</section>"""


def others(houses: list[dict]) -> str:
    cards = []
    for o in houses:
        pic = f'<img src="{o["pic"]}" alt="" loading="lazy">' if o["pic"] else '<span class="noimg">⌂</span>'
        cards.append(f'<a class="house" href="{e(o["href"])}">{pic}<div><b>{e(o["address"])}</b>'
                     f'<span>{e(o["place"])} · {e(o["area"])}</span><p class="price">{rub(o["price"])} ₽</p></div></a>')
    if not cards:
        return ""
    return f"""<section class="section sand">
  <div class="container">
    <div class="stag fu">Ещё дома</div>
    <h2 class="stitle fu" style="margin-bottom:40px">Другие дома <em>в продаже</em></h2>
    <div class="shelf">{"".join(cards)}</div>
  </div>
</section>"""


def contact(c: dict, draft: bool) -> str:
    phone = c["phone"]
    digits = "+7" + re.sub(r"\D", "", phone)[1:] if phone else ""
    block = (f"""<div class="cta-phone-block fu">
        <a href="tel:{digits}" class="cta-phone">{e(phone)}</a>
        <p class="cta-phone-note">{e(c["brand"])}</p>
        <button class="copy-btn" type="button" data-copy="{digits}">{COPY_ICON} <span class="copied">Скопировать номер</span></button>
      </div>""" if phone else need("телефон в карточку: «телефон:»", draft))
    name = f"«{e(c['project'])}»" if c["project"] else "Дом"
    return f"""<section class="cta-section" id="contact">
  <div class="cta-grid-bg"></div>
  <div class="container">
    <div class="cta-inner">
      <div class="cta-tag fu">Посмотреть дом</div>
      <h2 class="cta-title fu">{name}<br>ждёт своих хозяев</h2>
      <p class="cta-sub fu">Позвоните — ответим на все вопросы и запишем на просмотр</p>
      {block}
    </div>
  </div>
</section>"""


def footer(c: dict, common: dict) -> str:
    p = c["post"]
    updated = date.fromisoformat(c["updated"]).strftime("%d.%m.%Y") if c["updated"] else date.today().strftime("%d.%m.%Y")
    kn = "<br>".join(f"{e(label)}: {n}" for label, n in c["kn"])
    obj = f"""<div><div class="foot-head">Объект</div><div class="foot-body">
          {f"Жилой дом «{e(c['project'])}»<br>" if c["project"] else ""}{e(p.get("Адрес", ""))}<br>
          {e(p.get("Посёлок", ""))}, Северский р-н<br>Краснодарский край</div></div>"""
    brand = e(c["brand"]) if c["brand"] else ""
    left = (f'<div><div class="foot-logo">{brand}</div><p class="foot-tagline">Недвижимость Краснодарского края.<br>'
            f'Строим. Продаём. Отвечаем за качество.<br>{e(common["experience"])}</p></div>')
    phone = f'<a href="tel:+7{re.sub(r"[^0-9]", "", c["phone"])[1:]}">{e(c["phone"])}</a><br><br>' if c["phone"] else ""
    right = f'<div><div class="foot-head">Контакты</div><div class="foot-body">{phone}{kn}</div></div>'
    copy = f"© {date.today().year} {brand}" if brand else ""
    return f"""<footer>
  <div class="container">
    <div class="foot-grid">{left}{obj}{right}</div>
    <div class="foot-bottom">
      <p class="foot-copy">{copy}</p>
      <p class="foot-copy">Цена актуальна на {e(updated)}. Информация не является публичной офертой.</p>
    </div>
  </div>
</footer>"""


def page(c: dict, imgs: list[dict], houses: list[dict], draft: bool, common: dict, M: Mortgage) -> str:
    base = "."                       # фото дома — в его папке (img/), общие стили и калькулятор — ../shared/
    photos = [i for i in imgs if i["kind"] == "photo"]
    hero_img = next((i for i in imgs if i["hero"]), photos[0] if photos else None)
    p = c["post"]
    name = f'«{c["project"]}» — ' if c["project"] else ""
    title = f'{name}{p.get("Адрес", c["name"])}, {p.get("Посёлок", "")} — {rub(c["price"])} ₽'
    if c["brand"]:
        title += f' | {c["brand"]}'
    bar = ""
    if draft:
        bar = '<div class="draft-bar">Черновик — не опубликовано. Жёлтым отмечено, чего не хватает.</div>'
    preload = f'<link rel="preload" as="image" href="{img_url(base, hero_img)}">' if hero_img else ""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(title)}</title>
  <meta name="description" content="{e(title)}. Готовый дом, семейная ипотека — расчёт платежа на странице.">
  {'<meta name="robots" content="noindex">' if draft else ""}
  <script>document.documentElement.classList.add('js')</script>
  {preload}
  <link rel="stylesheet" href="../shared/samara/samara.css">
  {'<style>body.draft #navbar { top: 34px; } .draft-bar { position: fixed; top: 0; left: 0; right: 0; }</style>' if draft else ""}
  <script type="module" src="../shared/landing.js"></script>
  <script defer src="../shared/samara/samara.js"></script>
</head>
<body{' class="draft"' if draft else ""}>
{bar}
{nav(c)}
<main>
{hero(c, hero_img, base, M)}
{stats(c)}
{plan(c, imgs, base, draft)}
{calc(c, M)}
{location(c, draft)}
{winter(imgs, base)}
{mapblock(c, imgs, base, common)}
{documents()}
{included(c, draft)}
{how_to_buy(common, M)}
{deal(common)}
{about(c, imgs, base, draft)}
{gallery(imgs, base, draft)}
{nature(imgs, base)}
{others(houses)}
{contact(c, draft)}
</main>
{footer(c, common)}
<div class="sticky"><a class="btn-primary" href="#calc">Рассчитать платёж</a></div>
</body>
</html>
"""
