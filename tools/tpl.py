import json, re, html as H

CSS = r"""
:root {
%(vars)s
  --ok: #2fbf71;
}
* { box-sizing: border-box }
[hidden] { display: none !important }
html { scroll-behavior: smooth }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.6 var(--font-body); }
a { color: inherit }
button { font: inherit; color: inherit; cursor: pointer }
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
.wrap { max-width: 1120px; margin: 0 auto; padding-inline: 20px }
@media (max-width: 600px) { .wrap { padding-inline: 16px } }
.demo { background: var(--accent); color: var(--accent-ink); font-size: 13px; text-align: center; padding: 8px 16px; font-weight: 500 }

header.nav { position: sticky; top: 0; z-index: 20; background: color-mix(in srgb, var(--bg) 90%%, transparent); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line) }
header.nav .wrap { display: flex; align-items: center; gap: 28px; height: 68px }
.logo { display: flex; align-items: center; gap: 10px; text-decoration: none; min-width: 0 }
.logo .mark { width: 38px; height: 38px; border-radius: 11px; background: var(--accent); color: var(--accent-ink); display: grid; place-items: center; font: 700 17px/1 var(--font-display); flex: none }
.logo b { display: block; font: 700 16px/1.1 var(--font-display); white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.logo small { display: block; font-size: 12px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
nav.links { display: flex; gap: 24px; margin-left: auto; font-size: 15px }
nav.links a { text-decoration: none; color: var(--muted) }
nav.links a:hover { color: var(--ink) }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: var(--r-btn); padding: 14px 22px; font-weight: 700; text-decoration: none; text-align: center;
  background: var(--accent); color: var(--accent-ink); transition: transform .15s, filter .2s }
.btn:hover { filter: brightness(1.06) } .btn:active { transform: scale(.98) }
.btn.ghost { background: var(--panel-2); color: var(--ink); border: 1px solid var(--line) }
.btn.sm { padding: 10px 16px; font-size: 15px }
@media (max-width: 480px) { .logo small { display: none } .logo b { font-size: 15px } }
@media (max-width: 760px) { nav.links { display: none } header.nav .btn { margin-left: auto; flex: none } }

.hero { padding: 60px 0 76px }
.hero .wrap { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 48px; align-items: center }
@media (max-width: 860px) { .hero { padding: 34px 0 56px } .hero .wrap { grid-template-columns: minmax(0, 1fr); gap: 32px } }
.tag { display: inline-block; font: 600 12px/1 var(--font-body); letter-spacing: .1em; text-transform: uppercase; background: var(--tag-bg); color: var(--tag-ink); padding: 7px 10px; border-radius: 6px }
.hero h1 { font: var(--h1-weight) clamp(34px, 5.4vw, 64px)/1.04 var(--font-display); margin: 20px 0 18px; letter-spacing: -.01em; text-wrap: balance }
.hero h1 em { font-style: var(--em-style); color: var(--accent-text) }
.hero p.lead { font-size: 18px; color: var(--muted); max-width: 46ch; margin: 0 0 28px }
.hero .ctas { display: flex; flex-wrap: wrap; gap: 12px }
.chips-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 26px }
.chips-row span { border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; font-size: 14px; color: var(--muted) }
.chips-row span b { color: var(--ink) }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: var(--r-card); padding: 22px; box-shadow: var(--shadow) }

section { padding: 84px 0 }
@media (max-width: 600px) { section { padding: 58px 0 } }
.alt { background: var(--panel) }
.alt .card, .alt .perk, .alt details, .alt .contacts > div, .alt .form, .alt .summary { background: var(--bg) }
.sec-head { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 32px; flex-wrap: wrap }
.sec-head h2 { font: var(--h1-weight) clamp(26px, 3.6vw, 42px)/1.12 var(--font-display); margin: 14px 0 0 }
.sec-head p { margin: 0; color: var(--muted); max-width: 44ch }

.perks { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px }
@media (max-width: 860px) { .perks { grid-template-columns: minmax(0, 1fr) } }
.perk { background: var(--panel); border: 1px solid var(--line); border-radius: var(--r-card); padding: 24px }
.perk .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; font-size: 22px; background: var(--panel-2); margin-bottom: 14px }
.perk b { display: block; font: 700 19px/1.25 var(--font-display); margin-bottom: 8px }
.perk p { margin: 0; color: var(--muted); font-size: 15px }

.plist { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px }
@media (max-width: 860px) { .plist { grid-template-columns: minmax(0, 1fr) } }
.plist h3 { font: 700 18px/1.2 var(--font-display); margin: 0 0 8px }
.prow { display: flex; justify-content: space-between; gap: 16px; padding: 11px 0; border-top: 1px dashed var(--line) }
.prow span small { display: block; color: var(--muted); font-size: 13px }
.prow b { white-space: nowrap; color: var(--accent-text); font-family: var(--font-num) }
.ptable-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: var(--r-card); background: var(--bg) }
table.pt { width: 100%%; border-collapse: collapse; min-width: 480px }
.pt th, .pt td { padding: 13px 16px; text-align: right; border-top: 1px solid var(--line); white-space: nowrap }
.pt thead th { border-top: 0; font-size: 13px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em }
.pt th:first-child, .pt td:first-child { text-align: left }
.pt td { font-family: var(--font-num); font-weight: 500 }
.pt td.r { font-weight: 700; color: var(--accent-text) }
.note { color: var(--muted); font-size: 14px; margin: 14px 0 0 }

.split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 48px; align-items: center }
@media (max-width: 860px) { .split { grid-template-columns: minmax(0, 1fr); gap: 28px } }
.split h2 { font: var(--h1-weight) clamp(26px, 3.6vw, 42px)/1.12 var(--font-display); margin: 14px 0 14px }
.split p { color: var(--muted); margin: 0 0 12px; max-width: 46ch }
.tg { background: #17212b; color: #e9eef3; border-radius: 22px; padding: 16px; border: 1px solid #263240; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif }
.tg .who { display: flex; align-items: center; gap: 10px; padding: 0 2px 12px; border-bottom: 1px solid #263240; margin-bottom: 12px; font-size: 14px }
.tg .who i { width: 34px; height: 34px; border-radius: 50%%; background: var(--accent); color: var(--accent-ink); display: grid; place-items: center; font: 700 14px/1 var(--font-display); font-style: normal }
.tg .who small { display: block; color: #6c7883; font-size: 12px }
.tg .msg { background: #182533; border: 1px solid #263240; border-radius: 16px 16px 16px 4px; padding: 11px 13px; font-size: 14.5px; margin-bottom: 8px; line-height: 1.5 }
.tg .msg time { display: block; text-align: right; font-size: 11px; color: #6c7883 }
.tg .kb { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px }
.tg .kb span { text-align: center; padding: 9px; border-radius: 10px; background: #22303f; color: #6ab3f3; font-size: 14px; font-weight: 600 }

.bk { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, .8fr); gap: 24px; align-items: start }
@media (max-width: 900px) { .bk { grid-template-columns: minmax(0, 1fr) } }
.form { background: var(--bg); border: 1px solid var(--line); border-radius: var(--r-card); padding: 24px }
@media (max-width: 600px) { .form { padding: 18px } }
.field { margin-bottom: 20px }
.field > .lbl, .field > label { display: block; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 10px }
.chips { display: flex; flex-wrap: wrap; gap: 8px }
.chips button { border: 1.5px solid var(--line); background: var(--panel); border-radius: 12px; padding: 9px 13px; font-size: 15px; text-align: left; line-height: 1.35 }
.chips button small { display: block; font-size: 12px; color: var(--muted) }
.chips button[aria-pressed="true"] { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 14%%, var(--panel)) }
.chips button:disabled { opacity: .3; text-decoration: line-through; cursor: default }
.chips.mono button { font-family: var(--font-num); font-weight: 600 }
.form input, .form textarea { width: 100%%; background: var(--panel); border: 1.5px solid var(--line); color: var(--ink); border-radius: 12px; padding: 13px 14px; font: inherit }
.form textarea { min-height: 80px; resize: vertical }
.form input::placeholder, .form textarea::placeholder { color: var(--muted); opacity: .7 }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px }
@media (max-width: 600px) { .two { grid-template-columns: minmax(0, 1fr) } }
.summary { position: sticky; top: 88px; background: var(--bg); border: 1px solid var(--line); border-radius: var(--r-card); padding: 24px }
.summary h3 { font: 700 20px/1.2 var(--font-display); margin: 0 0 14px }
.summary dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 8px 16px; margin: 0 0 16px; font-size: 15px }
.summary dt { color: var(--muted) } .summary dd { margin: 0 }
.summary .total { display: flex; justify-content: space-between; align-items: baseline; border-top: 1px dashed var(--line); padding-top: 14px; margin-bottom: 16px }
.summary .total b { font: 700 30px/1 var(--font-num); color: var(--accent-text) }
.summary .btn { width: 100%% }
.summary .btn:disabled { opacity: .4; cursor: default }
.summary .hint { display: block; text-align: center; margin-top: 10px; font-size: 13px; color: var(--muted) }
.done { text-align: center }
.done .ok { width: 60px; height: 60px; border-radius: 50%%; background: var(--ok); color: #fff; display: grid; place-items: center; margin: 0 auto 12px; font-size: 28px; font-weight: 700 }
.done p { color: var(--muted); margin: 0 0 12px; font-size: 15px }
.admin { margin-top: 16px; background: #17212b; color: #e9eef3; border-radius: 16px; padding: 14px; text-align: left; font-size: 14px; white-space: pre-line }
.admin small { display: block; color: #6c7883; margin-bottom: 6px; letter-spacing: .1em; text-transform: uppercase; font-size: 10px }
html:not(.js) #bookForm { display: none }
html:not(.js) .bk { grid-template-columns: minmax(0, 1fr) }
html.js .nojs { display: none }

details { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 0 18px }
details + details { margin-top: 8px }
summary { cursor: pointer; padding: 15px 0; font-weight: 600; list-style: none; display: flex; justify-content: space-between; gap: 10px }
summary::-webkit-details-marker { display: none }
summary::after { content: "+"; color: var(--accent-text); font: 700 18px/1 var(--font-num) }
details[open] summary::after { content: "−" }
details p { margin: 0 0 16px; color: var(--muted) }

.contacts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px }
@media (max-width: 860px) { .contacts { grid-template-columns: minmax(0, 1fr) } }
.contacts > div { background: var(--panel); border: 1px solid var(--line); border-radius: var(--r-card); padding: 22px }
.contacts small { font-size: 13px; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; font-weight: 600 }
.contacts b { display: block; font: 700 19px/1.3 var(--font-display); margin: 8px 0 6px }
.contacts p { margin: 0 0 14px; color: var(--muted); font-size: 15px }
footer { border-top: 1px solid var(--line); padding: 26px 0 40px; color: var(--muted); font-size: 14px }
footer .wrap { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap }
%(extra_css)s
"""

ENGINE = r"""
const C = __CONFIG__;
const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString("ru-RU") + " ₽";
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const digits = s => (s || "").replace(/\D/g, "");
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const round50 = n => Math.round(n / 50) * 50;
const dayName = d => new Date(d + "T12:00").toLocaleDateString("ru-RU", { weekday: "short", day: "numeric", month: "long" });

const st = { branch: 0, opt: 0, svc: null, master: -1, day: null, time: null, sent: false };
// примерная занятость: часть слотов зачёркнута, чтобы календарь выглядел живым
const busy = new Set();
for (let i = 0; i < C.days; i++) { const d = new Date(); d.setDate(d.getDate() + i); C.hours.forEach((h, j) => { if ((j * 7 + i * 3 + 1) % 5 < 2) busy.add(`${iso(d)}_${h}`); }); }
const slotKey = h => `${st.day}_${h}`;
const svcList = () => C.services;
const svcPrice = s => round50(s.p * (C.opts ? C.opts.list[st.opt][1] : 1));
const masters = () => (C.masters || []).filter(m => (m.b === undefined || m.b === st.branch) && (!st.svc || !m.cats || m.cats.includes(svcList()[st.svc - 1].c)));
const priceText = s => s.p === 0 ? "бесплатно" : (s.from ? "от " : "") + fmt(svcPrice(s));
const closed = d => (C.closedDays || []).includes(d.getDay());

function chip(html, pressed, onClick, disabled) {
  const b = document.createElement("button");
  b.type = "button"; b.innerHTML = html; b.setAttribute("aria-pressed", pressed ? "true" : "false"); b.disabled = !!disabled;
  b.onclick = () => { onClick(); render(); };
  return b;
}
function render() {
  if (C.branches) $("fBranch").replaceChildren(...C.branches.map((b, i) => chip(`${esc(b[0])}<small>${esc(b[1])}</small>`, st.branch === i, () => { st.branch = i; st.master = -1; st.time = null; })));
  if (C.opts) $("fOpt").replaceChildren(...C.opts.list.map((o, i) => chip(esc(o[0]), st.opt === i, () => { st.opt = i; })));
  $("fService").replaceChildren(...svcList().map((s, i) => chip(`${esc(s.n)} · ${priceText(s)}${s.d ? `<small>${esc(s.d)}</small>` : ""}`, st.svc === i + 1, () => { st.svc = i + 1; if (st.master >= 0 && !masters().includes(C.masters[st.master])) st.master = -1; })));
  if (C.masters) {
    const list = masters();
    $("fMaster").replaceChildren(chip(`Любой свободный<small>${esc(C.anyMaster || "подберём сами")}</small>`, st.master < 0, () => { st.master = -1; }),
      ...list.map(m => { const i = C.masters.indexOf(m); return chip(`${esc(m.n)}<small>${esc(m.r)}</small>`, st.master === i, () => { st.master = i; st.time = null; }); }));
  }
  const now = new Date(), days = [];
  for (let i = 0; i < C.days; i++) { const d = new Date(); d.setDate(d.getDate() + i); days.push(d); }
  const todayDone = !C.hours.some(h => +h.slice(0, 2) > now.getHours());
  if (!st.day) { const first = days.find((d, i) => !closed(d) && !(i === 0 && todayDone)); st.day = iso(first); }
  $("fDay").replaceChildren(...days.map((d, i) => chip(`${d.getDate()}<small>${i === 0 ? "сегодня" : i === 1 ? "завтра" : d.toLocaleDateString("ru-RU", { weekday: "short" })}</small>`,
    st.day === iso(d), () => { st.day = iso(d); st.time = null; }, (i === 0 && todayDone) || closed(d))));
  const shift = (st.master + 1) + st.branch;
  $("fTime").replaceChildren(...C.hours.map((h, j) => chip(h, st.time === h, () => { st.time = h; },
    busy.has(`${st.day}_${C.hours[(j + shift) % C.hours.length]}`) || (st.day === iso(now) && +h.slice(0, 2) <= now.getHours()))));
  summary();
}
function summary() {
  if (st.sent) return;
  const s = st.svc ? svcList()[st.svc - 1] : null;
  const ok = { svc: !!s, time: !!st.time, name: $("fName").value.trim().length > 1, phone: digits($("fPhone").value).length >= 10 };
  const label = !ok.svc ? C.text.pickSvc : !ok.time ? "Выберите время" : !ok.name ? "Укажите имя" : !ok.phone ? "Укажите телефон" : C.text.send;
  const when = st.time ? `${dayName(st.day)}, ${st.time}` : "выберите время";
  const rows = [];
  if (C.branches) rows.push(["Адрес", C.branches[st.branch][1]]);
  if (C.opts) rows.push([C.opts.label, C.opts.list[st.opt][0]]);
  rows.push([C.text.svcRow, s ? s.n : "не выбрано"]);
  if (C.masters) rows.push([C.text.masterRow || "Мастер", st.master < 0 ? "любой свободный" : C.masters[st.master].n]);
  rows.push(["Когда", when]);
  $("summary").innerHTML = `<h3>${C.text.sumTitle}</h3>
    <dl>${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${esc(r[1])}</dd>`).join("")}</dl>
    <div class="total"><span>${s && s.from ? "Стоимость от" : "Стоимость"}</span><b>${s ? (s.p === 0 ? "0 ₽" : fmt(svcPrice(s))) : "—"}</b></div>
    <button class="btn" type="button" id="send" ${Object.values(ok).every(Boolean) ? "" : "disabled"}>${label}</button>
    <span class="hint">${C.text.hint}</span>`;
  $("send").onclick = send;
}
["fName", "fPhone"].forEach(id => $(id).addEventListener("input", summary));
function send() {
  const s = svcList()[st.svc - 1];
  const no = String(100 + Math.floor(Math.random() * 80));
  const when = `${dayName(st.day)}, ${st.time}`;
  const name = $("fName").value.trim(), phone = $("fPhone").value.trim(), note = $("fNote") ? $("fNote").value.trim() : "";
  busy.add(`${st.day}_${st.time}`);
  st.sent = true;
  const lines = [`🆕 ${C.text.adminTitle} № ${no}`];
  if (C.branches) lines.push(`📍 ${C.branches[st.branch][1]}`);
  lines.push(`${C.text.adminIcon} ${s.n}${C.opts ? ", " + C.opts.list[st.opt][0].toLowerCase() : ""} · ${priceText(s)}`);
  if (C.masters) lines.push(`👤 ${C.text.masterRow || "Мастер"}: ${st.master < 0 ? "любой свободный" : C.masters[st.master].n}`);
  lines.push(`🗓 ${when}`, `🙋 ${name}, ${phone}`);
  if (note) lines.push(`💬 ${note}`);
  $("summary").innerHTML = `<div class="done"><div class="ok">✓</div><h3>${C.text.doneTitle} · № ${no}</h3>
    <p>${esc(name)}, ${esc(C.text.doneText.replace("{when}", when))}</p>
    <div class="admin"><small>Так заявка приходит ${esc(C.text.adminTo)} в Telegram</small>${esc(lines.join("\n"))}\n\n[ ✅ Подтвердить ]  [ ✖ Отказать ]</div>
    <button class="btn ghost sm" type="button" id="again" style="margin-top:14px">Записаться ещё</button></div>`;
  $("again").onclick = () => { st.sent = false; st.time = null; render(); };
}
document.querySelectorAll("[data-svc]").forEach(a => a.addEventListener("click", () => { st.svc = +a.dataset.svc; st.time = null; render(); }));
render();
"""

def page(c):
    wa = "https://wa.me/" + re.sub(r"\D", "", c["phone"])
    vars_ = "\n".join(f"  --{k}: {v};" for k, v in c["vars"].items() if k != "color-scheme") + f"\n  color-scheme: {c['vars']['color-scheme']};"
    css = CSS % {"vars": vars_, "extra_css": c.get("extra_css", "")}
    cfg = json.dumps(c["engine"], ensure_ascii=False)
    js = ENGINE.replace("__CONFIG__", cfg)
    nav = "".join(f'<a href="#{a}">{t}</a>' for a, t in c["nav"])
    chips = "".join(f"<span>{x}</span>" for x in c["hero_chips"])
    perks = "".join(f'<div class="perk"><div class="ico">{i}</div><b>{t}</b><p>{p}</p></div>' for i, t, p in c["perks"])
    faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in c["faq"])
    e = c["engine"]
    fields = []
    if e.get("branches"): fields.append('<div class="field"><span class="lbl">Филиал</span><div class="chips" id="fBranch"></div></div>')
    if e.get("opts"): fields.append(f'<div class="field"><span class="lbl">{e["opts"]["label"]}</span><div class="chips" id="fOpt"></div></div>')
    fields.append(f'<div class="field"><span class="lbl">{e["text"]["svcLabel"]}</span><div class="chips" id="fService"></div></div>')
    if e.get("masters"): fields.append(f'<div class="field"><span class="lbl">{e["text"].get("masterRow","Мастер")}</span><div class="chips" id="fMaster"></div></div>')
    fields.append(f'<div class="field"><span class="lbl">{e["text"].get("dayLabel","День")}</span><div class="chips mono" id="fDay"></div></div>')
    fields.append('<div class="field"><span class="lbl">Время</span><div class="chips mono" id="fTime"></div></div>')
    fields.append('<div class="field two"><div><label for="fName" class="lbl" style="display:block;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:10px">Имя</label><input id="fName" autocomplete="name" placeholder="Как к вам обращаться"></div>'
                  '<div><label for="fPhone" style="display:block;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:10px">Телефон</label><input id="fPhone" type="tel" autocomplete="tel" placeholder="+7 ___ ___-__-__"></div></div>')
    if e["text"].get("noteLabel"):
        fields.append(f'<div class="field"><label for="fNote">{e["text"]["noteLabel"]}</label><textarea id="fNote" placeholder="{e["text"]["notePh"]}"></textarea></div>')
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c["title"]}</title>
<meta name="description" content="{H.escape(c["desc"])}">
<script>document.documentElement.classList.add("js")</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="{c["fonts"]}">
<style>{css}</style>
</head>
<body>
<div class="demo"><b>Демо-версия сайта</b> для {c["name"] if "«" in c["name"] else "«" + c["name"] + "»"}. {c["demo_note"]}</div>
<header class="nav"><div class="wrap">
  <a class="logo" href="#top"><span class="mark">{c["mark"]}</span><span><b>{c["name"]}</b><small>{c["logo_sub"]}</small></span></a>
  <nav class="links">{nav}</nav>
  <a class="btn sm" href="#booking">{c["cta_short"]}</a>
</div></header>
<main id="top">
  <section class="hero"><div class="wrap">
    <div>
      <span class="tag">{c["tag"]}</span>
      <h1>{c["h1"]}</h1>
      <p class="lead">{c["lead"]}</p>
      <div class="ctas"><a class="btn" href="#booking">{c["cta"]}</a><a class="btn ghost" href="{wa}" target="_blank" rel="noopener">Написать в WhatsApp</a></div>
      <div class="chips-row">{chips}</div>
    </div>
    <div>{c["hero_card"]}</div>
  </div></section>
  <section id="perks" style="padding-top:0"><div class="wrap"><div class="perks">{perks}</div></div></section>
  <section class="alt" id="prices"><div class="wrap">
    <div class="sec-head"><div><span class="tag">Цены</span><h2>{c["prices_h"]}</h2></div><p>{c["prices_p"]}</p></div>
    {c["prices_html"]}
  </div></section>
  {c["extra_html"]}
  <section class="alt" id="booking"><div class="wrap">
    <div class="sec-head"><div><span class="tag">Онлайн-запись</span><h2>{c["book_h"]}</h2></div><p>{c["book_p"]}</p></div>
    <div class="bk">
      <form class="form" id="bookForm" onsubmit="return false">{"".join(fields)}</form>
      <aside class="summary" id="summary" aria-live="polite"><h3>{c["nojs_h"]}</h3><p style="color:var(--muted);margin:0 0 18px">{c["nojs_p"]}</p><a class="btn" href="{wa}" style="width:100%">Написать в WhatsApp</a><span class="hint">{c["phone"]}</span></aside>
    </div>
  </div></section>
  <section id="faq"><div class="wrap">
    <div class="sec-head"><div><span class="tag">Вопросы</span><h2>Частые вопросы</h2></div></div>
    {faq}
  </div></section>
  <section id="contacts" style="padding-top:0"><div class="wrap">
    <div class="sec-head"><div><span class="tag">Контакты</span><h2>Как нас найти</h2></div></div>
    <div class="contacts">{c["contacts_html"]}</div>
  </div></section>
</main>
<footer><div class="wrap"><span>© {c["name"]} · {c["footer_addr"]}</span><span>Демо-версия сайта. {c["demo_note"]}</span></div></footer>
<script>{js}{c.get("extra_js", "")}</script>
</body>
</html>
"""

def contact_cards(addrs, phones, hours, hours_note):
    """addrs: [(addr, note)], phones: [(phone, note)]"""
    out = []
    for a, n in addrs:
        q = "Санкт-Петербург, " + a
        out.append(f'<div><small>Адрес</small><b>{a}</b><p>{n}</p><a class="btn ghost sm" href="https://yandex.ru/maps/?text={q.replace(" ", "%20")}" target="_blank" rel="noopener">Открыть на карте</a></div>')
    for p, n in phones:
        out.append(f'<div><small>Телефон</small><b>{p}</b><p>{n}</p><a class="btn ghost sm" href="https://wa.me/{re.sub(r"[^0-9]", "", p)}" target="_blank" rel="noopener">Написать в WhatsApp</a></div>')
    out.append(f'<div><small>Часы работы</small><b>{hours}</b><p>{hours_note}</p><a class="btn ghost sm" href="#booking">Записаться онлайн</a></div>')
    return "".join(out)

def plist(groups, book=True):
    """groups: [(title, [(name, sub, price_text, svc_index or None)])]"""
    out = []
    for t, rows in groups:
        r = "".join(f'<div class="prow"><span>{n}{f"<small>{s}</small>" if s else ""}</span><b>{p}</b></div>' for n, s, p, _ in rows)
        out.append(f'<div class="card"><h3>{t}</h3>{r}</div>')
    return f'<div class="plist">{"".join(out)}</div>'
