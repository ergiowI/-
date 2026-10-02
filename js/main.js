// Собирает страницы из объекта SITE (js/config.js). Здесь менять ничего не нужно.
// Обычный режим: каждая страница — свой .html файл с <main data-page="...">.
// Однофайловый режим (window.SINGLE_FILE): все страницы в одном файле, переключение по #якорю.
(function () {
  const S = SITE;
  const SINGLE = !!window.SINGLE_FILE;
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const rub = (n) => n.toLocaleString("ru-RU").replace(/ /g, " ") + " ₽";
  const href = (page) => (SINGLE ? `#${page}` : page === "home" ? "index.html" : `${page}.html`);
  const tgIcon = `<svg class="tg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.4 4.1 2.9 11.3c-1.3.5-1.2 1.3-.2 1.6l4.7 1.5 1.8 5.6c.2.6.4.8.9.8.4 0 .6-.2.9-.5l2.3-2.2 4.7 3.5c.9.5 1.5.2 1.7-.8l3.1-14.6c.3-1.3-.5-1.9-1.4-1.5Zm-3.5 3.3-8.7 7.9-.3 3.5-1.6-5 10-6.6c.5-.3.9 0 .6.2Z"/></svg>`;
  const cta = (cls = "btn") => `<a class="${cls}" href="${esc(S.botLink)}" target="_blank" rel="noopener">${tgIcon}${esc(S.ctaText)}</a>`;

  // Картинка ниши: S.art = "tire" — шина с маркировкой по боковине; { emoji } — круглый бейдж с эмодзи.
  // ring — текст по кругу (только для большой картинки в шапке).
  function art(label, ring) {
    const id = "arc" + Math.random().toString(36).slice(2, 7);
    const text = ring ? `<text font-family="JetBrains Mono, monospace" font-size="14" style="fill:var(--dust)"><textPath href="#${id}" textLength="790" lengthAdjust="spacing">${esc(ring)}</textPath></text>` : "";
    if (S.art && S.art.emoji) {
      return `<svg viewBox="0 0 400 400" role="img" aria-label="${esc(label || S.name)}">
      <defs><path id="${id}" d="M200,200 m-128,0 a128,128 0 1,1 256,0 a128,128 0 1,1 -256,0"/></defs>
      <g class="spin">
        <circle cx="200" cy="200" r="184" style="fill:var(--asphalt-2)"/>
        <circle cx="200" cy="200" r="174" fill="none" style="stroke:var(--marking)" stroke-width="6" stroke-dasharray="2 14" stroke-linecap="round"/>
        ${text}
        <circle cx="200" cy="200" r="104" style="fill:color-mix(in srgb, var(--marking) 14%, var(--asphalt-2))"/>
      </g>
      <text x="200" y="200" text-anchor="middle" dominant-baseline="central" font-size="110">${esc(S.art.emoji)}</text></svg>`;
    }
    return `<svg viewBox="0 0 400 400" role="img" aria-label="${esc(label || S.name)}">
      <defs><path id="${id}" d="M200,200 m-128,0 a128,128 0 1,1 256,0 a128,128 0 1,1 -256,0"/></defs>
      <g class="spin">
        <circle cx="200" cy="200" r="184" fill="#101113"/>
        <circle cx="200" cy="200" r="176" fill="none" stroke="#2a2e33" stroke-width="22" stroke-dasharray="14 9"/>
        <circle cx="200" cy="200" r="160" fill="none" stroke="#24272b" stroke-width="6" stroke-dasharray="4 10"/>
        <circle cx="200" cy="200" r="148" fill="#1b1d20"/>
        ${text}
        <circle cx="200" cy="200" r="104" fill="#2a2e33"/>
        <circle cx="200" cy="200" r="98" fill="none" stroke="#3a3f45" stroke-width="2"/>
        ${[0, 72, 144, 216, 288].map((a) => `<rect x="192" y="112" width="16" height="64" rx="8" fill="#3a3f45" transform="rotate(${a} 200 200)"/>`).join("")}
        <circle cx="200" cy="200" r="30" fill="#17191c" style="stroke:var(--marking)" stroke-width="4"/>
        ${[0, 72, 144, 216, 288].map((a) => `<circle cx="200" cy="182" r="3.5" fill="#a19e95" transform="rotate(${a} 200 200)"/>`).join("")}
      </g></svg>`;
  }

  function mskNow() {
    const p = Object.fromEntries(new Intl.DateTimeFormat("en-GB", { timeZone: S.timezone, weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23", month: "numeric" }).formatToParts(new Date()).map((x) => [x.type, x.value]));
    const wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(p.weekday);
    return { wd, min: +p.hour * 60 + +p.minute, month: +p.month };
  }
  const toMin = (t) => { const [h, m] = t.split(":"); return h * 60 + +m; };
  function openStatus() {
    const n = mskNow(), h = S.hours[n.wd];
    if (h && n.min >= toMin(h[0]) && n.min < toMin(h[1])) return { open: true, text: `Открыто до ${h[1]}` };
    for (let i = 0; i < 7; i++) {
      const d = (n.wd + i) % 7, hh = S.hours[d];
      if (!hh) continue;
      if (i === 0 && n.min < toMin(hh[0])) return { open: false, text: `Закрыто, откроемся сегодня в ${hh[0]}` };
      if (i === 1) return { open: false, text: `Закрыто, откроемся завтра в ${hh[0]}` };
      if (i > 1) return { open: false, text: `Закрыто, откроемся в ${["пн", "вт", "ср", "чт", "пт", "сб", "вс"][d]} в ${hh[0]}` };
    }
    return { open: false, text: "Закрыто" };
  }

  // Часы работы коротко: соседние дни с одинаковым графиком склеиваются («Пн–Пт 09:00–20:00»)
  function hoursShort() {
    const names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"], out = [];
    for (let i = 0; i < 7; ) {
      const key = S.hours[i] ? S.hours[i].join("–") : "выходной";
      let j = i;
      while (j + 1 < 7 && (S.hours[j + 1] ? S.hours[j + 1].join("–") : "выходной") === key) j++;
      out.push(`${i === j ? names[i] : names[i] + "–" + names[j]} ${key}`);
      i = j + 1;
    }
    return out.join("<br>");
  }

  // ===== Общие части =====
  function header() {
    const n = mskNow(), season = S.seasons.find((s) => s.months.includes(n.month));
    return `${season ? `<div class="season">${esc(season.text)}</div>` : ""}
    <header class="hdr"><div class="wrap">
      <a class="logo" href="${href("home")}">${art("", "")}<span>${esc(S.name)}</span></a>
      <button class="burger" type="button" aria-label="Меню" aria-expanded="false">☰</button>
      <nav class="nav" aria-label="Разделы">${S.nav.map((x) => `<a href="${href(x.page)}" data-nav="${x.page}">${esc(x.label)}</a>`).join("")}</nav>
      ${cta()}
    </div></header>`;
  }
  function footer() {
    return `<footer class="ftr"><div class="wrap">
      <div><b>${esc(S.name)}</b>${esc(S.address)}</div>
      <div><b>Телефон</b><span class="mono">${esc(S.phone)}</span></div>
      <div><b>Часы работы</b>${hoursShort()}</div>
      <div><b>© ${new Date().getFullYear()}</b>${esc(S.footer)}</div>
    </div></footer>${cta("btn fab")}`;
  }
  const pageTop = (eyebrow, title, lead) => `<section class="wrap page-top"><span class="eyebrow">${esc(eyebrow)}</span><h1>${esc(title)}</h1>${lead ? `<p class="lead">${esc(lead)}</p>` : ""}</section>`;
  const head = (eyebrow, title, lead) => `<div class="section-head"><span class="eyebrow">${esc(eyebrow)}</span><h2>${esc(title)}</h2>${lead ? `<p class="lead">${esc(lead)}</p>` : ""}</div>`;
  const reviews = () => `<div class="grid">${S.reviews.map((r) => `<blockquote class="card review" style="margin:0"><div class="stars" aria-label="${r.stars} из 5">${"★".repeat(r.stars)}${"☆".repeat(5 - r.stars)}</div><q>${esc(r.text)}</q><footer>${esc(r.name)} · ${esc(r.meta)}</footer></blockquote>`).join("")}</div><p class="note">${esc(S.reviewsNote)}</p>`;
  const ctaBand = (title, text) => `<section class="wrap section"><div class="cta-band tread"><span class="eyebrow">Онлайн-запись</span><h2>${esc(title)}</h2><p class="lead">${esc(text)}</p>${cta()}</div></section>`;

  // ===== Страницы =====
  const PAGES = {
    home: () => `
      <section class="hero"><div class="wrap">
        <div class="hero-copy">
          <span class="marking">${esc(S.hero.badge)} <b>${esc(S.hero.marking)}</b></span>
          <h1>${esc(S.hero.title)} <em>${esc(S.hero.accent)}</em></h1>
          <p class="lead">${esc(S.hero.text)}</p>
          <div class="actions">${cta()}<a class="btn ghost" href="${href("services")}">${esc(S.hero.secondary)}</a></div>
          <div class="stats">${S.hero.stats.map((s) => `<div class="stat"><b class="mono">${esc(s.value)}</b><span>${esc(s.label)}</span></div>`).join("")}</div>
        </div>
        <div class="tire">${art(S.hero.marking, S.hero.ringText)}</div>
      </div></section>
      <div class="road"></div>
      <section class="wrap section">
        ${head(S.home.pricesEyebrow, S.home.pricesTitle, S.calc.note)}
        <div class="quick">${S.home.quick.map((q) => `<a href="${href(q.page)}"><div>${esc(q.title)}<small>${esc(q.sub)}</small></div><span class="price">${esc(q.price)}</span></a>`).join("")}</div>
      </section>
      <section class="tread"><div class="wrap section">
        ${head("Почему мы", S.home.whyTitle)}
        <div class="grid">${S.why.map((w, i) => `<div class="card"><span class="why-n">${i + 1}</span><h3>${esc(w.title)}</h3><p>${esc(w.text)}</p></div>`).join("")}</div>
      </div></section>
      <section class="wrap section">
        ${head(S.home.stepsEyebrow, S.home.stepsTitle)}
        <div class="steps">${S.steps.map((s) => `<div class="step"><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p></div>`).join("")}</div>
      </section>
      <section class="wrap section">${head("Отзывы", "Что говорят клиенты")}${reviews()}</section>
      ${ctaBand(S.home.cta.title, S.home.cta.text)}`,

    services: () => {
      const C = S.calc;
      return `
      ${pageTop("Услуги и цены", C.pageTitle, C.note)}
      <section class="wrap section">
        <div class="table-wrap"><table>
          <thead><tr><th>${esc(C.rowHead)}</th>${C.variants.map((v) => `<th>${esc(v.label)}</th>`).join("")}</tr></thead>
          <tbody>${C.rows.map((r) => `<tr><td class="r">${esc(r.key)}</td>${C.variants.map((v) => `<td class="p">${r.prices[v.id] ? rub(r.prices[v.id]) : "—"}</td>`).join("")}</tr>`).join("")}</tbody>
        </table></div>
        <div class="table-wrap"><table>
          <thead><tr><th>Дополнительно</th><th>Цена</th></tr></thead>
          <tbody>${C.extras.map((e) => `<tr><td>${esc(e.label)}</td><td class="p">${rub(e.price)} / ${esc(e.per)}</td></tr>`).join("")}</tbody>
        </table></div>
      </section>
      <section class="tread" id="calc"><div class="wrap section">
        ${head("Калькулятор", "Посчитайте стоимость заранее", C.lead)}
        <div class="calc">
          <form class="calc-form" id="calc-form">
            <fieldset class="field"><legend>${esc(C.variantLabel)}</legend><div class="chips">${C.variants.map((v, i) => `<label class="chip"><input type="radio" name="variant" id="car-${esc(v.id)}" value="${esc(v.id)}" ${i === 0 ? "checked" : ""}><span>${esc(v.label)}</span></label>`).join("")}</div></fieldset>
            <fieldset class="field"><legend>${esc(C.rowLabel)}</legend><div class="chips">${C.rows.map((r) => `<label class="chip"><input type="radio" name="row" id="r-${esc(r.key)}" value="${esc(r.key)}" ${r.key === C.defaultRow ? "checked" : ""}><span>${esc(r.key)}</span></label>`).join("")}</div></fieldset>
            <fieldset class="field"><legend>Дополнительно</legend>${C.extras.map((e) => `<label class="check"><input type="checkbox" name="extra" id="x-${esc(e.id)}" value="${esc(e.id)}"><span>${esc(e.label)}</span><small>${rub(e.price)} / ${esc(e.per)}</small></label>`).join("")}</fieldset>
          </form>
          <aside class="total" aria-live="polite"><span class="eyebrow" style="color:inherit">Итого</span><div class="sum mono" id="calc-sum">—</div><div id="calc-time"></div><ul id="calc-list"></ul>${cta()}</aside>
        </div>
      </div></section>
      <section class="wrap section">${head("Вопросы", "Частые вопросы")}<div class="faq">${S.faq.map((f) => `<details><summary>${esc(f.q)}</summary><p>${esc(f.a)}</p></details>`).join("")}</div></section>
      ${ctaBand(C.cta.title, C.cta.text)}`;
    },

    storage: () => `
      ${pageTop(S.storage.eyebrow, S.storage.title, S.storage.lead)}
      <section class="wrap section"><div class="plans">${S.storage.plans.map((p) => `<div class="card plan ${p.featured ? "featured" : ""}">${p.featured ? `<span class="tag">Чаще выбирают</span>` : ""}<h3>${esc(p.title)}</h3><div class="big">${esc(p.price)}</div><p>${esc(p.per)}</p><ul>${p.items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div>`).join("")}</div></section>
      <section class="tread"><div class="wrap section">${head("Что входит", S.storage.includedTitle)}<ul class="incl">${S.storage.included.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div></section>
      ${ctaBand(S.storage.cta.title, S.storage.cta.text)}`,

    gallery: () => `
      ${pageTop("Наши работы", S.gallery.title, S.gallery.note)}
      <section class="wrap section">
        <div class="filters" role="group" aria-label="Фильтр работ">${S.gallery.filters.map((f, i) => `<button type="button" data-filter="${esc(f)}" aria-pressed="${i === 0}">${esc(f)}</button>`).join("")}</div>
        <div class="gallery">${S.gallery.items.map((g, i) => `<figure class="shot" data-tag="${esc(g.tag)}"><div class="ph" style="background:var(${["--asphalt-2", "--asphalt-3", "--asphalt-2"][i % 3]})">${g.img ? `<img src="${esc(g.img)}" alt="${esc(g.title)}" loading="lazy">` : art(g.title, "")}<span class="lbl">${esc(g.tag)}</span></div><figcaption><b>${esc(g.title)}</b><small>${esc(g.size)}</small></figcaption></figure>`).join("")}</div>
      </section>
      <section class="wrap section">${head("Отзывы", "Что говорят клиенты")}${reviews()}</section>`,

    contacts: () => {
      const st = openStatus(), n = mskNow(), days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"];
      const map = SINGLE
        ? `<div class="map mapcard"><div class="pin"></div><p>${esc(S.address)}</p><a class="btn" href="https://yandex.ru/maps/?text=${encodeURIComponent(S.address)}" target="_blank" rel="noopener">Открыть на Яндекс.Картах</a></div>`
        : (() => { const { lat, lon } = S.map, d = 0.006; return `<div class="map"><iframe title="Карта" loading="lazy" src="https://www.openstreetmap.org/export/embed.html?bbox=${lon - d},${lat - d / 2},${lon + d},${lat + d / 2}&layer=mapnik&marker=${lat},${lon}"></iframe></div>`; })();
      return `
      ${pageTop("Контакты", "Как нас найти")}
      <section class="wrap section"><div class="contacts">
        <div class="card" style="gap:18px">
          <span class="status ${st.open ? "open" : ""}"><i></i>${esc(st.text)}</span>
          <div><span class="eyebrow">Адрес</span><p style="font-size:1.15rem;margin-top:6px">${esc(S.address)}</p><p class="note" style="margin-top:6px">${esc(S.directions)}</p></div>
          <div><span class="eyebrow">Телефон</span><div style="margin-top:6px"><span class="phone">${esc(S.phone)}</span></div></div>
          <div><span class="eyebrow">Часы работы</span><table class="hours"><tbody>${days.map((d, i) => `<tr class="${i === n.wd ? "today" : ""}"><td>${d}</td><td>${S.hours[i] ? S.hours[i].join("–") : "выходной"}</td></tr>`).join("")}</tbody></table></div>
          ${cta()}
        </div>
        ${map}
      </div></section>`;
    },
  };

  // ===== Интерактив =====
  function initCalc(root) {
    const form = root.querySelector("#calc-form");
    if (!form) return;
    const C = S.calc;
    const update = () => {
      const v = form.querySelector("[name=variant]:checked").value;
      // строки без цены для выбранного варианта недоступны
      form.querySelectorAll("[name=row]").forEach((r) => { r.disabled = !C.rows.find((x) => x.key === r.value).prices[v]; });
      let picked = form.querySelector("[name=row]:checked");
      if (!picked || picked.disabled) { picked = form.querySelector("[name=row]:not(:disabled)"); picked.checked = true; }
      const row = C.rows.find((x) => x.key === picked.value);
      const lines = [[C.baseLine.replace("{row}", row.key), row.prices[v]]];
      form.querySelectorAll("[name=extra]:checked").forEach((x) => {
        const e = C.extras.find((y) => y.id === x.value);
        lines.push(e.perUnit && C.units > 1 ? [`${e.label} × ${C.units}`, e.price * C.units] : [e.label, e.price]);
      });
      const total = lines.reduce((s, l) => s + l[1], 0);
      root.querySelector("#calc-sum").textContent = rub(total);
      root.querySelector("#calc-time").textContent = `≈ ${row.minutes} ${C.timeText}`;
      root.querySelector("#calc-list").innerHTML = lines.map((l) => `<li>${esc(l[0])} — ${rub(l[1])}</li>`).join("");
    };
    form.addEventListener("change", update);
    update();
  }
  function initGallery(root) {
    const btns = root.querySelectorAll("[data-filter]");
    btns.forEach((b) => b.addEventListener("click", () => {
      btns.forEach((x) => x.setAttribute("aria-pressed", x === b));
      root.querySelectorAll(".shot").forEach((s) => { s.hidden = b.dataset.filter !== S.gallery.filters[0] && s.dataset.tag !== b.dataset.filter; });
    }));
  }

  // ===== Сборка =====
  // цвета/шрифты ниши: SITE.theme = { "--marking": "#...", ... } переопределяет переменные из style.css
  Object.entries(S.theme || {}).forEach(([k, v]) => document.documentElement.style.setProperty(k, v));
  const mains = document.querySelectorAll("main[data-page]");
  document.getElementById("site-header").innerHTML = header();
  document.getElementById("site-footer").innerHTML = footer();
  mains.forEach((m) => { m.innerHTML = PAGES[m.dataset.page](); initCalc(m); initGallery(m); });

  const nav = document.querySelector(".nav"), burger = document.querySelector(".burger");
  burger.addEventListener("click", () => { const o = nav.classList.toggle("open"); burger.setAttribute("aria-expanded", o); });
  const setActive = (page) => {
    document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === page));
    const label = S.nav.find((x) => x.page === page);
    document.title = page === "home" || !label ? S.name : `${label.label} · ${S.name}`;
  };

  if (SINGLE) {
    const route = () => {
      const page = PAGES[location.hash.slice(1)] ? location.hash.slice(1) : "home";
      mains.forEach((m) => { m.hidden = m.dataset.page !== page; });
      setActive(page); nav.classList.remove("open"); burger.setAttribute("aria-expanded", "false");
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", route);
    route();
  } else {
    setActive(mains[0].dataset.page);
  }
})();
