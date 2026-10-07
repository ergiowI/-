"""Демо-сайты для лидов без сайта. Запуск: python3 tools/sites.py [slug ...]  (без аргументов — все)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tpl import page, contact_cards, plist

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOURS_DAY = [f"{h:02d}:00" for h in range(10, 21)]

def tg(name, ini, sub, msgs, kb=None):
    m = "".join(f'<div class="msg">{t}<time>{tm}</time></div>' for t, tm in msgs)
    k = f'<div class="kb">{"".join(f"<span>{x}</span>" for x in kb)}</div>' if kb else ""
    return f'<div class="tg"><div class="who"><i>{ini}</i><div>{name}<small>{sub}</small></div></div>{m}{k}</div>'

def split(tag, h, ps, right, alt=False, id_=""):
    p = "".join(f"<p>{x}</p>" for x in ps)
    cls = ' class="alt"' if alt else ""
    idd = f' id="{id_}"' if id_ else ""
    return f'<section{cls}{idd}><div class="wrap split"><div><span class="tag">{tag}</span><h2>{h}</h2>{p}</div><div>{right}</div></div></section>'

SITES = []

# ───────────────────────── 1. Шиномонтаж Бикар ─────────────────────────
RAD = [("R13–R14", 1800), ("R15", 2000), ("R16", 2300), ("R17", 2600), ("R18", 2900), ("R19–R20", 3500)]
TYPES = [("Легковой", 1), ("Кроссовер", 1.2), ("Внедорожник / минивэн", 1.4)]
r50 = lambda n: int(round(n / 50) * 50)
CLS_R = ' class="r"'
def _row(r, p):
    cells = "".join(f'<td{CLS_R if i == 0 else ""}>{r50(p * k):,} ₽</td>'.replace(",", " ") for i, (_, k) in enumerate(TYPES))
    return f"<tr><td>{r}</td>{cells}</tr>"
rows = "".join(_row(r, p) for r, p in RAD)
SITES.append(dict(
    slug="bikar-site", send="Bikar-shinomontazh.html",
    title="Шиномонтаж Бикар 24/7 · Красносельское ш., 26",
    desc="Круглосуточный шиномонтаж на Красносельском шоссе, 26. Сезонная переобувка с ценой сразу и онлайн-запись на любое время.",
    fonts="https://fonts.googleapis.com/css2?family=Russo+One&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap",
    vars={"bg": "#0f1520", "panel": "#161e2b", "panel-2": "#1f2a3a", "line": "#2a3647", "ink": "#eef2f7", "muted": "#8d99ab",
          "accent": "#ff7a1a", "accent-ink": "#1a0d02", "accent-text": "#ff9a4d", "tag-bg": "#ff7a1a", "tag-ink": "#1a0d02",
          "font-display": '"Russo One", "Arial Black", sans-serif', "font-body": '"Manrope", "Segoe UI", Roboto, Arial, sans-serif',
          "font-num": '"JetBrains Mono", ui-monospace, Menlo, monospace', "h1-weight": "400", "em-style": "normal",
          "r-btn": "12px", "r-card": "20px", "shadow": "0 24px 48px -28px #000", "color-scheme": "dark"},
    name="Шиномонтаж Бикар", mark="Б", logo_sub="Шиномонтаж 24/7 · Красносельское ш., 26",
    demo_note="Цены примерные.", phone="+7 931 103-59-64",
    nav=[("prices", "Цены"), ("night", "Круглосуточно"), ("booking", "Запись"), ("contacts", "Контакты")],
    cta_short="Записаться", cta="Записаться на переобувку",
    tag="Открыты 24/7",
    h1="Переобувка <em>без очереди</em> в любое время суток",
    lead="Шиномонтаж на Красносельском шоссе, 26. Выберите радиус и время онлайн: цену увидите сразу, она не изменится на месте.",
    hero_chips=["<b>24/7</b> без выходных", "Красносельское ш., 26", "<b>R13–R20</b>, легковые и кроссоверы"],
    hero_card=f"""<div class="card bk-hero">
      <div class="live"><i></i> Сейчас открыто</div>
      <small>Переобувка R16, легковой</small>
      <div class="big">2 300 ₽</div>
      <div class="lines"><span>Снятие и установка</span><span>Монтаж и балансировка</span><span>4 колеса</span></div>
      <div class="fix">✓ Цена фиксируется при записи</div>
    </div>""",
    perks=[("🕐", "Круглосуточно", "Приезжайте после работы или ночью. По записи — без очереди, даже в сезон."),
           ("💳", "Цена сразу", "Выбираете тип машины и радиус и видите итог до визита. На месте сумма не меняется."),
           ("🔔", "Напомним сами", "Бот в Telegram напомнит о записи за 2 часа, а через полгода — что пора менять резину.")],
    prices_h="Сезонная переобувка", prices_p="Комплекс на 4 колеса: снятие, монтаж, балансировка, установка.",
    prices_html=f"""<div class="ptable-wrap"><table class="pt"><thead><tr><th>Радиус</th>{"".join(f"<th>{t}</th>" for t, _ in TYPES)}</tr></thead><tbody>{rows}</tbody></table></div>
    <div class="plist" style="margin-top:16px">
      <div class="card"><h3>Отдельные работы</h3><div class="prow"><span>Перестановка колёс<small>колёса уже на дисках</small></span><b>900 ₽</b></div><div class="prow"><span>Балансировка 4 колёс</span><b>1 000 ₽</b></div></div>
      <div class="card"><h3>Ремонт</h3><div class="prow"><span>Ремонт прокола<small>жгут или грибок</small></span><b>от 500 ₽</b></div><div class="prow"><span>Правка литого диска</span><b>от 1 500 ₽</b></div></div>
    </div>""",
    extra_html=split("Круглосуточно", "Ночью тоже работаем — и это видно заранее",
        ["Клиент выбирает время онлайн, даже в 3 часа ночи. Мастеру сразу приходит заявка с радиусом, ценой и телефоном.",
         "Не нужно отвлекаться на звонки посреди работы и объяснять цены по телефону."],
        tg("Бикар · заявки", "Б", "бот шиномонтажа",
           [("🆕 Запись № 118<br>🛞 Переобувка R17, кроссовер · 3 100 ₽<br>🗓 сегодня, 23:00<br>🙋 Андрей, +7 9•• •••-••-12", "22:41")],
           ["✅ Подтвердить", "✖ Отказать"]), id_="night"),
    book_h="Запишитесь за минуту", book_p="Время, которое уже заняли, зачёркнуто. Подтверждение придёт в Telegram или по СМС.",
    nojs_h="Запись на шиномонтаж", nojs_p="Напишите в WhatsApp радиус и удобное время — подтвердим запись и назовём цену.",
    faq=[("Можно приехать без записи?", "Да, мы работаем круглосуточно. Но в сезон по записи вы проедете без очереди."),
         ("Цена может измениться на месте?", "Нет. Цена за переобувку фиксируется при записи. Дополнительные работы — только после согласования с вами."),
         ("Сколько времени занимает переобувка?", "Обычно 30–40 минут на легковой автомобиль."),
         ("Есть ли хранение шин?", "Уточните по телефону или в WhatsApp — подскажем.")],
    contacts_html=contact_cards([("Красносельское ш., 26", "Въезд со стороны шоссе")], [("+7 931 103-59-64", "Звонки и WhatsApp")], "Круглосуточно", "Без выходных и перерывов"),
    footer_addr="Красносельское ш., 26",
    extra_css="""
.bk-hero { max-width: 400px; justify-self: center; margin-inline: auto }
.bk-hero .live { display: inline-flex; align-items: center; gap: 8px; font-size: 14px; color: var(--ok); font-weight: 600; margin-bottom: 18px }
.bk-hero .live i { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 0 4px color-mix(in srgb, var(--ok) 25%, transparent) }
.bk-hero > small { display: block; color: var(--muted) }
.bk-hero .big { font: 700 52px/1.1 var(--font-num); color: var(--accent-text); margin: 4px 0 16px }
.bk-hero .lines { display: grid; gap: 8px; margin-bottom: 18px }
.bk-hero .lines span { padding-left: 22px; position: relative; font-size: 15px }
.bk-hero .lines span::before { content: ""; position: absolute; left: 0; top: 9px; width: 10px; height: 2px; background: var(--accent) }
.bk-hero .fix { border-top: 1px dashed var(--line); padding-top: 14px; color: var(--ok); font-size: 14px }
""",
    engine=dict(days=10, hours=[f"{h:02d}:00" for h in range(24)],
        opts=dict(label="Тип машины", list=[[t, k] for t, k in TYPES]),
        services=[dict(n=f"Переобувка {r}", p=p, d="4 колеса, комплекс") for r, p in RAD] +
                 [dict(n="Перестановка колёс", p=900, d="колёса на дисках"), dict(n="Ремонт прокола", p=500, frm=1, d="жгут или грибок"), dict(n="Балансировка 4 колёс", p=1000)],
        text=dict(svcLabel="Услуга", pickSvc="Выберите услугу", svcRow="Услуга", sumTitle="Ваша запись", send="Записаться",
                  hint="Оплата на месте после работы", adminTitle="Запись", adminIcon="🛞", adminTo="мастеру",
                  doneTitle="Вы записаны", doneText="ждём вас {when} на Красносельском ш., 26. Напоминание придёт за 2 часа."))
))

# ───────────────────────── 3. Алло Сервис ─────────────────────────
SITES.append(dict(
    slug="allo-servis-site", send="Allo-Servis-remont-telefonov.html",
    title="Алло Сервис · ремонт телефонов, пр. Ветеранов, 147",
    desc="Ремонт телефонов, планшетов и ноутбуков на проспекте Ветеранов, 147. Прайс на сайте, оценка по фото, статус ремонта онлайн.",
    fonts="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap",
    vars={"bg": "#f4f7fa", "panel": "#ffffff", "panel-2": "#eaf0f6", "line": "#dbe4ee", "ink": "#13202e", "muted": "#64768a",
          "accent": "#0a7cff", "accent-ink": "#ffffff", "accent-text": "#0a6ad8", "tag-bg": "#e1eefc", "tag-ink": "#0a5bb0",
          "font-display": '"Onest", "Segoe UI", Arial, sans-serif', "font-body": '"Onest", "Segoe UI", Roboto, Arial, sans-serif',
          "font-num": '"JetBrains Mono", ui-monospace, Menlo, monospace', "h1-weight": "700", "em-style": "normal",
          "r-btn": "12px", "r-card": "18px", "shadow": "0 24px 48px -30px rgba(15,40,80,.35)", "color-scheme": "light"},
    name="Алло Сервис", mark="A", logo_sub="Ремонт техники · пр. Ветеранов, 147",
    demo_note="Цены и часы примерные.", phone="+7 904 555-05-56",
    nav=[("prices", "Цены"), ("status", "Статус ремонта"), ("booking", "Заявка"), ("contacts", "Контакты")],
    cta_short="Заявка", cta="Оставить заявку на ремонт",
    tag="Ремонт телефонов и ноутбуков",
    h1="Цена ремонта — <em>до того, как отдали телефон</em>",
    lead="Прайс открыт на сайте. Пришлите фото поломки — назовём точную сумму. Статус ремонта видно онлайн по номеру квитанции.",
    hero_chips=["пр. Ветеранов, 147", "<b>Диагностика</b> бесплатно", "Гарантия на работу"],
    hero_card="""<div class="card al-hero">
      <div class="head"><small>Квитанция</small><b>№ 2417</b></div>
      <div class="dev">iPhone 12 · замена экрана</div>
      <ol class="steps"><li class="d">Принят<span>пн, 12:10</span></li><li class="d">Диагностика<span>пн, 12:40</span></li><li class="d">Ремонт<span>пн, 15:20</span></li><li class="d now">Готов, можно забирать<span>пн, 16:05</span></li></ol>
      <div class="sum"><span>К оплате</span><b>6 900 ₽</b></div>
    </div>""",
    perks=[("📋", "Прайс на виду", "Основные цены на сайте. Итог называем после диагностики и до начала ремонта."),
           ("📷", "Оценка по фото", "Пришлите фото и модель в WhatsApp — скажем цену и срок, не выходя из дома."),
           ("🔎", "Статус онлайн", "Не нужно звонить и спрашивать, готов ли телефон: статус виден по номеру квитанции.")],
    prices_h="Сколько стоит ремонт", prices_p="Цена зависит от модели. Точную сумму называем после бесплатной диагностики.",
    prices_html=plist([
        ("Телефоны", [("Замена экрана", "1–2 часа при наличии", "от 2 500 ₽", 0), ("Замена аккумулятора", "30–60 мин", "от 1 500 ₽", 0), ("Разъём зарядки", "", "от 1 200 ₽", 0), ("Стекло камеры", "", "от 900 ₽", 0), ("После воды", "чистка и диагностика", "от 1 000 ₽", 0)]),
        ("Ноутбуки и ТВ", [("Чистка ноутбука от пыли", "с заменой термопасты", "1 800 ₽", 0), ("Замена экрана ноутбука", "", "от 4 500 ₽", 0), ("Замена клавиатуры", "", "от 2 000 ₽", 0), ("Ремонт телевизора", "после диагностики", "от 2 500 ₽", 0), ("Диагностика", "любое устройство", "бесплатно", 0)]),
    ]),
    extra_html="""<section id="status"><div class="wrap split">
      <div><span class="tag">Статус ремонта</span><h2>Готов ли телефон? Проверьте сами</h2>
        <p>Номер квитанции выдаём при приёме. Когда ремонт закончен, бот присылает сообщение в Telegram: «Готов, можно забирать» и сумму.</p>
        <p>Хотите узнать цену заранее? <a href="https://wa.me/79045550556?text=%D0%97%D0%B4%D1%80%D0%B0%D0%B2%D1%81%D1%82%D0%B2%D1%83%D0%B9%D1%82%D0%B5!%20%D0%9E%D1%86%D0%B5%D0%BD%D0%B8%D1%82%D0%B5%20%D1%80%D0%B5%D0%BC%D0%BE%D0%BD%D1%82%20%D0%BF%D0%BE%20%D1%84%D0%BE%D1%82%D0%BE" target="_blank" rel="noopener">Пришлите фото в WhatsApp</a>.</p></div>
      <div class="card"><label for="tNo" class="tlbl">Номер квитанции</label>
        <div class="trow"><input id="tNo" inputmode="numeric" placeholder="Например, 2417"><button class="btn" type="button" id="tGo">Проверить</button></div>
        <div id="tOut" aria-live="polite"><ol class="steps"><li class="d">Принят<span>сегодня, 11:20</span></li><li class="d now">Диагностика<span>сегодня, 11:45</span></li><li>Ремонт<span>—</span></li><li>Готов<span>—</span></li></ol><p class="note nojs">Пример. Проверка по номеру работает при открытии в браузере.</p></div>
      </div></div></section>""",
    book_h="Заявка на ремонт", book_p="Выберите поломку и когда удобно принести. Мастер подготовит запчасть заранее, если она есть в наличии.",
    nojs_h="Заявка на ремонт", nojs_p="Напишите в WhatsApp модель и что случилось, можно с фото, — назовём цену и срок.",
    faq=[("Сколько стоит диагностика?", "Бесплатно, даже если вы решите не ремонтировать."),
         ("Есть ли гарантия?", "Да, на работу и установленные запчасти. Срок указан в квитанции."),
         ("Сколько длится ремонт?", "Экран и аккумулятор на популярные модели — обычно в день обращения. Если запчасть под заказ, скажем срок сразу."),
         ("Можно ли узнать цену без визита?", "Да: пришлите модель и фото поломки в WhatsApp.")],
    contacts_html=contact_cards([("пр. Ветеранов, 147", "Торговый комплекс, отдел ремонта")], [("+7 904 555-05-56", "Звонки и WhatsApp")], "Ежедневно, 10:00–21:00", "Приём устройств до 20:30"),
    footer_addr="пр. Ветеранов, 147",
    extra_css="""
.al-hero { max-width: 400px; margin-inline: auto }
.al-hero .head { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px dashed var(--line); padding-bottom: 12px; margin-bottom: 12px }
.al-hero .head small { color: var(--muted) } .al-hero .head b { font: 700 22px/1 var(--font-num) }
.al-hero .dev { font-weight: 600; margin-bottom: 14px }
.al-hero .sum { display: flex; justify-content: space-between; align-items: baseline; border-top: 1px dashed var(--line); padding-top: 14px; margin-top: 6px }
.al-hero .sum b { font: 700 28px/1 var(--font-num); color: var(--accent-text) }
ol.steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 0 }
ol.steps li { position: relative; padding: 0 0 16px 30px; font-weight: 600; color: var(--muted) }
ol.steps li span { display: block; font-weight: 400; font-size: 13px }
ol.steps li::before { content: ""; position: absolute; left: 0; top: 4px; width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--line); background: var(--panel) }
ol.steps li:not(:last-child)::after { content: ""; position: absolute; left: 8px; top: 22px; bottom: 0; width: 2px; background: var(--line) }
ol.steps li.d { color: var(--ink) } ol.steps li.d::before { background: var(--accent); border-color: var(--accent) }
ol.steps li.now::before { background: var(--ok); border-color: var(--ok); box-shadow: 0 0 0 4px color-mix(in srgb, var(--ok) 22%, transparent) }
.tlbl { display: block; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 10px }
.trow { display: flex; gap: 8px; margin-bottom: 20px }
.trow input { flex: 1; min-width: 0; background: var(--bg); border: 1.5px solid var(--line); color: var(--ink); border-radius: 12px; padding: 13px 14px; font: inherit }
html:not(.js) .trow { display: none }
""",
    extra_js=r"""
(() => {
  const STEPS = ["Принят", "Диагностика", "Ремонт", "Готов, можно забирать"];
  const DEV = ["iPhone 11 · замена аккумулятора", "Samsung A52 · замена экрана", "Xiaomi Redmi Note 10 · разъём зарядки", "Ноутбук ASUS · чистка от пыли", "iPhone 13 · стекло камеры"];
  $("tGo").onclick = () => {
    const n = digits($("tNo").value);
    if (n.length < 3) { $("tOut").innerHTML = `<p class="note">Введите номер с квитанции, например 2417.</p>`; return; }
    const sum = [...n].reduce((a, c) => a + +c, 0), stage = sum % 4, dev = DEV[sum % DEV.length];
    const t = ["10:15", "10:40", "13:30", "16:05"];
    $("tOut").innerHTML = `<p style="margin:0 0 14px"><b>№ ${esc(n)}</b> · ${dev}</p><ol class="steps">${STEPS.map((s, i) =>
      `<li class="${i < stage ? "d" : i === stage ? "d now" : ""}">${s}<span>${i <= stage ? "сегодня, " + t[i] : "—"}</span></li>`).join("")}</ol>
      <p class="note">${stage === 3 ? "Ремонт готов. Ждём вас на пр. Ветеранов, 147." : "Как только статус изменится, бот пришлёт сообщение."} (в демо статус условный)</p>`;
  };
  $("tNo").addEventListener("keydown", e => { if (e.key === "Enter") $("tGo").click(); });
})();
""",
    engine=dict(days=10, hours=HOURS_DAY,
        services=[dict(n="Замена экрана телефона", p=2500, frm=1), dict(n="Замена аккумулятора", p=1500, frm=1),
                  dict(n="Разъём зарядки", p=1200, frm=1), dict(n="Телефон после воды", p=1000, frm=1),
                  dict(n="Стекло камеры", p=900, frm=1), dict(n="Чистка ноутбука", p=1800),
                  dict(n="Экран ноутбука", p=4500, frm=1), dict(n="Ремонт телевизора", p=2500, frm=1),
                  dict(n="Не знаю, нужна диагностика", p=0)],
        text=dict(svcLabel="Что случилось", pickSvc="Выберите поломку", svcRow="Ремонт", sumTitle="Ваша заявка", send="Отправить заявку",
                  hint="Точную цену назовём после диагностики, до ремонта", adminTitle="Заявка на ремонт", adminIcon="📱", adminTo="мастеру",
                  doneTitle="Заявка принята", doneText="ждём вас {when} на пр. Ветеранов, 147. Если нужно уточнить модель, мастер напишет.",
                  dayLabel="Когда принесёте", noteLabel="Модель и что случилось", notePh="Например: iPhone 12, упал, разбит экран"))
))

# ───────────────────────── 4. Студия красоты «Нероли» ─────────────────────────
SITES.append(dict(
    slug="neroli-site", send="Neroli-studiya-krasoty.html",
    title="Студия красоты «Нероли» · пр. Ветеранов, 143",
    desc="Студия красоты «Нероли» на проспекте Ветеранов, 143: маникюр, стрижки и окрашивание, брови и ресницы, уход за лицом. Онлайн-запись к мастеру.",
    fonts="https://fonts.googleapis.com/css2?family=Prata&family=Manrope:wght@400;500;600;700&display=swap",
    vars={"bg": "#fbf7f1", "panel": "#ffffff", "panel-2": "#f3ece2", "line": "#ebe2d6", "ink": "#2b2622", "muted": "#857a6f",
          "accent": "#e07b33", "accent-ink": "#ffffff", "accent-text": "#bf5f1b", "tag-bg": "#fbe6d4", "tag-ink": "#9a4a12",
          "font-display": '"Prata", Georgia, serif', "font-body": '"Manrope", "Segoe UI", Roboto, Arial, sans-serif',
          "font-num": '"Manrope", "Segoe UI", Arial, sans-serif', "h1-weight": "400", "em-style": "normal",
          "r-btn": "14px", "r-card": "22px", "shadow": "0 24px 48px -32px rgba(120,70,30,.35)", "color-scheme": "light"},
    name="Студия красоты «Нероли»", mark="Н", logo_sub="пр. Ветеранов, 143",
    demo_note="Цены, мастера и часы примерные.", phone="+7 981 962-90-49",
    nav=[("prices", "Услуги"), ("masters", "Мастера"), ("booking", "Запись"), ("contacts", "Контакты")],
    cta_short="Записаться", cta="Записаться онлайн",
    tag="Студия красоты на Ветеранов",
    h1="Запишитесь к своему мастеру <em>за минуту</em>",
    lead="Маникюр, стрижки и окрашивание, брови и уход за лицом на проспекте Ветеранов, 143. Свободные окна видно сразу — не нужно звонить и ждать ответа.",
    hero_chips=["пр. Ветеранов, 143", "<b>Ежедневно</b> 10:00–21:00", "Запись онлайн 24/7"],
    hero_card="""<div class="card ne-hero">
      <small class="cap">Свободно сегодня</small>
      <div class="slot"><time>14:00</time><span><b>Маникюр с покрытием</b>Анна</span></div>
      <div class="slot"><time>16:30</time><span><b>Женская стрижка</b>Виктория</span></div>
      <div class="slot"><time>18:00</time><span><b>Брови: коррекция и окрашивание</b>Ксения</span></div>
      <a class="btn" href="#booking" style="width:100%;margin-top:6px">Выбрать время</a>
    </div>""",
    perks=[("🗓", "Видно свободное время", "Выбираете мастера и окно сами, в любое время суток — даже когда студия закрыта."),
           ("💬", "Напоминание накануне", "Бот пришлёт напоминание и кнопку «Перенести», если планы поменялись."),
           ("🌸", "Свой мастер", "Записывайтесь к любимому мастеру повторно в два нажатия.")],
    prices_h="Услуги и цены", prices_p="Цена может зависеть от длины волос и сложности работы — мастер скажет заранее.",
    prices_html=plist([
        ("Ногти", [("Маникюр с покрытием гель-лак", "90 мин", "2 200 ₽", 0), ("Педикюр с покрытием", "120 мин", "2 800 ₽", 0), ("Наращивание ногтей", "150 мин", "3 200 ₽", 0)]),
        ("Волосы", [("Женская стрижка", "60 мин", "1 800 ₽", 0), ("Окрашивание в один тон", "от 2 часов", "от 3 500 ₽", 0), ("Укладка", "45 мин", "1 500 ₽", 0)]),
        ("Брови и ресницы", [("Коррекция и окрашивание бровей", "45 мин", "1 200 ₽", 0), ("Ламинирование ресниц", "60 мин", "2 300 ₽", 0)]),
        ("Лицо", [("Чистка лица", "75 мин", "2 900 ₽", 0), ("Уходовая процедура", "60 мин", "2 500 ₽", 0)]),
    ]),
    extra_html="""<section id="masters"><div class="wrap">
      <div class="sec-head"><div><span class="tag">Мастера</span><h2>Наша команда</h2></div><p>Фото мастеров добавим после настройки сайта.</p></div>
      <div class="team">
        <div class="card"><i>А</i><b>Анна</b><small>мастер маникюра</small><a href="#booking" class="btn ghost sm">Записаться</a></div>
        <div class="card"><i>О</i><b>Ольга</b><small>маникюр и педикюр</small><a href="#booking" class="btn ghost sm">Записаться</a></div>
        <div class="card"><i>В</i><b>Виктория</b><small>парикмахер-стилист</small><a href="#booking" class="btn ghost sm">Записаться</a></div>
        <div class="card"><i>К</i><b>Ксения</b><small>брови и ресницы</small><a href="#booking" class="btn ghost sm">Записаться</a></div>
        <div class="card"><i>М</i><b>Марина</b><small>косметолог</small><a href="#booking" class="btn ghost sm">Записаться</a></div>
      </div></div></section>""" + split("Напоминания", "Клиенты приходят вовремя",
        ["За день до визита бот присылает напоминание. Если планы поменялись, клиент переносит запись сам, и окно сразу освобождается для других.",
         "Администратору не нужно обзванивать клиентов и отвечать на одни и те же вопросы."],
        tg("Студия «Нероли»", "Н", "бот записи",
           [("Добрый день, Елена! Напоминаем: завтра в 14:00<br>💅 Маникюр с покрытием · Анна<br>📍 пр. Ветеранов, 143", "12:00")],
           ["✅ Приду", "🔄 Перенести"]), alt=False),
    book_h="Онлайн-запись", book_p="Сначала услуга, потом мастер и время. Занятые окна зачёркнуты.",
    nojs_h="Запись в студию", nojs_p="Напишите в WhatsApp услугу и удобное время — подберём мастера и подтвердим запись.",
    faq=[("Можно ли выбрать конкретного мастера?", "Да. Или выберите «любой свободный» — так быстрее найдётся окно."),
         ("Как перенести или отменить запись?", "Кнопкой в напоминании или в WhatsApp. Пожалуйста, не позднее чем за 3 часа."),
         ("Как оплатить?", "Картой, наличными или переводом после процедуры."),
         ("Цена может измениться?", "Только если объём работы отличается от выбранного, например длина волос. Мастер скажет до начала.")],
    contacts_html=contact_cards([("пр. Ветеранов, 143", "Вход с проспекта")], [("+7 981 962-90-49", "Звонки и WhatsApp")], "Ежедневно, 10:00–21:00", "Последняя запись — за 1,5 часа до закрытия"),
    footer_addr="пр. Ветеранов, 143",
    extra_css="""
.ne-hero { max-width: 400px; margin-inline: auto; padding: 26px }
.ne-hero .cap { display: block; color: var(--muted); font-size: 13px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; margin-bottom: 12px }
.ne-hero .slot { display: grid; grid-template-columns: 70px minmax(0, 1fr); gap: 14px; align-items: center; padding: 12px 0; border-top: 1px dashed var(--line) }
.ne-hero time { font: 700 20px/1 var(--font-num); color: var(--accent-text) }
.ne-hero .slot span { color: var(--muted); font-size: 14px } .ne-hero .slot b { display: block; color: var(--ink); font-size: 15.5px }
.team { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px }
@media (max-width: 900px) { .team { grid-template-columns: repeat(2, minmax(0, 1fr)) } }
.team .card { text-align: center; padding: 22px 14px }
.team i { width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 12px; display: grid; place-items: center; font: 400 30px/1 var(--font-display); font-style: normal; background: var(--tag-bg); color: var(--tag-ink) }
.team b { display: block; font: 400 20px/1.2 var(--font-display) }
.team small { display: block; color: var(--muted); margin-bottom: 14px }
""",
    engine=dict(days=12, hours=HOURS_DAY,
        services=[dict(n="Маникюр с покрытием", p=2200, d="90 мин", c="nails"), dict(n="Педикюр с покрытием", p=2800, d="120 мин", c="nails"),
                  dict(n="Наращивание ногтей", p=3200, d="150 мин", c="nails"), dict(n="Женская стрижка", p=1800, d="60 мин", c="hair"),
                  dict(n="Окрашивание в один тон", p=3500, frm=1, d="от 2 часов", c="hair"), dict(n="Укладка", p=1500, d="45 мин", c="hair"),
                  dict(n="Брови: коррекция и окрашивание", p=1200, d="45 мин", c="brows"), dict(n="Ламинирование ресниц", p=2300, d="60 мин", c="brows"),
                  dict(n="Чистка лица", p=2900, d="75 мин", c="face")],
        masters=[dict(n="Анна", r="маникюр", cats=["nails"]), dict(n="Ольга", r="маникюр и педикюр", cats=["nails"]),
                 dict(n="Виктория", r="парикмахер-стилист", cats=["hair"]), dict(n="Ксения", r="брови и ресницы", cats=["brows"]),
                 dict(n="Марина", r="косметолог", cats=["face"])],
        text=dict(svcLabel="Услуга", pickSvc="Выберите услугу", svcRow="Услуга", sumTitle="Ваша запись", send="Записаться",
                  hint="Оплата после процедуры", adminTitle="Запись", adminIcon="💅", adminTo="администратору",
                  doneTitle="Вы записаны", doneText="ждём вас {when} на пр. Ветеранов, 143. Напоминание придёт накануне."))
))

# ───────────────────────── 5. BACKENBART ─────────────────────────
WA1 = "79520985050"
cert = lambda amount, sub: f'<div class="card cert"><small>Подарочный сертификат</small><b>{amount}</b><p>{sub}</p><a class="btn sm" target="_blank" rel="noopener" href="https://wa.me/{WA1}?text={amount.replace(" ", "%20").replace("₽", "%E2%82%BD").replace("+", "%2B")}%20%E2%80%94%20%D1%85%D0%BE%D1%87%D1%83%20%D1%81%D0%B5%D1%80%D1%82%D0%B8%D1%84%D0%B8%D0%BA%D0%B0%D1%82">Заказать</a></div>'
SITES.append(dict(
    slug="backenbart-site", send="BACKENBART-barbershop.html",
    title="BACKENBART · барбершоп на Петергофском и Ветеранов",
    desc="Барбершоп BACKENBART: Петергофское ш., 72к4 и пр. Ветеранов, 183. Мужские стрижки, борода, бритьё. Онлайн-запись к барберу и подарочные сертификаты.",
    fonts="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap",
    vars={"bg": "#121110", "panel": "#1b1917", "panel-2": "#25221f", "line": "#35302a", "ink": "#f1ebe3", "muted": "#9d9285",
          "accent": "#c9a15b", "accent-ink": "#17130c", "accent-text": "#d9b673", "tag-bg": "#c9a15b", "tag-ink": "#17130c",
          "font-display": '"Oswald", "Arial Narrow", sans-serif', "font-body": '"Manrope", "Segoe UI", Roboto, Arial, sans-serif',
          "font-num": '"Oswald", "Arial Narrow", sans-serif', "h1-weight": "600", "em-style": "normal",
          "r-btn": "6px", "r-card": "14px", "shadow": "0 24px 48px -28px #000", "color-scheme": "dark"},
    name="BACKENBART", mark="B", logo_sub="Барбершоп · 2 адреса",
    demo_note="Цены, барберы и часы примерные.", phone="+7 952 098-50-50",
    nav=[("prices", "Цены"), ("gift", "Сертификаты"), ("booking", "Запись"), ("contacts", "Контакты")],
    cta_short="Записаться", cta="Записаться к барберу",
    tag="Барбершоп · 2 адреса",
    h1="СТРИЖКА И БОРОДА <em>БЕЗ ЗВОНКОВ</em>",
    lead="Петергофское шоссе и проспект Ветеранов. Выберите адрес, барбера и время онлайн — подтверждение придёт в Telegram.",
    hero_chips=["Петергофское ш., 72к4", "пр. Ветеранов, 183", "<b>от 900 ₽</b>"],
    hero_card="""<div class="bb-hero">
      <div class="card"><small>Петергофское ш., 72к4</small><b>Сегодня свободно</b><div class="t"><span>17:00</span><span>18:30</span><span>20:00</span></div></div>
      <div class="card"><small>пр. Ветеранов, 183</small><b>Сегодня свободно</b><div class="t"><span>16:00</span><span>19:00</span></div></div>
      <div class="card gift"><small>Подарок</small><b>Сертификат от 1 500 ₽</b><a href="#gift">Подробнее →</a></div>
    </div>""",
    perks=[("✂️", "Запись за минуту", "Адрес, барбер, время — и готово. Не нужно писать в ВК и ждать ответа."),
           ("📍", "Два адреса", "Выбирайте точку, которая ближе: Петергофское шоссе или проспект Ветеранов."),
           ("🎁", "Сертификаты", "Подарочный сертификат на сумму или услугу — заказ в пару сообщений.")],
    prices_h="Услуги и цены", prices_p="Цены одинаковые на обоих адресах.",
    prices_html=plist([
        ("Стрижки", [("Мужская стрижка", "60 мин", "1 600 ₽", 0), ("Стрижка машинкой", "30 мин", "900 ₽", 0), ("Детская стрижка", "до 12 лет", "1 100 ₽", 0), ("Отец + сын", "две стрижки", "2 600 ₽", 0)]),
        ("Борода и бритьё", [("Моделирование бороды", "45 мин", "1 000 ₽", 0), ("Стрижка + борода", "90 мин", "2 400 ₽", 0), ("Королевское бритьё", "горячее полотенце", "1 500 ₽", 0), ("Камуфляж седины", "", "900 ₽", 0)]),
    ]),
    extra_html=f"""<section id="gift"><div class="wrap">
      <div class="sec-head"><div><span class="tag">Подарочные сертификаты</span><h2>Лучший подарок мужчине</h2></div><p>Электронный сертификат придёт в WhatsApp или Telegram, его можно переслать. Действует на обоих адресах.</p></div>
      <div class="certs">{cert("1 500 ₽", "мужская стрижка")}{cert("2 400 ₽", "стрижка + борода")}{cert("3 000 ₽", "на любые услуги")}{cert("5 000 ₽", "на любые услуги")}</div>
    </div></section>""",
    book_h="Запись к барберу", book_p="Выберите адрес — покажем барберов и свободное время на этой точке.",
    nojs_h="Запись к барберу", nojs_p="Напишите в WhatsApp адрес, услугу и удобное время — подтвердим запись.",
    faq=[("Можно прийти без записи?", "Можно, если есть свободный барбер. По записи — без ожидания."),
         ("Как перенести запись?", "Кнопкой в напоминании от бота или в WhatsApp."),
         ("Сертификат действует на обоих адресах?", "Да, на Петергофском и на Ветеранов."),
         ("Стрижёте детей?", "Да, детская стрижка до 12 лет. Есть комплекс «Отец + сын».")],
    contacts_html=contact_cards([("Петергофское ш., 72к4", "Первая точка"), ("пр. Ветеранов, 183", "Вторая точка")],
                                [("+7 952 098-50-50", "Петергофское ш."), ("+7 903 098-55-38", "пр. Ветеранов")], "Ежедневно, 10:00–22:00", "На обоих адресах"),
    footer_addr="Петергофское ш., 72к4 · пр. Ветеранов, 183",
    extra_css="""
.hero h1 { text-transform: uppercase; letter-spacing: .01em }
.sec-head h2, .split h2 { text-transform: uppercase }
.bb-hero { display: grid; gap: 12px; max-width: 420px; margin-inline: auto }
.bb-hero small { color: var(--muted); font-size: 13px }
.bb-hero b { display: block; font: 600 20px/1.3 var(--font-display); text-transform: uppercase; margin: 2px 0 10px }
.bb-hero .t { display: flex; gap: 8px; flex-wrap: wrap }
.bb-hero .t span { border: 1px solid var(--accent); color: var(--accent-text); border-radius: 6px; padding: 5px 12px; font: 600 16px/1.2 var(--font-num) }
.bb-hero .gift { background: linear-gradient(135deg, #2a2216, var(--panel)); border-color: #5a4626 }
.bb-hero .gift a { color: var(--accent-text); text-decoration: none; font-weight: 600 }
.certs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px }
@media (max-width: 900px) { .certs { grid-template-columns: repeat(2, minmax(0, 1fr)) } }
@media (max-width: 480px) { .certs { grid-template-columns: minmax(0, 1fr) } }
.cert { background: linear-gradient(150deg, #2a2216, var(--panel) 70%); border-color: #4a3a22 }
.cert small { color: var(--muted); font-size: 12px; letter-spacing: .08em; text-transform: uppercase }
.cert b { display: block; font: 700 34px/1.2 var(--font-num); color: var(--accent-text); margin: 6px 0 2px }
.cert p { color: var(--muted); margin: 0 0 16px; font-size: 15px }
""",
    engine=dict(days=10, hours=[f"{h:02d}:00" for h in range(10, 22)],
        branches=[["Петергофское ш.", "Петергофское ш., 72к4"], ["пр. Ветеранов", "пр. Ветеранов, 183"]],
        services=[dict(n="Мужская стрижка", p=1600, d="60 мин"), dict(n="Стрижка машинкой", p=900, d="30 мин"),
                  dict(n="Стрижка + борода", p=2400, d="90 мин"), dict(n="Моделирование бороды", p=1000, d="45 мин"),
                  dict(n="Королевское бритьё", p=1500, d="45 мин"), dict(n="Детская стрижка", p=1100, d="до 12 лет"),
                  dict(n="Отец + сын", p=2600, d="две стрижки"), dict(n="Камуфляж седины", p=900, d="30 мин")],
        masters=[dict(n="Артём", r="топ-барбер", b=0), dict(n="Денис", r="барбер", b=0), dict(n="Илья", r="барбер", b=0),
                 dict(n="Максим", r="топ-барбер", b=1), dict(n="Руслан", r="барбер", b=1)],
        anyMaster="первый свободный на этом адресе",
        text=dict(svcLabel="Услуга", pickSvc="Выберите услугу", svcRow="Услуга", masterRow="Барбер", sumTitle="Ваша запись", send="Записаться",
                  hint="Оплата после стрижки", adminTitle="Запись", adminIcon="✂️", adminTo="администратору",
                  doneTitle="Вы записаны", doneText="ждём вас {when}. Напоминание придёт за 2 часа."))
))

# ───────────────────────── 29. Массаж от А до Я ─────────────────────────
SITES.append(dict(
    slug="massazh-ot-a-do-ya-site", send="Massazh-ot-A-do-YA.html",
    title="Массаж и СПА «Массаж от А до Я» · ул. Адмирала Черокова, 18к1",
    desc="Массаж и СПА «Массаж от А до Я» на улице Адмирала Черокова, 18к1: классический, лечебный, антицеллюлитный массаж и спа-программы. Онлайн-запись к мастеру.",
    fonts="https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap",
    vars={"bg": "#f6f4ef", "panel": "#ffffff", "panel-2": "#ece8de", "line": "#e2ddd0", "ink": "#252a26", "muted": "#767a72",
          "accent": "#3f7d5a", "accent-ink": "#ffffff", "accent-text": "#2f6a49", "tag-bg": "#dcebe1", "tag-ink": "#24583b",
          "font-display": '"Lora", Georgia, serif', "font-body": '"Manrope", "Segoe UI", Roboto, Arial, sans-serif',
          "font-num": '"Manrope", "Segoe UI", Arial, sans-serif', "h1-weight": "600", "em-style": "italic",
          "r-btn": "14px", "r-card": "20px", "shadow": "0 24px 48px -32px rgba(40,70,50,.35)", "color-scheme": "light"},
    name="Массаж от А до Я", mark="А", logo_sub="ул. Адмирала Черокова, 18к1",
    demo_note="Цены, мастера и часы примерные.", phone="+7 905 258-00-03",
    nav=[("prices", "Услуги"), ("course", "Курсы"), ("booking", "Запись"), ("contacts", "Контакты")],
    cta_short="Записаться", cta="Записаться онлайн",
    tag="Массаж и СПА на Черокова",
    h1="Массаж и СПА рядом с домом — <em>запись за минуту</em>",
    lead="Классический, лечебный и антицеллюлитный массаж, спа-программы на улице Адмирала Черокова, 18к1. Свободное время видно сразу, подтверждение придёт в Telegram.",
    hero_chips=["ул. Адмирала Черокова, 18к1", "<b>Ежедневно</b> 10:00–21:00", "Запись онлайн 24/7"],
    hero_card="""<div class="card az-hero">
      <small class="cap">Свободно сегодня</small>
      <div class="slot"><time>13:00</time><span><b>Классический массаж</b>60 мин · Елена</span></div>
      <div class="slot"><time>16:00</time><span><b>Массаж спины</b>40 мин · Ирина</span></div>
      <div class="slot"><time>19:00</time><span><b>Спа-программа «Детокс»</b>120 мин</span></div>
      <a class="btn" href="#booking" style="width:100%;margin-top:6px">Выбрать время</a>
    </div>""",
    perks=[("🗓", "Видно свободное время", "Выбираете массаж, мастера и окно сами — даже ночью, когда салон закрыт."),
           ("💬", "Напоминание накануне", "Бот напомнит о сеансе и даст перенести запись одной кнопкой."),
           ("🎟", "Курсы со скидкой", "Курс из 5 или 10 сеансов дешевле, а бот сам считает, сколько осталось.")],
    prices_h="Услуги и цены", prices_p="Время указано без подготовки. Масла и полотенца включены.",
    prices_html=plist([
        ("Массаж", [("Классический массаж", "60 мин", "2 800 ₽", 0), ("Массаж спины", "40 мин", "1 900 ₽", 0), ("Шейно-воротниковая зона", "30 мин", "1 300 ₽", 0), ("Лечебный массаж", "60 мин", "3 200 ₽", 0)]),
        ("Коррекция фигуры", [("Антицеллюлитный массаж", "45 мин", "2 500 ₽", 0), ("Лимфодренажный массаж", "60 мин", "3 000 ₽", 0)]),
        ("СПА", [("Спа-программа «Детокс»", "120 мин", "5 500 ₽", 0), ("Стоун-терапия", "90 мин", "4 000 ₽", 0)]),
    ]),
    extra_html=split("Курсы", "Курс из 5 или 10 сеансов",
        ["Курс дешевле разовых сеансов на 10–15%. После каждого визита бот присылает, сколько сеансов пройдено, и предлагает записаться на следующий — курс не бросают на середине.",
         "Подарочный сертификат на курс или сумму тоже можно оформить через бота."],
        tg("Массаж от А до Я", "А", "бот записи",
           [("🎟 Сеанс 4 из 10 пройден. Осталось 6. Записаться на следующий?", "20:10"),
            ("⏰ Напоминаю: <b>завтра, 18:00</b> массаж у Елены.<br>📍 ул. Адмирала Черокова, 18к1", "19:00")],
           ["📅 Записаться", "❌ Не смогу"]), alt=True, id_="course"),
    book_h="Онлайн-запись", book_p="Выберите массаж, мастера и время. Занятые окна зачёркнуты.",
    nojs_h="Запись на массаж", nojs_p="Напишите в WhatsApp, какой массаж и когда удобно — подберём мастера и подтвердим запись.",
    faq=[("Как подготовиться к массажу?", "Не есть плотно за час до сеанса. Всё остальное есть в кабинете."),
         ("Можно выбрать мастера?", "Да, или «любой свободный» — так быстрее найдётся окно."),
         ("Как перенести запись?", "Кнопкой в напоминании или в WhatsApp, пожалуйста, не позднее чем за 3 часа."),
         ("Как работает курс?", "Оплачиваете 5 или 10 сеансов со скидкой, бот считает пройденные и напоминает о следующих.")],
    contacts_html=contact_cards([("ул. Адмирала Черокова, 18к1", "Массаж и СПА")], [("+7 905 258-00-03", "Звонки и WhatsApp")], "Ежедневно, 10:00–21:00", "Последняя запись — за час до закрытия"),
    footer_addr="ул. Адмирала Черокова, 18к1",
    extra_css="""
.az-hero { max-width: 400px; margin-inline: auto; padding: 26px }
.az-hero .cap { display: block; color: var(--muted); font-size: 13px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; margin-bottom: 12px }
.az-hero .slot { display: grid; grid-template-columns: 70px minmax(0, 1fr); gap: 14px; align-items: center; padding: 12px 0; border-top: 1px dashed var(--line) }
.az-hero time { font: 700 20px/1 var(--font-num); color: var(--accent-text) }
.az-hero .slot span { color: var(--muted); font-size: 14px } .az-hero .slot b { display: block; color: var(--ink); font-size: 15.5px }
""",
    engine=dict(days=12, hours=HOURS_DAY,
        services=[dict(n="Классический массаж", p=2800, d="60 мин", c="m"), dict(n="Массаж спины", p=1900, d="40 мин", c="m"),
                  dict(n="Шейно-воротниковая зона", p=1300, d="30 мин", c="m"), dict(n="Лечебный массаж", p=3200, d="60 мин", c="m"),
                  dict(n="Антицеллюлитный массаж", p=2500, d="45 мин", c="m"), dict(n="Лимфодренажный массаж", p=3000, d="60 мин", c="m"),
                  dict(n="Спа-программа «Детокс»", p=5500, d="120 мин", c="spa"), dict(n="Стоун-терапия", p=4000, d="90 мин", c="spa")],
        masters=[dict(n="Елена", r="массажист", cats=["m", "spa"]), dict(n="Ирина", r="лечебный массаж", cats=["m"]),
                 dict(n="Ольга", r="спа-мастер", cats=["spa", "m"])],
        text=dict(svcLabel="Массаж", pickSvc="Выберите массаж", svcRow="Массаж", sumTitle="Ваша запись", send="Записаться",
                  hint="Оплата после сеанса", adminTitle="Запись", adminIcon="🌿", adminTo="администратору",
                  doneTitle="Вы записаны", doneText="ждём вас {when} на ул. Адмирала Черокова, 18к1. Напоминание придёт накануне."))
))

ONLY = set(sys.argv[1:])
for s in SITES:
    if ONLY and s["slug"] not in ONLY:
        continue
    for sv in s["engine"]["services"]:
        if sv.pop("frm", 0): sv["from"] = True
    s["vars"].setdefault("color-scheme", "light")
    d = os.path.join(ROOT, s["slug"]); os.makedirs(d, exist_ok=True)
    html = page(s)
    open(os.path.join(d, "index.html"), "w").write(html)
    os.makedirs(os.path.join(ROOT, "dlya-otpravki"), exist_ok=True)
    open(os.path.join(ROOT, "dlya-otpravki", s["send"]), "w").write(html)
    print(s["slug"], len(html.encode()))
