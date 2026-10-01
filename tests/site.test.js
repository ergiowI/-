// Тесты сайта в настоящем браузере: страницы, адаптив, калькулятор, галерея, «открыто/закрыто», демо в одном файле.
const { test, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { launch, open } = require("./helpers");

const PAGES = { index: "home", services: "services", storage: "storage", gallery: "gallery", contacts: "contacts" };
let browser;
before(async () => { browser = await launch(); });
after(async () => { await browser.close(); });

// ---------- все страницы ----------

for (const [file, page] of Object.entries(PAGES)) {
  test(`${file}.html: рендерится без ошибок, меню и кнопка записи на месте`, async () => {
    const p = await open(browser, `${file}.html`);
    assert.deepEqual(p.errors, []);
    assert.ok((await p.textContent("main")).trim().length > 100, "страница пустая");
    assert.equal(await p.getAttribute(".nav a.active", "data-nav"), page);
    assert.equal(await p.locator(".nav a").count(), 5);
    const cta = await p.getAttribute(".hdr .btn", "href");
    assert.match(cta, /^https:\/\/t\.me\//);
    await p.close();
  });

  for (const width of [375, 1280]) {
    test(`${file}.html: нет горизонтальной прокрутки на ширине ${width}`, async () => {
      const p = await open(browser, `${file}.html`, { width });
      const scroll = await p.evaluate(() => document.documentElement.scrollWidth);
      assert.ok(scroll <= width, `ширина страницы ${scroll} > ${width}`);
      await p.close();
    });
  }
}

test("ссылки меню ведут на существующие страницы", async () => {
  const p = await open(browser, "index.html");
  const hrefs = await p.$$eval(".nav a", (as) => as.map((a) => a.getAttribute("href")));
  assert.deepEqual(hrefs, ["index.html", "services.html", "storage.html", "gallery.html", "contacts.html"]);
  await p.close();
});

test("на телефоне меню открывается кнопкой ☰, плавающая кнопка записи видна", async () => {
  const p = await open(browser, "index.html", { width: 375 });
  assert.equal(await p.isVisible(".nav"), false);
  await p.click(".burger");
  assert.equal(await p.isVisible(".nav"), true);
  assert.equal(await p.getAttribute(".burger", "aria-expanded"), "true");
  assert.equal(await p.isVisible(".fab"), true);
  await p.close();
});

test("на компьютере плавающая кнопка скрыта", async () => {
  const p = await open(browser, "index.html", { width: 1280 });
  assert.equal(await p.isVisible(".fab"), false);
  await p.close();
});

// ---------- калькулятор ----------

const sum = (p) => p.textContent("#calc-sum");
const pick = (p, id) => p.click(`label:has(#${id})`);

test("калькулятор: по умолчанию легковой R16 = 2 400 ₽, 45 минут", async () => {
  const p = await open(browser, "services.html");
  assert.equal(await sum(p), "2 400 ₽");
  assert.match(await p.textContent("#calc-time"), /45 минут/);
  await p.close();
});

test("калькулятор: кроссовер R16 + ремонт прокола = 3 300 ₽", async () => {
  const p = await open(browser, "services.html");
  await pick(p, "car-suv");
  await pick(p, "x-repair");
  assert.equal(await sum(p), "3 300 ₽");
  await p.close();
});

test("калькулятор: услуги «за колесо» умножаются на 4", async () => {
  const p = await open(browser, "services.html");
  await pick(p, "x-valve"); // 100 × 4
  await pick(p, "x-utilization"); // 150 × 4
  assert.equal(await sum(p), "3 400 ₽");
  await p.close();
});

test("калькулятор: R17+ занимает 70 минут", async () => {
  const p = await open(browser, "services.html");
  await pick(p, "r-R19");
  assert.equal(await sum(p), "3 200 ₽");
  assert.match(await p.textContent("#calc-time"), /70 минут/);
  await p.close();
});

test("калькулятор: для кроссовера R13/R14 недоступны, выбор перескакивает на доступный радиус", async () => {
  const p = await open(browser, "services.html");
  await pick(p, "r-R13");
  assert.equal(await sum(p), "2 000 ₽");
  await pick(p, "car-suv");
  assert.equal(await p.isDisabled("#r-R13"), true);
  assert.equal(await p.isDisabled("#r-R14"), true);
  assert.equal(await sum(p), "2 800 ₽"); // первый доступный — R15
  await p.close();
});

test("таблица цен совпадает с конфигом", async () => {
  const p = await open(browser, "services.html");
  const rows = await p.$$eval(".table-wrap:first-of-type tbody tr", (trs) => trs.length);
  const cfg = await p.evaluate(() => SITE.prices.length);
  assert.equal(rows, cfg);
  await p.close();
});

// ---------- галерея ----------

test("галерея: фильтр показывает только выбранный вид работ", async () => {
  const p = await open(browser, "gallery.html");
  const visible = () => p.$$eval(".shot", (s) => s.filter((x) => !x.hidden).map((x) => x.dataset.tag));
  assert.equal((await visible()).length, 9);
  await p.click('[data-filter="Ремонт"]');
  assert.deepEqual(await visible(), ["Ремонт", "Ремонт"]);
  assert.equal(await p.getAttribute('[data-filter="Ремонт"]', "aria-pressed"), "true");
  await p.click('[data-filter="Все"]');
  assert.equal((await visible()).length, 9);
  await p.close();
});

// ---------- контакты: «открыто / закрыто» по Москве ----------

// 2030-01-14 — понедельник; время в UTC, Москва = UTC+3
const cases = [
  ["пн 12:00", "2030-01-14T09:00:00Z", true, "Открыто до 20:00"],
  ["пн 08:00", "2030-01-14T05:00:00Z", false, "откроемся сегодня в 09:00"],
  ["пн 21:00", "2030-01-14T18:00:00Z", false, "откроемся завтра в 09:00"],
  ["пт 21:00 → сб с 10:00", "2030-01-18T18:00:00Z", false, "откроемся завтра в 10:00"],
  ["сб 17:59", "2030-01-19T14:59:00Z", true, "Открыто до 18:00"],
];
for (const [name, clock, isOpen, text] of cases) {
  test(`контакты: ${name}`, async () => {
    const p = await open(browser, "contacts.html", { clock });
    assert.equal(await p.evaluate(() => document.querySelector(".status").classList.contains("open")), isOpen);
    assert.match(await p.textContent(".status"), new RegExp(text));
    await p.close();
  });
}

test("контакты: сегодняшний день подсвечен в часах работы", async () => {
  const p = await open(browser, "contacts.html", { clock: "2030-01-16T09:00:00Z" }); // среда
  assert.equal(await p.textContent(".hours tr.today td"), "Среда");
  await p.close();
});

// ---------- сезонный баннер ----------

for (const [clock, word] of [["2030-04-10T09:00:00Z", "Весенний"], ["2030-10-10T09:00:00Z", "Осенняя"], ["2030-07-10T09:00:00Z", "Межсезонье"]]) {
  test(`баннер: ${word}`, async () => {
    const p = await open(browser, "index.html", { clock });
    assert.match(await p.textContent(".season"), new RegExp(word));
    await p.close();
  });
}

// ---------- демо в одном файле ----------

test("demo/site.html: страницы переключаются по #якорю, видна только одна", async () => {
  const p = await open(browser, "demo/site.html", { hash: "#storage" });
  assert.deepEqual(p.errors, []);
  const shown = () => p.$$eval("main[data-page]", (m) => m.filter((x) => !x.hidden).map((x) => x.dataset.page));
  assert.deepEqual(await shown(), ["storage"]);
  await p.click('.nav a[data-nav="contacts"]');
  await p.waitForFunction(() => location.hash === "#contacts" && !document.querySelector('main[data-page="contacts"]').hidden);
  assert.deepEqual(await shown(), ["contacts"]);
  assert.equal(await p.getAttribute(".nav a.active", "data-nav"), "contacts");
  assert.equal(await p.isVisible(".mapcard"), true); // в одном файле вместо iframe-карты — ссылка
  await p.close();
});

test("demo/site.html собран из актуальных исходников", async () => {
  const { execFileSync } = require("node:child_process");
  const fs = require("node:fs");
  const path = require("node:path");
  const os = require("node:os");
  const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "site-")), "site.html");
  execFileSync("python3", [path.join(__dirname, "..", "tools", "build_demo.py"), tmp]);
  const fresh = fs.readFileSync(tmp, "utf8");
  const committed = fs.readFileSync(path.join(__dirname, "..", "demo", "site.html"), "utf8");
  assert.ok(fresh === committed, "запустите python tools/build_demo.py и закоммитьте demo/site.html");
});
