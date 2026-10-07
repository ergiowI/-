"""Шаблоны демо Telegram-бота (demo.html: мини-приложение в рамке телефона + чат владельца) и самого бота (bot.py)."""
import json, re, pprint

DEMO_CSS = r"""
:root {
__VARS__
  --ok: #2fbf71;
}
* { box-sizing: border-box }
[hidden] { display: none !important }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 var(--font-body); }
button { font: inherit; color: inherit; }
button:focus-visible, a:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }

.demo-flag { background: var(--accent); color: var(--accent-ink); font-size: 13px; text-align: center; padding: 8px 16px; font-weight: 500 }
.shell { max-width: 1080px; margin: 0 auto; padding: 28px 16px 48px; display: grid; gap: 24px; }
.intro .tag { display: inline-block; font: 600 11px/1 var(--font-body); letter-spacing: .1em; text-transform: uppercase;
  background: var(--accent); color: var(--accent-ink); padding: 6px 8px; border-radius: 4px; margin-bottom: 12px; }
.intro h1 { font: var(--h-weight) clamp(20px, 3.2vw, 30px)/1.15 var(--font-display); margin: 0 0 8px; text-wrap: balance; }
.intro p { margin: 0; color: var(--muted); max-width: 66ch; }
.stage { display: grid; grid-template-columns: 400px minmax(0, 1fr); gap: 32px; align-items: start; }
@media (max-width: 820px) { .stage { grid-template-columns: minmax(0, 1fr); } }
.phone { width: 100%; max-width: 400px; margin-inline: auto; border-radius: 36px; padding: 10px; background: #000;
  border: 1px solid var(--line); box-shadow: 0 30px 60px rgba(0,0,0,.35), 0 0 0 6px var(--frame); }
.screen { position: relative; height: 760px; border-radius: 28px; overflow: hidden; background: var(--bg); display: flex; flex-direction: column; }
@media (max-width: 820px) { .screen { height: 82vh; min-height: 600px } }
.tgbar { flex: none; display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: var(--panel); border-bottom: 1px solid var(--line); font-size: 14px; }
.tgbar b { font-weight: 600 } .tgbar span { color: var(--muted) }

body.tg .intro, body.tg .side, body.tg .tgbar, body.tg .demo-flag { display: none }
body.tg .shell { padding: 0; max-width: none }
body.tg .stage { display: block }
body.tg .phone { padding: 0; border: 0; border-radius: 0; box-shadow: none; max-width: none; background: none }
body.tg .screen { height: 100vh; height: var(--tg-viewport-stable-height, 100vh); border-radius: 0 }

.app { flex: 1; overflow-y: auto; padding: 0 16px 170px; scroll-behavior: smooth; }
.app.notbook { padding-bottom: 90px; }
.hero { display: flex; gap: 14px; align-items: center; padding: 18px 0 8px; }
.hero .ava { width: 60px; height: 60px; flex: none; border-radius: 18px; background: var(--accent); color: var(--accent-ink); display: grid; place-items: center; font: 700 26px/1 var(--font-display); animation: pop .6s cubic-bezier(.2,.8,.2,1) both }
@keyframes pop { from { transform: scale(.6); opacity: 0 } to { transform: none; opacity: 1 } }
.hero h2 { font: var(--h-weight) 18px/1.15 var(--font-display); margin: 0 0 4px; }
.hero p { margin: 0; color: var(--muted); font-size: 13px; }
.promise { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 4px; }
.promise span { font-size: 12px; padding: 4px 8px; border-radius: 999px; background: var(--panel-2); color: var(--muted); }
.promise span b { color: var(--accent-text); font-weight: 600 }

.step { margin-top: 22px; }
.step h3 { display: flex; align-items: baseline; gap: 8px; font: 600 13px/1.2 var(--font-body); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin: 0 0 10px; }
.step h3 i { font: 700 11px/1 var(--font-num); font-style: normal; color: var(--accent-ink); background: var(--accent); border-radius: 4px; padding: 3px 5px; }
.opt { background: var(--panel); border: 1.5px solid var(--line); border-radius: 14px; padding: 10px 12px; cursor: pointer; text-align: left; transition: border-color .15s, background .15s, transform .1s; }
.opt:active { transform: scale(.97) }
.opt[aria-pressed="true"] { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--panel)); }
.opt:disabled { opacity: .3; text-decoration: line-through; cursor: not-allowed; }
.grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.grid3 .opt, .grid2 .opt { font-size: 14px; overflow-wrap: anywhere; }
.opt small { display: block; color: var(--muted); font-size: 12px }
.services { display: grid; gap: 8px; }
.services .opt { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 12px; align-items: center; padding: 12px 14px; }
.services .opt b { font-weight: 600 }
.services .opt small { grid-column: 1; }
.services .opt .p { grid-row: 1 / span 2; grid-column: 2; font: 700 15px/1 var(--font-num); white-space: nowrap }
.days { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
.days .opt { display: grid; justify-items: center; gap: 2px; padding: 8px 0; }
.days .opt small { font-size: 11px; text-transform: uppercase; letter-spacing: .05em }
.days .opt b { font: 700 17px/1 var(--font-num); }
.times { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; margin-top: 10px; }
.times .opt { text-align: center; font: 500 14px/1 var(--font-num); padding: 11px 0; }
.hint { color: var(--muted); font-size: 12px; margin: 8px 0 0 }

.bar { position: absolute; left: 0; right: 0; bottom: 62px; padding: 12px 16px; background: linear-gradient(to top, var(--bg) 70%, transparent);
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; }
.sum small { display: block; color: var(--muted); font-size: 12px; }
.sum b { font: 700 22px/1.1 var(--font-num); font-variant-numeric: tabular-nums; white-space: nowrap }
.go { background: var(--accent); color: var(--accent-ink); border: 0; border-radius: 14px; padding: 15px 18px; font-weight: 700; cursor: pointer; transition: opacity .2s, transform .1s; }
.go:active { transform: scale(.97) }
.go:disabled { opacity: .4; cursor: default }
body.tg .go { display: none }

.tabs { position: absolute; left: 0; right: 0; bottom: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  background: var(--panel); border-top: 1px solid var(--line); padding: 6px 4px calc(6px + env(safe-area-inset-bottom, 0px)); z-index: 2; }
.tabs button { background: none; border: 0; display: grid; justify-items: center; gap: 3px; padding: 6px 0; font-size: 11px; color: var(--muted); cursor: pointer; position: relative; }
.tabs button svg { width: 22px; height: 22px; }
.tabs button[aria-selected="true"] { color: var(--accent-text); }
.tabs .badge { position: absolute; top: 2px; left: calc(50% + 6px); min-width: 16px; height: 16px; border-radius: 8px; background: var(--accent); color: var(--accent-ink); font: 700 10px/16px var(--font-num); padding: 0 4px; }

.done { position: absolute; inset: 0; background: var(--bg); padding: 24px 16px; overflow-y: auto; display: grid; align-content: start; gap: 16px; animation: up .45s cubic-bezier(.2,.8,.2,1); z-index: 3 }
@keyframes up { from { transform: translateY(30px); opacity: 0 } to { transform: none; opacity: 1 } }
.check { width: 56px; height: 56px; border-radius: 50%; background: var(--ok); display: grid; place-items: center; margin: 8px auto 0; color: #fff; font-size: 28px; font-weight: 700 }
.done h2 { text-align: center; font: var(--h-weight) 20px/1.2 var(--font-display); margin: 0 }
.ticket { background: var(--panel); border-radius: 16px; border: 1px solid var(--line) }
.ticket .top, .ticket .bottom { padding: 16px 18px; }
.ticket .top { border-bottom: 2px dashed var(--line); }
.ticket .no { font: 500 12px/1 var(--font-num); color: var(--muted); letter-spacing: .08em }
.ticket .when { font: var(--h-weight) 21px/1.2 var(--font-display); margin: 8px 0 2px }
.ticket dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 6px 14px; margin: 0; font-size: 14px }
.ticket dt { color: var(--muted) } .ticket dd { margin: 0; }
.ticket .total { display: flex; justify-content: space-between; align-items: baseline; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--line); }
.ticket .total b { font: 700 22px/1 var(--font-num); color: var(--accent-text) }
.ticket.cancelled { opacity: .45 }
.ticket .acts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
.ticket .acts a, .ticket .acts button { text-align: center; text-decoration: none; background: var(--panel-2); border: 1px solid var(--line); border-radius: 10px; padding: 10px; font-size: 13px; color: var(--ink); cursor: pointer; }
.again { background: var(--panel-2); border: 1px solid var(--line); border-radius: 12px; padding: 12px; cursor: pointer; }
.cta2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.extra-line { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; font-size: 14px }

.pagehead { padding: 20px 0 6px; }
.pagehead h2 { font: var(--h-weight) 20px/1.15 var(--font-display); margin: 0 0 4px; }
.pagehead p { margin: 0; color: var(--muted); font-size: 13px; }
.list { display: grid; gap: 1px; background: var(--line); border-radius: 14px; overflow: hidden; margin-top: 10px; }
.list > div { background: var(--panel); display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 12px; padding: 12px 14px; align-items: center; }
.list b { font-weight: 600 } .list small { color: var(--muted); grid-column: 1; font-size: 12px }
.list .p { grid-row: 1 / span 2; grid-column: 2; font: 700 14px/1 var(--font-num); white-space: nowrap }
.sub { font: 600 13px/1.2 var(--font-body); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin: 22px 0 0; }
.mine { display: grid; gap: 14px; margin-top: 14px; }
.empty-state { text-align: center; padding: 40px 10px; color: var(--muted); display: grid; gap: 14px; justify-items: center; }
.contact { display: grid; gap: 10px; margin-top: 14px; }
.contact .row { background: var(--panel); border-radius: 14px; padding: 14px; display: grid; grid-template-columns: 36px minmax(0, 1fr); gap: 12px; align-items: center; }
.contact .row > span { width: 36px; height: 36px; border-radius: 10px; background: var(--panel-2); display: grid; place-items: center; }
.contact .row b { display: block; font-weight: 600 } .contact .row small { color: var(--muted) }
.cta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.cta a { text-align: center; text-decoration: none; border-radius: 12px; padding: 13px; font-weight: 600; }
.cta a.y { background: var(--accent); color: var(--accent-ink) }
.cta a.g { background: var(--panel-2); color: var(--ink); border: 1px solid var(--line) }
details { background: var(--panel); border-radius: 12px; padding: 0 14px; }
details + details { margin-top: 6px }
summary { cursor: pointer; padding: 13px 0; font-weight: 500; list-style: none; display: flex; justify-content: space-between; gap: 10px; }
summary::-webkit-details-marker { display: none }
summary::after { content: "+"; color: var(--accent-text); font: 700 18px/1 var(--font-num); }
details[open] summary::after { content: "−"; }
details p { margin: 0 0 14px; color: var(--muted); font-size: 14px; }

.side { display: grid; gap: 18px; min-width: 0; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 16px 18px; }
.card > h2 { font: var(--h-weight) 15px/1.3 var(--font-display); margin: 0 0 12px; }
.tgchat { background: #17212b; color: #e9eef3; border-radius: 12px; padding: 12px; display: grid; align-content: end; gap: 8px; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif }
#owner { min-height: 170px }
.tgchat .empty { color: #6c7883; font-size: 14px; text-align: center; align-self: center; margin: 0 }
.bubble { background: #182533; border: 1px solid #263240; border-radius: 14px 14px 14px 4px; padding: 10px 12px; max-width: 100%; animation: up .4s cubic-bezier(.2,.8,.2,1); white-space: pre-line; overflow-wrap: anywhere; font-size: 14px; }
.bubble b { font-weight: 700 }
.bubble .money { color: #ffd479; }
.bubble time { display: block; text-align: right; font-size: 11px; color: #6c7883 }
.ikb { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
.ikb span { text-align: center; font-size: 13px; padding: 8px; border-radius: 10px; background: #22303f; color: #6ab3f3; font-weight: 600 }
.feat { margin: 0; padding: 0; list-style: none; display: grid; gap: 12px; }
.feat li { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 10px; }
.feat li span:first-child { width: 28px; height: 28px; border-radius: 8px; background: var(--panel-2); display: grid; place-items: center; font-size: 14px; }
.feat b { display: block; font-weight: 600 } .feat small { color: var(--muted); font-size: 13px }
.note { color: var(--muted); font-size: 12px; margin: 10px 0 0 }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important } }
"""

DEMO_JS = r"""
const C = __CONFIG__;
const tg = window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData !== undefined && window.Telegram.WebApp.platform !== "unknown" ? window.Telegram.WebApp : null;
if (tg) { document.body.classList.add("tg"); tg.ready(); tg.expand(); try { tg.setHeaderColor(C.bg); tg.setBackgroundColor(C.bg); } catch (e) {} }
const haptic = () => { try { tg && tg.HapticFeedback.selectionChanged(); } catch (e) {} };
const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString("ru-RU") + " ₽";
const round50 = n => Math.round(n / 50) * 50;
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const dayLabel = d => new Date(d + "T12:00").toLocaleDateString("ru-RU", { day: "numeric", month: "long", weekday: "short" });

// занятые слоты: бот передаёт ?busy=b0_2026-10-03_11:00,... ; в демо — правдоподобный узор
const busy = new Set();
const qs = new URLSearchParams(location.search);
if (qs.get("busy")) qs.get("busy").split(",").forEach(s => busy.add(s));
else for (let i = 0; i < 7; i++) { const d = new Date(); d.setDate(d.getDate() + i);
  (C.branches || [0]).forEach((_, b) => C.hours.forEach((h, j) => { if ((j * 7 + i * 3 + b * 2 + 1) % 5 < 2) busy.add(`b${b}_${iso(d)}_${h}`); })); }

const st = { branch: 0, opt: 0, svc: null, master: -1, day: null, time: null };
const svc = () => st.svc === null ? null : C.services[st.svc];
const price = s => round50(s.p * (C.opts ? C.opts.list[st.opt][1] : 1));
const priceText = s => s.p === 0 ? "бесплатно" : (s.from ? "от " : "") + fmt(price(s));
const masters = () => (C.masters || []).filter(m => (m.b === undefined || m.b === st.branch) && (!svc() || !m.cats || m.cats.includes(svc().c)));
const closed = d => (C.closedDays || []).includes(d.getDay());

function btn(cls, html, pressed, onClick, disabled) {
  const b = document.createElement("button");
  b.type = "button"; b.className = "opt " + cls; b.innerHTML = html; b.disabled = !!disabled;
  b.setAttribute("aria-pressed", pressed ? "true" : "false");
  b.onclick = () => { haptic(); onClick(); render(); };
  return b;
}
function step(n, title, cls, items) {
  const s = document.createElement("section"); s.className = "step";
  s.innerHTML = `<h3><i>${n}</i>${title}</h3>`;
  const box = document.createElement("div"); box.className = cls; box.replaceChildren(...items); s.appendChild(box);
  return s;
}
function render() {
  const steps = []; let n = 1;
  if (C.branches) steps.push(step(n++, "Адрес", "grid2", C.branches.map((b, i) => btn("", `${esc(b[0])}<small>${esc(b[1])}</small>`, st.branch === i, () => { st.branch = i; st.master = -1; st.time = null; }))));
  if (C.opts) steps.push(step(n++, C.opts.label, "grid3", C.opts.list.map((o, i) => btn("", esc(o[0]), st.opt === i, () => { st.opt = i; }))));
  steps.push(step(n++, C.text.svcLabel, "services", C.services.map((s, i) => btn("", `<b>${esc(s.n)}</b>${s.d ? `<small>${esc(s.d)}</small>` : "<small>&nbsp;</small>"}<span class="p">${priceText(s)}</span>`, st.svc === i,
    () => { st.svc = i; if (st.master >= 0 && !masters().includes(C.masters[st.master])) st.master = -1; }))));
  if (C.masters) steps.push(step(n++, C.text.masterLabel || "Мастер", "grid2", [btn("", `Любой<small>${esc(C.anyMaster || "первый свободный")}</small>`, st.master < 0, () => { st.master = -1; }),
    ...masters().map(m => { const i = C.masters.indexOf(m); return btn("", `${esc(m.n)}<small>${esc(m.r)}</small>`, st.master === i, () => { st.master = i; st.time = null; }); })]));
  const days = []; for (let i = 0; i < 7; i++) { const d = new Date(); d.setDate(d.getDate() + i); days.push(d); }
  const now = new Date(), todayDone = !C.hours.some(h => +h.slice(0, 2) > now.getHours());
  if (!st.day) st.day = iso(days.find((d, i) => !closed(d) && !(i === 0 && todayDone)));
  const dayStep = step(n++, "День и время", "days", days.map((d, i) => btn("", `<small>${i === 0 ? "сег" : i === 1 ? "зав" : d.toLocaleDateString("ru-RU", { weekday: "short" })}</small><b>${d.getDate()}</b>`,
    st.day === iso(d), () => { st.day = iso(d); st.time = null; }, (i === 0 && todayDone) || closed(d))));
  const shift = st.master + 1;
  const times = document.createElement("div"); times.className = "times";
  times.replaceChildren(...C.hours.map((h, j) => btn("", h, st.time === h, () => { st.time = h; },
    busy.has(`b${st.branch}_${st.day}_${C.hours[(j + shift) % C.hours.length]}`) || (st.day === iso(now) && +h.slice(0, 2) <= now.getHours()))));
  dayStep.appendChild(times);
  const hint = document.createElement("p"); hint.className = "hint"; hint.textContent = "Зачёркнутое время уже занято."; dayStep.appendChild(hint);
  steps.push(dayStep);
  $("steps").replaceChildren(...steps);

  const s = svc(), ready = !!(s && st.time);
  $("sum").textContent = s ? (s.p === 0 ? "0 ₽" : (s.from ? "от " : "") + fmt(price(s))) : "—";
  $("sumlabel").textContent = ready ? `${dayLabel(st.day)} в ${st.time}` : s ? s.n : C.text.pickSvc;
  $("go").disabled = !ready; $("go").textContent = !s ? C.text.pickSvc : !st.time ? "Выберите время" : C.text.send;
  if (tg) tg.MainButton.setParams({ text: ready ? `${C.text.send} · ${$("sum").textContent}` : "Выберите время", color: C.accent, text_color: C.accentInk, is_active: ready, is_visible: view === "book" });
}

const mine = [];
let nextNo = 120 + Math.floor(Math.random() * 60);
if (qs.get("my")) qs.get("my").split(",").forEach(x => { const [no, day, time, k, total] = x.split("~"); const i = C.services.findIndex(s => s.k === k); if (i >= 0) mine.push({ no, day, time, svc: i, total: +total, status: "new" }); });

function submit() {
  const s = svc(); if (!s || !st.time) return;
  const payload = { branch: st.branch, opt: st.opt, svc: s.k, master: st.master, day: st.day, time: st.time, total: s.p === 0 ? 0 : price(s) };
  if (tg) { try { tg.HapticFeedback.notificationOccurred("success"); } catch (e) {} tg.sendData(JSON.stringify(payload)); return; }
  const no = String(nextNo++).padStart(4, "0");
  mine.push({ no, ...payload, svc: st.svc, status: "new" });
  busy.add(`b${st.branch}_${st.day}_${st.time}`);
  updateBadge();
  const rows = [];
  if (C.branches) rows.push(["Адрес", C.branches[st.branch][1]]);
  if (C.opts) rows.push([C.opts.label, C.opts.list[st.opt][0]]);
  rows.push([C.text.svcRow, s.n]);
  if (C.masters) rows.push([C.text.masterLabel || "Мастер", st.master < 0 ? "любой свободный" : C.masters[st.master].n]);
  $("done").innerHTML = `<div class="check">✓</div><h2>${C.text.doneTitle}</h2>
    <div class="ticket"><div class="top"><div class="no">ЗАПИСЬ № ${no}</div><div class="when">${dayLabel(st.day)}, ${st.time}</div><div style="color:var(--muted);font-size:14px">${esc(C.branches ? C.branches[st.branch][1] : C.address)}</div></div>
      <div class="bottom"><dl>${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${esc(r[1])}</dd>`).join("")}</dl>
      <div class="total"><span>${s.from ? "Стоимость от" : "Стоимость"}</span><b>${s.p === 0 ? "0 ₽" : fmt(price(s))}</b></div></div></div>
    ${C.text.doneExtra ? `<div class="extra-line">${C.text.doneExtra.replace("{n}", s.course || "").replace("{date}", followDate())}</div>` : ""}
    <p class="hint" style="text-align:center">В настоящем боте дальше: кнопка «Отправить номер», напоминание ${esc(C.text.remindWhen)}, отмена в один клик.</p>
    <div class="cta2"><button class="again" id="again" type="button">Записаться ещё</button><button class="again" id="tomine" type="button">Мои записи</button></div>`;
  $("done").hidden = false;
  $("again").onclick = () => { $("done").hidden = true; st.time = null; render(); $("app").scrollTop = 0; };
  $("tomine").onclick = () => { $("done").hidden = true; st.time = null; render(); show("my"); };
  const lines = [`${C.text.adminIcon} <b>Новая запись № ${no}</b>`, `<b>${dayLabel(st.day)}, ${st.time}</b>`];
  if (C.branches) lines.push(`📍 ${esc(C.branches[st.branch][1])}`);
  lines.push(`${esc(s.n)}${C.opts ? ", " + esc(C.opts.list[st.opt][0].toLowerCase()) : ""} · <span class="money">${priceText(s)}</span>`);
  if (C.masters) lines.push(`👤 ${st.master < 0 ? "любой свободный" : esc(C.masters[st.master].n)}`);
  if (s.course) lines.push(`🎟 ${C.text.courseWord || "Курс"}: ${s.course} сеансов, сейчас 1-й`);
  lines.push("📞 +7 921 ••• 45 67");
  ownerSay(lines.join("\n"), true);
}
function followDate() {
  if (!C.follow) return "";
  const d = new Date(st.day + "T12:00");
  if (C.follow.mode === "season") { const m = d.getMonth(); const t = m >= 2 && m <= 7 ? new Date(d.getFullYear(), 9, 1) : new Date(m >= 8 ? d.getFullYear() + 1 : d.getFullYear(), 3, 1); return t.toLocaleDateString("ru-RU", { day: "numeric", month: "long" }); }
  d.setDate(d.getDate() + C.follow.days); return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}
function ownerSay(html, kb) {
  const o = $("owner");
  o.querySelector(".empty")?.remove();
  const b = document.createElement("div");
  b.innerHTML = `<div class="bubble">${html}</div>${kb ? `<div class="ikb" style="margin-top:6px"><span>✔ Подтвердить</span><span>✖ Отказать</span></div>` : ""}`;
  o.appendChild(b);
}

let view = "book";
function show(v) {
  view = v;
  ["book", "prices", "my", "info"].forEach(k => { $("v-" + k).hidden = k !== v; });
  document.querySelectorAll("#tabs button").forEach(b => b.setAttribute("aria-selected", b.dataset.v === v ? "true" : "false"));
  document.querySelector(".bar").hidden = v !== "book";
  $("app").classList.toggle("notbook", v !== "book");
  $("app").scrollTop = 0;
  if (v === "my") renderMine();
  if (tg) render();
  haptic();
}
document.querySelectorAll("#tabs button").forEach(b => b.onclick = () => show(b.dataset.v));

function renderPrices() {
  $("plist").innerHTML = C.services.filter(s => s.p > 0).map(s => `<div><b>${esc(s.n)}</b><small>${esc(s.d || "")}</small><span class="p">${s.from ? "от " : ""}${fmt(s.p)}</span></div>`).join("");
}
function updateBadge() { const n = mine.filter(m => m.status !== "cancelled").length; $("badge").textContent = n; $("badge").hidden = n === 0; }
function renderMine() {
  const box = $("mine");
  if (!mine.length) { box.innerHTML = `<div class="empty-state"><div>Записей пока нет</div><button class="go" type="button" id="emptygo">Записаться</button></div>`; $("emptygo").onclick = () => show("book"); return; }
  box.replaceChildren(...mine.slice().reverse().map(m => {
    const s = C.services[m.svc], d = document.createElement("div");
    d.className = "ticket" + (m.status === "cancelled" ? " cancelled" : "");
    d.innerHTML = `<div class="top"><div class="no">ЗАПИСЬ № ${m.no}</div><div class="when">${dayLabel(m.day)}, ${m.time}</div></div>
      <div class="bottom"><dl><dt>${esc(C.text.svcRow)}</dt><dd>${esc(s.n)}</dd></dl><div class="total"><span>Стоимость</span><b>${m.total ? fmt(m.total) : "0 ₽"}</b></div>
      ${m.status === "cancelled" ? `<p class="hint">Запись отменена</p>` : `<div class="acts"><a href="${C.mapUrl}" target="_blank" rel="noopener">📍 Маршрут</a><button type="button">Отменить</button></div>`}</div>`;
    const c = d.querySelector(".acts button");
    if (c) c.onclick = () => {
      if (c.dataset.armed !== "1") { c.dataset.armed = "1"; c.textContent = "Точно отменить?"; return; }
      if (tg) { tg.sendData(JSON.stringify({ action: "cancel", no: m.no })); return; }
      m.status = "cancelled"; busy.delete(`b${m.branch}_${m.day}_${m.time}`); updateBadge(); renderMine(); render();
      ownerSay(`❌ Клиент отменил запись № ${m.no} (${m.time}), окно снова свободно.`);
    };
    return d;
  }));
}
renderPrices(); updateBadge();
$("go").onclick = submit;
if (tg) tg.MainButton.onClick(submit);
render();
"""


def demo_html(c):
    vars_ = "\n".join(f"  --{k}: {v};" for k, v in c["vars"].items() if k != "color-scheme") + f"\n  color-scheme: {c['vars']['color-scheme']};"
    e = dict(c["engine"])
    e.update(address=c["address"], mapUrl=c["map_url"], bg=c["vars"]["bg"], accent=c["vars"]["accent"], accentInk=c["vars"]["accent-ink"])
    js = DEMO_JS.replace("__CONFIG__", json.dumps(e, ensure_ascii=False))
    wa = "https://wa.me/" + re.sub(r"\D", "", c["phone"])
    feats = "".join(f"<li><span>{i}</span><div><b>{t}</b><small>{d}</small></div></li>" for i, t, d in c["features"])
    faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in c["faq"])
    chips = "".join(f"<span>{x}</span>" for x in c["promise"])
    example = "".join(f'<div class="bubble">{t}<time>{tm}</time></div>' for t, tm in c["example_msgs"])
    example_kb = f'<div class="ikb">{"".join(f"<span>{x}</span>" for x in c["example_kb"])}</div>' if c.get("example_kb") else ""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c["name"]} · бот записи</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="{c["fonts"]}">
<style>{DEMO_CSS.replace("__VARS__", vars_)}</style>
</head>
<body>
<noscript><div style="max-width:560px;margin:40px auto;padding:24px;border-radius:16px;background:#fff;color:#222;font:16px/1.5 system-ui,sans-serif;text-align:center"><b>Демо интерактивное и не работает в предпросмотре файла.</b><br>Откройте этот файл в браузере (Safari или Chrome). На телефоне удобнее посмотреть скриншоты.</div></noscript>
<div class="demo-flag"><b>Демо-версия бота</b> для {c["name"] if "«" in c["name"] else "«" + c["name"] + "»"}. {c["demo_note"]}</div>
<div class="shell">
  <header class="intro">
    <span class="tag">Демо · Telegram-бот записи</span>
    <h1>{c["h1"]}</h1>
    <p>{c["intro"]}</p>
  </header>
  <div class="stage">
    <div class="phone">
      <div class="screen" id="screen">
        <div class="tgbar"><b>{c["short"]}</b><span>мини-приложение</span></div>
        <main class="app" id="app">
          <div class="view" id="v-book">
            <section class="hero"><div class="ava">{c["mark"]}</div><div><h2>{c["name"]}</h2><p>{c["hero_sub"]}</p></div></section>
            <div class="promise">{chips}</div>
            <div id="steps"></div>
          </div>
          <div class="view" id="v-prices" hidden>
            <div class="pagehead"><h2>Цены</h2><p>{c["prices_note"]}</p></div>
            <div class="list" id="plist"></div>
            <p class="note">Цены примерные, для демонстрации.</p>
          </div>
          <div class="view" id="v-my" hidden>
            <div class="pagehead"><h2>Мои записи</h2><p>Отменить или построить маршрут можно отсюда.</p></div>
            <div class="mine" id="mine"></div>
          </div>
          <div class="view" id="v-info" hidden>
            <div class="pagehead"><h2>Контакты</h2><p>{c["name"]}</p></div>
            <div class="contact">
              {"".join(f'<div class="row"><span>📍</span><div><b>{a}</b><small>{n}</small></div></div>' for a, n in c["addresses"])}
              <div class="row"><span>📞</span><div><b>{c["phone"]}</b><small>звонки и WhatsApp</small></div></div>
              <div class="row"><span>🕘</span><div><b>{c["hours_text"]}</b><small>{c["hours_note"]}</small></div></div>
              <div class="cta"><a class="y" href="{c["map_url"]}" target="_blank" rel="noopener">Маршрут</a><a class="g" href="{wa}" target="_blank" rel="noopener">WhatsApp</a></div>
            </div>
            <h3 class="sub">Частые вопросы</h3>
            <div style="margin-top:10px">{faq}</div>
          </div>
        </main>
        <div class="bar"><div class="sum"><small id="sumlabel"></small><b id="sum">—</b></div><button class="go" id="go" type="button" disabled>Выберите услугу</button></div>
        <nav class="tabs" role="tablist" id="tabs">
          <button type="button" role="tab" data-v="book" aria-selected="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/></svg>Запись</button>
          <button type="button" role="tab" data-v="prices" aria-selected="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10"/></svg>Цены</button>
          <button type="button" role="tab" data-v="my" aria-selected="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>Мои записи<span class="badge" id="badge" hidden>0</span></button>
          <button type="button" role="tab" data-v="info" aria-selected="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>Контакты</button>
        </nav>
        <div class="done" id="done" hidden></div>
      </div>
    </div>
    <aside class="side">
      <section class="card"><h2>Telegram {c["owner_who"]}</h2><div class="tgchat" id="owner" aria-live="polite"><p class="empty">Здесь появится новая запись.<br>Запишитесь в приложении слева.</p></div></section>
      <section class="card"><h2>{c["example_title"]}</h2><div class="tgchat">{example}{example_kb}</div></section>
      <section class="card"><h2>Что ещё делает бот</h2><ul class="feat">{feats}</ul><p class="note">{c["demo_note"]} В вашей версии будут ваши услуги и цены.</p></section>
    </aside>
  </div>
</div>
<script>{js}</script>
</body>
</html>
"""


BOT_PY = r'''"""Telegram-бот онлайн-записи для «__NAME__» (__ADDRESS__).

Запись через мини-приложение (webapp/index.html) или по шагам в чате, квитанция с номером, «Мои записи», отмена,
напоминание перед визитом, кнопки «Подтвердить / Отказать» у владельца, расписание /today и /tomorrow,
__FOLLOW_DOC__

Запуск:
    pip install "aiogram==3.*"
    BOT_TOKEN=... ADMIN_CHAT_ID=... WEBAPP_URL=https://.../index.html python bot.py

WEBAPP_URL можно не задавать: тогда работает только запись в чате.
Услуги, цены и часы — в CONFIG ниже (те же, что в demo.html).
"""
import asyncio
import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])  # чат владельца: сюда приходят заявки
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")      # https-адрес webapp/index.html

CONFIG = __CONFIG__

NAME = CONFIG["name"]
ADDRESS = CONFIG["address"]
MAP_URL = "https://yandex.ru/maps/?text=" + quote("Санкт-Петербург, " + ADDRESS)
SERVICES = {s["k"]: s for s in CONFIG["services"]}
BRANCHES = CONFIG.get("branches") or []          # [[коротко, полный адрес], ...]
OPTS = CONFIG.get("opts")                        # {"label": ..., "list": [[название, коэффициент цены], ...]}
MASTERS = CONFIG.get("masters") or []            # [{"n": имя, "r": роль, "b": филиал, "cats": [...]}]
HOURS = CONFIG["hours"]                          # ["10:00", "11:00", ...]
CLOSED = {(d + 6) % 7 for d in CONFIG.get("closedDays", [])}  # в конфиге 0 = воскресенье (как в JS)
FOLLOW = CONFIG.get("follow")                    # {"mode": "season"} или {"mode": "days", "days": N}
REMIND_BEFORE = timedelta(hours=CONFIG.get("remindHours", 2))
BANNER = Path(__file__).with_name("banner.png")

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]
LINE = "━━━━━━━━━━━━━━━"

db = sqlite3.connect("bookings.db")
db.execute("""CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY, user_id INTEGER, branch INTEGER, opt INTEGER, service TEXT, master INTEGER,
    day TEXT, time TEXT, price INTEGER, phone TEXT, status TEXT DEFAULT 'new',
    reminded INTEGER DEFAULT 0, visited INTEGER DEFAULT 0, followed INTEGER DEFAULT 0, created TEXT)""")
# Курсы и абонементы: сколько сеансов куплено и сколько уже пройдено
db.execute("""CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY, user_id INTEGER, service TEXT, total INTEGER, used INTEGER DEFAULT 0, created TEXT)""")
db.execute("CREATE TABLE IF NOT EXISTS optout (user_id INTEGER PRIMARY KEY)")
db.commit()


class Booking(StatesGroup):
    branch = State()
    opt = State()
    service = State()
    master = State()
    day = State()
    time = State()
    phone = State()


# ---------- helpers ----------

def kb(rows, cols=2):
    buttons = [InlineKeyboardButton(text=t, url=d[4:]) if d.startswith("url:") else InlineKeyboardButton(text=t, callback_data=d)
               for t, d in rows]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + cols] for i in range(0, len(buttons), cols)])


def money(n):
    return f"{n:,}".replace(",", " ") + " ₽"


def human_day(day_iso):
    d = date.fromisoformat(day_iso)
    return f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]}"


def human_date(d):
    return f"{d.day} {MONTHS[d.month - 1]}"


def calc(data):
    s = SERVICES[data["service"]]
    k = OPTS["list"][data.get("opt", 0)][1] if OPTS else 1
    return round(s["p"] * k / 50) * 50


def price_text(data):
    s = SERVICES[data["service"]]
    return "бесплатно" if s["p"] == 0 else ("от " if s.get("from") else "") + money(calc(data))


def masters_for(branch, service=None):
    cat = SERVICES[service].get("c") if service else None
    return [i for i, m in enumerate(MASTERS)
            if m.get("b", branch) == branch and (not cat or not m.get("cats") or cat in m["cats"])]


def capacity(branch):
    return max(1, len([m for m in MASTERS if m.get("b", branch) == branch]))


def slot_free(branch, master, day, time):
    rows = db.execute("SELECT master FROM bookings WHERE branch=? AND day=? AND time=? AND status!='cancelled'",
                      (branch, day, time)).fetchall()
    if len(rows) >= capacity(branch):
        return False
    return master < 0 or all(m != master for (m,) in rows)


def busy_slots():
    """Полностью занятые слоты на неделю вперёд для мини-приложения: b0_2026-10-03_11:00,..."""
    rows = db.execute("SELECT branch, day, time, COUNT(*) FROM bookings WHERE status!='cancelled' AND day>=? "
                      "GROUP BY branch, day, time", (date.today().isoformat(),)).fetchall()
    return ",".join(f"b{b}_{d}_{t}" for b, d, t, n in rows if n >= capacity(b))


def my_param(user_id):
    rows = db.execute("SELECT id, day, time, service, price FROM bookings WHERE user_id=? AND status!='cancelled' "
                      "AND day>=? ORDER BY day, time", (user_id, date.today().isoformat())).fetchall()
    return ",".join(f"{bid:04d}~{d}~{t}~{s}~{p}" for bid, d, t, s, p in rows)


def main_keyboard(user_id=None):
    """Постоянная кнопка снизу: открывает мини-приложение (sendData работает только из такой кнопки)."""
    if not WEBAPP_URL:
        return None
    sep = "&" if "?" in WEBAPP_URL else "?"
    url = f"{WEBAPP_URL}{sep}busy={busy_slots()}"
    if user_id is not None:
        url += f"&my={my_param(user_id)}"
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=f"{CONFIG['icon']} Записаться онлайн", web_app=WebAppInfo(url=url))]],
                               resize_keyboard=True, is_persistent=True)


def active_course(user_id):
    return db.execute("SELECT id, service, total, used FROM courses WHERE user_id=? AND used<total ORDER BY id DESC LIMIT 1",
                      (user_id,)).fetchone()


def next_season(day_iso):
    d = date.fromisoformat(day_iso)
    if 3 <= d.month <= 8:
        return date(d.year, 10, 1), "зимнюю"
    return date(d.year + 1 if d.month >= 9 else d.year, 4, 1), "летнюю"


def details(data):
    lines = []
    if BRANCHES:
        lines.append(f"📍 {BRANCHES[data['branch']][1]}")
    opt = f", {OPTS['list'][data['opt']][0].lower()}" if OPTS else ""
    lines.append(f"{CONFIG['icon']} {SERVICES[data['service']]['n']}{opt}")
    if MASTERS:
        lines.append(f"👤 {MASTERS[data['master']]['n'] if data['master'] >= 0 else 'любой свободный'}")
    return "\n".join(lines)


def days_keyboard():
    days = []
    for i in range(7):
        d = date.today() + timedelta(days=i)
        if d.weekday() in CLOSED:
            continue
        label = "Сегодня" if i == 0 else "Завтра" if i == 1 else f"{WEEKDAYS[d.weekday()]} {d.day}"
        days.append((label, f"d:{d.isoformat()}"))
    return kb(days, 4)


dp = Dispatcher()


# ---------- start ----------

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    caption = f"<b>{NAME}</b>\n{ADDRESS} · {CONFIG['hoursText']}\n\n{CONFIG['welcome']}"
    rows = [("💬 Записаться в чате", "go"), ("📋 Мои записи", "my")]
    if any(s.get("course") for s in SERVICES.values()):
        rows.append(("🎟 Мой абонемент", "course"))
    rows.append(("📍 Как добраться", f"url:{MAP_URL}"))
    if BANNER.exists():
        await m.answer_photo(FSInputFile(BANNER), caption=caption, parse_mode="HTML", reply_markup=kb(rows, 1))
    else:
        await m.answer(caption, parse_mode="HTML", reply_markup=kb(rows, 1))
    if WEBAPP_URL:
        await m.answer(f"Нажмите «{CONFIG['icon']} Записаться онлайн» внизу: там всё свободное время и цены.",
                       reply_markup=main_keyboard(m.from_user.id))


# ---------- мини-приложение ----------

@dp.message(F.web_app_data)
async def from_webapp(m: Message, state: FSMContext, bot: Bot):
    try:
        p = json.loads(m.web_app_data.data)
        if p.get("action") == "cancel":
            await cancel_booking(bot, int(p["no"]), m.from_user.id, m)
            return
        data = {"branch": int(p.get("branch", 0)), "opt": int(p.get("opt", 0)), "service": p["svc"],
                "master": int(p.get("master", -1)), "day": p["day"], "time": p["time"]}
        SERVICES[data["service"]]  # значения проверяем по своему прайсу
        assert data["time"] in HOURS and 0 <= data["branch"] < max(1, len(BRANCHES))
        assert not OPTS or 0 <= data["opt"] < len(OPTS["list"])
        assert data["master"] < 0 or data["master"] in masters_for(data["branch"], data["service"])
        date.fromisoformat(data["day"])
    except (KeyError, ValueError, TypeError, AssertionError):
        await m.answer("Не получилось прочитать заявку, попробуйте ещё раз.", reply_markup=main_keyboard(m.from_user.id))
        return
    if not slot_free(data["branch"], data["master"], data["day"], data["time"]):
        await m.answer("Это время только что заняли 😔 Откройте запись ещё раз и выберите другое.",
                       reply_markup=main_keyboard(m.from_user.id))
        return
    await state.set_data(data)  # цену пересчитываем сами, присланной не доверяем
    await ask_phone(m, state)


# ---------- запись в чате ----------

@dp.callback_query(F.data == "go")
async def go(c: CallbackQuery, state: FSMContext):
    await state.set_data({"branch": 0, "opt": 0, "master": -1})
    if BRANCHES:
        await state.set_state(Booking.branch)
        await c.message.answer("Куда вам удобнее?", reply_markup=kb([(b[1], f"b:{i}") for i, b in enumerate(BRANCHES)], 1))
    else:
        await ask_opt(c.message, state)
    await c.answer()


@dp.callback_query(Booking.branch, F.data.startswith("b:"))
async def picked_branch(c: CallbackQuery, state: FSMContext):
    await state.update_data(branch=int(c.data[2:]))
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_opt(c.message, state)
    await c.answer()


async def ask_opt(m: Message, state: FSMContext):
    if not OPTS:
        return await ask_service(m, state)
    await state.set_state(Booking.opt)
    await m.answer(f"{OPTS['label']}?", reply_markup=kb([(o[0], f"o:{i}") for i, o in enumerate(OPTS["list"])], 1))


@dp.callback_query(Booking.opt, F.data.startswith("o:"))
async def picked_opt(c: CallbackQuery, state: FSMContext):
    await state.update_data(opt=int(c.data[2:]))
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_service(c.message, state)
    await c.answer()


async def ask_service(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Booking.service)
    rows = [(f"{s['n']} · {price_text({**data, 'service': k})}", f"s:{k}") for k, s in SERVICES.items()]
    await m.answer(CONFIG["askService"], reply_markup=kb(rows, 1))


@dp.callback_query(Booking.service, F.data.startswith("s:"))
async def picked_service(c: CallbackQuery, state: FSMContext):
    await state.update_data(service=c.data[2:])
    data = await state.get_data()
    await c.message.edit_reply_markup(reply_markup=None)
    ids = masters_for(data["branch"], data["service"]) if MASTERS else []
    if ids:
        await state.set_state(Booking.master)
        await c.message.answer(f"{CONFIG.get('masterLabel', 'Мастер')}?",
                               reply_markup=kb([("Любой свободный", "m:-1")] + [(f"{MASTERS[i]['n']} · {MASTERS[i]['r']}", f"m:{i}") for i in ids], 1))
    else:
        await ask_day(c.message, state)
    await c.answer()


@dp.callback_query(Booking.master, F.data.startswith("m:"))
async def picked_master(c: CallbackQuery, state: FSMContext):
    await state.update_data(master=int(c.data[2:]))
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_day(c.message, state)
    await c.answer()


async def ask_day(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Booking.day)
    await m.answer(f"💰 Стоимость: <b>{price_text(data)}</b>\n\nВыберите день:", parse_mode="HTML", reply_markup=days_keyboard())


@dp.callback_query(Booking.day, F.data.startswith("d:"))
async def ask_time(c: CallbackQuery, state: FSMContext):
    day, data, now = c.data[2:], await state.get_data(), datetime.now()
    free = [(t, f"h:{t}") for t in HOURS
            if not (day == now.date().isoformat() and int(t[:2]) <= now.hour) and slot_free(data["branch"], data["master"], day, t)]
    if not free:
        await c.answer("На этот день всё занято, выберите другой", show_alert=True)
        return
    await state.update_data(day=day)
    await state.set_state(Booking.time)
    await c.message.edit_text(f"{human_day(day)}. Свободное время:", reply_markup=kb(free, 4))
    await c.answer()


@dp.callback_query(Booking.time, F.data.startswith("h:"))
async def picked_time(c: CallbackQuery, state: FSMContext):
    await state.update_data(time=c.data[2:])
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_phone(c.message, state)
    await c.answer()


async def ask_phone(m: Message, state: FSMContext):
    await state.set_state(Booking.phone)
    await m.answer("Последний шаг: оставьте номер, чтобы с вами могли связаться, если что-то изменится.",
                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
                                                    resize_keyboard=True, one_time_keyboard=True))


@dp.message(Booking.phone)
async def finish(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    if len([ch for ch in phone if ch.isdigit()]) < 10:
        await m.answer("Нажмите кнопку «📱 Отправить мой номер» или напишите номер цифрами.")
        return
    data = await state.get_data()
    await state.clear()
    if not slot_free(data["branch"], data["master"], data["day"], data["time"]):
        await m.answer("Это время только что заняли 😔 Выберите другое: /start", reply_markup=main_keyboard(m.from_user.id))
        return
    total = 0 if SERVICES[data["service"]]["p"] == 0 else calc(data)
    cur = db.execute("INSERT INTO bookings (user_id, branch, opt, service, master, day, time, price, phone, created) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (m.from_user.id, data["branch"], data["opt"], data["service"], data["master"], data["day"], data["time"],
                      total, phone, datetime.now().isoformat()))
    bid = cur.lastrowid
    course_line = ""
    svc = SERVICES[data["service"]]
    if svc.get("course"):
        db.execute("INSERT INTO courses (user_id, service, total, created) VALUES (?,?,?,?)",
                   (m.from_user.id, data["service"], svc["course"], datetime.now().isoformat()))
        course_line = f"\n🎟 {CONFIG.get('courseWord', 'Курс')}: {svc['course']} сеансов, это первый"
    elif (c := active_course(m.from_user.id)):
        course_line = f"\n🎟 Сеанс {c[3] + 1} из {c[2]}"
    db.commit()
    where = BRANCHES[data["branch"]][1] if BRANCHES else ADDRESS
    await m.answer("Готово! 🎉", reply_markup=main_keyboard(m.from_user.id))
    await m.answer(f"✅ <b>Вы записаны</b> · № {bid:04d}\n{LINE}\n📅 <b>{human_day(data['day'])} · {data['time']}</b>\n"
                   f"{details(data)}{course_line}\n{LINE}\n💰 <b>{price_text(data)}</b>\n📍 {where}\n\n"
                   f"Напомню {CONFIG['remindWhen']}.",
                   parse_mode="HTML", reply_markup=kb([("📍 Маршрут", f"url:{MAP_URL}"), ("❌ Отменить", f"cancel:{bid}")]))
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"{CONFIG['icon']} <b>Новая запись № {bid:04d}</b>\n{LINE}\n📅 <b>{human_day(data['day'])} · {data['time']}</b>\n"
        f"{details(data)}\n💰 {price_text(data)}{course_line}\n📞 {phone}",
        parse_mode="HTML", reply_markup=kb([("✔ Подтвердить", f"ok:{bid}"), ("✖ Отказать", f"no:{bid}")]))


# ---------- мои записи / абонемент / отмена ----------

@dp.message(Command("my"))
@dp.callback_query(F.data == "my")
async def my_bookings(event):
    m = event.message if isinstance(event, CallbackQuery) else event
    rows = db.execute("SELECT id, day, time, service, price FROM bookings WHERE user_id=? AND status!='cancelled' "
                      "AND day>=? ORDER BY day, time", (event.from_user.id, date.today().isoformat())).fetchall()
    if not rows:
        await m.answer("Активных записей нет. Записаться: /start")
    for bid, day, t, svc, price in rows:
        await m.answer(f"№ {bid:04d} · <b>{human_day(day)}, {t}</b>\n{SERVICES[svc]['n']} · {money(price)}",
                       parse_mode="HTML", reply_markup=kb([("❌ Отменить", f"cancel:{bid}")]))
    if isinstance(event, CallbackQuery):
        await event.answer()


@dp.message(Command("course"))
@dp.callback_query(F.data == "course")
async def my_course(event):
    m = event.message if isinstance(event, CallbackQuery) else event
    c = active_course(event.from_user.id)
    if not c:
        await m.answer("Активного абонемента нет. Купить курс со скидкой можно при записи: /start")
    else:
        await m.answer(f"🎟 <b>{SERVICES[c[1]]['n']}</b>\nПройдено {c[3]} из {c[2]}, осталось <b>{c[2] - c[3]}</b>.",
                       parse_mode="HTML", reply_markup=kb([("📅 Записаться на следующий", "go")], 1))
    if isinstance(event, CallbackQuery):
        await event.answer()


async def cancel_booking(bot: Bot, bid: int, user_id: int, m: Message):
    row = db.execute("SELECT day, time FROM bookings WHERE id=? AND user_id=? AND status!='cancelled'", (bid, user_id)).fetchone()
    if not row:
        return False
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
    db.commit()
    await m.answer("Запись отменена. Будем рады видеть вас в другой раз: /start", reply_markup=main_keyboard(user_id))
    await bot.send_message(ADMIN_CHAT_ID, f"❌ Клиент отменил запись № {bid:04d} ({human_day(row[0])}, {row[1]}), окно свободно.")
    return True


@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery, bot: Bot):
    if await cancel_booking(bot, int(c.data.split(":")[1]), c.from_user.id, c.message):
        await c.message.edit_reply_markup(reply_markup=None)
    await c.answer()


@dp.callback_query(F.data == "optout")
async def optout(c: CallbackQuery):
    db.execute("INSERT OR IGNORE INTO optout (user_id) VALUES (?)", (c.from_user.id,))
    db.commit()
    await c.answer("Хорошо, больше не буду напоминать", show_alert=True)


# ---------- для владельца ----------

def is_admin(m: Message):
    return m.chat.id == ADMIN_CHAT_ID


@dp.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def admin_decision(c: CallbackQuery, bot: Bot):
    if c.message.chat.id != ADMIN_CHAT_ID:
        return await c.answer()
    action, bid = c.data.split(":")
    row = db.execute("SELECT user_id, day, time FROM bookings WHERE id=?", (int(bid),)).fetchone()
    if not row:
        return await c.answer("Запись не найдена")
    if action == "ok":
        db.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (int(bid),))
        await bot.send_message(row[0], f"👍 Запись подтверждена: {human_day(row[1])}, {row[2]}. Ждём вас!")
        mark = "✔ Подтверждено"
    else:
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (int(bid),))
        await bot.send_message(row[0], "К сожалению, на это время принять не получится. Выберите другое: /start")
        mark = "✖ Отказано"
    db.commit()
    await c.message.edit_text(c.message.html_text + f"\n\n<b>{mark}</b>", parse_mode="HTML")
    await c.answer("Готово")


async def schedule(m: Message, day: date):
    rows = db.execute("SELECT time, branch, opt, service, master, price, phone FROM bookings WHERE day=? AND status!='cancelled' "
                      "ORDER BY time", (day.isoformat(),)).fetchall()
    if not rows:
        return await m.answer(f"На {human_day(day.isoformat())} записей нет.")
    lines = [f"<b>{t}</b> · {details({'branch': b, 'opt': o, 'service': s, 'master': ms}).replace(chr(10), ' · ')} · {money(p)} · {ph}"
             for t, b, o, s, ms, p, ph in rows]
    await m.answer(f"📋 <b>{human_day(day.isoformat())}</b> · записей: {len(rows)}, сумма {money(sum(x[5] for x in rows))}\n\n"
                   + "\n".join(lines), parse_mode="HTML")


@dp.message(Command("today"), is_admin)
async def today(m: Message):
    await schedule(m, date.today())


@dp.message(Command("tomorrow"), is_admin)
async def tomorrow(m: Message):
    await schedule(m, date.today() + timedelta(days=1))


@dp.message(Command("all"), is_admin)
async def broadcast(m: Message, bot: Bot):
    """Рассылка всем прошлым клиентам: /all Текст сообщения"""
    text = m.text.partition(" ")[2]
    if not text:
        return await m.answer("Напишите текст после команды, например: /all В субботу есть свободные окна, записывайтесь: /start")
    users = [u for (u,) in db.execute("SELECT DISTINCT user_id FROM bookings WHERE user_id NOT IN (SELECT user_id FROM optout)")]
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.1)
    await m.answer(f"Отправлено {sent} из {len(users)} клиентам.")


# ---------- напоминания и «после визита» ----------

async def loop(bot: Bot):
    while True:
        now = datetime.now()
        rows = db.execute("SELECT id, user_id, day, time, visited, followed, reminded FROM bookings WHERE status!='cancelled' "
                          "AND (reminded=0 OR visited=0 OR followed=0)").fetchall()
        for bid, uid, day, t, visited, followed, reminded in rows:
            start = datetime.fromisoformat(f"{day}T{t}")
            try:
                if not reminded and timedelta(0) < start - now <= REMIND_BEFORE and 9 <= now.hour < 22:
                    await bot.send_message(uid, f"⏰ Напоминаю: <b>{human_day(day)}, {t}</b> вас ждут в «{NAME}».\n📍 {ADDRESS}",
                                           parse_mode="HTML", reply_markup=kb([("📍 Маршрут", f"url:{MAP_URL}"), ("❌ Не смогу", f"cancel:{bid}")]))
                    db.execute("UPDATE bookings SET reminded=1 WHERE id=?", (bid,))
                if not visited and now > start + timedelta(hours=2):
                    db.execute("UPDATE bookings SET visited=1 WHERE id=?", (bid,))
                    c = active_course(uid)
                    if c:
                        db.execute("UPDATE courses SET used=used+1 WHERE id=?", (c[0],))
                        left = c[2] - c[3] - 1
                        await bot.send_message(uid, f"🎟 Сеанс {c[3] + 1} из {c[2]} пройден. " +
                                               (f"Осталось {left}. Записаться на следующий?" if left else "Курс завершён, спасибо! 🙏"),
                                               reply_markup=kb([("📅 Записаться", "go")], 1) if left else None)
                if visited and not followed and FOLLOW and now.hour >= 11:
                    due, text = follow_due(day)
                    if date.today() >= due:
                        db.execute("UPDATE bookings SET followed=1 WHERE id=?", (bid,))
                        newer = db.execute("SELECT 1 FROM bookings WHERE user_id=? AND day>? AND status!='cancelled'", (uid, day)).fetchone()
                        opted = db.execute("SELECT 1 FROM optout WHERE user_id=?", (uid,)).fetchone()
                        if not newer and not opted:
                            await bot.send_message(uid, text, reply_markup=kb([("📅 Записаться", "go"), ("🔕 Не напоминать", "optout")], 1))
            except Exception:
                pass
            db.commit()
        await asyncio.sleep(300)


def follow_due(day):
    if FOLLOW["mode"] == "season":
        when, what = next_season(day)
        return when, f"Здравствуйте! Это {NAME}. Пора менять резину на {what}. Запишитесь заранее, пока есть удобное время."
    return date.fromisoformat(day) + timedelta(days=FOLLOW["days"]), FOLLOW["text"].replace("{name}", NAME)


async def main():
    bot = Bot(BOT_TOKEN)
    await bot.set_my_commands([BotCommand(command="start", description="Записаться"),
                               BotCommand(command="my", description="Мои записи")])
    asyncio.create_task(loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''


def bot_py(c):
    e = c["engine"]
    cfg = {"name": c["name"], "address": c["address_bot"], "icon": e["text"]["adminIcon"], "hoursText": c["hours_text"],
           "welcome": c["welcome"], "askService": c["ask_service"], "remindWhen": e["text"]["remindWhen"],
           "remindHours": c.get("remind_hours", 2), "courseWord": e["text"].get("courseWord", "Курс"),
           "masterLabel": e["text"].get("masterLabel", "Мастер"), "hours": e["hours"]}
    for k in ("branches", "opts", "masters", "closedDays", "follow"):
        if e.get(k):
            cfg[k] = e[k]
    cfg["services"] = e["services"]
    body = pprint.pformat(cfg, width=118, sort_dicts=False, indent=1)
    return (BOT_PY.replace("__CONFIG__", body).replace("__NAME__", c["name"].replace("«", "").replace("»", ""))
            .replace("__ADDRESS__", c["address_bot"]).replace("__FOLLOW_DOC__", c["follow_doc"]))


BANNER = r"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="__FONTS__"><style>
html,body{margin:0}body{width:1280px;height:640px;overflow:hidden;background:__BG__;color:__INK__;font-family:__BODY__;position:relative}
.wrap{position:absolute;left:80px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;max-width:760px}
.tag{display:inline-block;align-self:flex-start;background:__ACC__;color:__ACCINK__;font:700 22px/1 __BODY__;letter-spacing:.1em;text-transform:uppercase;padding:12px 16px;border-radius:8px}
h1{font:__HW__ 92px/1.02 __DISP__;margin:26px 0 18px;letter-spacing:-.01em}
p{font-size:34px;margin:0 0 30px;color:__MUTED__}p b{color:__ACCT__}
.chips{display:flex;gap:14px;flex-wrap:wrap}.chips span{border:2px solid __LINE__;border-radius:999px;padding:10px 22px;font-size:24px}
.mark{position:absolute;right:-90px;top:50%;transform:translateY(-50%);width:560px;height:560px;border-radius:50%;background:__ACC__;opacity:.95;display:grid;place-items:center;color:__ACCINK__;font:700 260px/1 __DISP__}
.mark i{position:absolute;inset:-34px;border-radius:50%;border:3px dashed __LINE__}
</style></head><body><div class="wrap"><span class="tag">__TAG__</span><h1>__BIG__</h1><p>__SUB__</p><div class="chips">__CHIPS__</div></div><div class="mark"><i></i><span style="margin-right:120px">__MARK__</span></div></body></html>"""

AVATAR = r"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="__FONTS__"><style>
html,body{margin:0}body{width:640px;height:640px;background:__ACC__;display:grid;place-items:center;color:__ACCINK__;font:700 330px/1 __DISP__}
</style></head><body>__MARK__</body></html>"""


def banner_html(c, avatar=False):
    v = c["vars"]
    t = AVATAR if avatar else BANNER
    rep = {"__FONTS__": c["fonts"], "__BG__": v["bg"], "__INK__": v["ink"], "__BODY__": v["font-body"], "__DISP__": v["font-display"],
           "__ACC__": v["accent"], "__ACCINK__": v["accent-ink"], "__ACCT__": v["accent-text"], "__MUTED__": v["muted"], "__LINE__": v["line"],
           "__HW__": v["h-weight"], "__MARK__": c["mark"]}
    if not avatar:
        b = c["banner"]
        rep.update({"__TAG__": b["tag"], "__BIG__": b["big"], "__SUB__": b["sub"], "__CHIPS__": "".join(f"<span>{x}</span>" for x in b["chips"])})
    for k, val in rep.items():
        t = t.replace(k, val)
    return t
