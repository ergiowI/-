// Тесты симулятора бота demo/bot.html: та же логика, что в настоящем боте, но в браузере.
const { test, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { launch, open } = require("./helpers");

let browser;
before(async () => { browser = await launch(); });
after(async () => { await browser.close(); });

// Утро понедельника по Москве: свободного времени на сегодня и неделю вперёд достаточно
const CLOCK = "2030-01-14T05:00:00Z";

async function setup() {
  const p = await open(browser, "demo/bot.html", { width: 1280, clock: CLOCK });
  p.kb = () => p.locator("#c-feed .ikb:not(.dead)").last().locator("button"); // кнопки последнего сообщения клиента
  p.lastC = () => p.$$eval("#c-feed .msg", (m) => m.at(-1).innerText);
  p.lastO = () => p.$$eval("#o-feed .msg", (m) => m.at(-1).innerText);
  p.say = async (text) => { await p.fill("#c-input", text); await p.press("#c-input", "Enter"); };
  p.menu = (label) => p.locator("#c-rkb button", { hasText: label }).click();
  p.owner = (label) => p.locator("#o-feed .ikb:not(.dead) button", { hasText: label }).last().click();
  return p;
}

// Запись: услуга по номеру кнопки, первый день, время по тексту
async function book(p, { service = 0, time = "12:00", known = false, comment } = {}) {
  await p.menu("Записаться");
  await p.kb().nth(service).click();
  await p.kb().first().click();
  await p.kb().filter({ hasText: new RegExp(`^${time}$`) }).click();
  if (known) await p.kb().filter({ hasText: "Да, это я" }).click();
  else { await p.say("Иван"); await p.locator("#c-rkb button", { hasText: "Поделиться" }).click(); }
  if (comment) await p.say(comment);
  else await p.kb().filter({ hasText: "Пропустить" }).click();
  await p.kb().filter({ hasText: "Записаться" }).click();
}

test("симулятор: запись доходит до владельца, подтверждение доходит до клиента", async () => {
  const p = await setup();
  await book(p, { comment: "Kia Rio R15" });
  assert.match(await p.lastC(), /Заявка отправлена/);
  assert.match(await p.lastO(), /Новая запись[\s\S]*Kia Rio R15[\s\S]*Иван/);
  await p.owner("Подтвердить");
  assert.match(await p.lastC(), /запись подтверждена/);
  assert.deepEqual(p.errors, []);
  await p.close();
});

test("симулятор: занятое время не предлагается", async () => {
  const p = await setup();
  await book(p, { time: "12:00" }); // переобувка 60 минут: 12:00–13:00
  await p.menu("Записаться");
  await p.kb().nth(0).click();
  await p.kb().first().click();
  const times = await p.kb().allTextContents();
  assert.ok(times.includes("11:00") && times.includes("13:00"));
  for (const t of ["11:30", "12:00", "12:30"]) assert.ok(!times.includes(t), `${t} должно быть занято`);
  await p.close();
});

test("симулятор: если время заняли параллельно — запись не создаётся", async () => {
  const p = await setup();
  await p.menu("Записаться");
  await p.kb().nth(2).click();
  await p.kb().first().click();
  await p.kb().filter({ hasText: /^12:00$/ }).click();
  await p.click("#other"); // другой клиент занял то же время
  await p.say("Иван");
  await p.locator("#c-rkb button", { hasText: "Поделиться" }).click();
  await p.kb().filter({ hasText: "Пропустить" }).click();
  await p.kb().filter({ hasText: "Записаться" }).click();
  assert.match(await p.$$eval("#c-feed .msg", (m) => m.at(-1).innerText), /только что заняли/);
  await p.close();
});

test("симулятор: повторного клиента не спрашивают имя и телефон", async () => {
  const p = await setup();
  await book(p, { time: "10:00" });
  await p.menu("Записаться");
  await p.kb().nth(2).click();
  await p.kb().first().click();
  await p.kb().filter({ hasText: /^15:00$/ }).click();
  assert.match(await p.lastC(), /Записать вас как Иван/);
  await p.close();
});

test("симулятор: перенос записи уходит владельцу на повторное подтверждение", async () => {
  const p = await setup();
  await book(p, { service: 2, time: "10:00" });
  await p.owner("Подтвердить");
  await p.menu("Мои записи");
  await p.kb().filter({ hasText: "Перенести" }).click();
  await p.kb().nth(1).click(); // второй день
  await p.kb().filter({ hasText: /^15:00$/ }).click();
  assert.match(await p.lastC(), /перенесена и ждёт подтверждения[\s\S]*15:00/);
  assert.match(await p.lastO(), /Перенос записи[\s\S]*Было[\s\S]*10:00[\s\S]*Стало[\s\S]*15:00/);
  await p.close();
});

test("симулятор: оценка после визита и /stats у владельца", async () => {
  const p = await setup();
  await book(p);
  await p.owner("Подтвердить");
  await p.click("#visit");
  await p.kb().filter({ hasText: "4 ⭐" }).click();
  assert.match(await p.lastO(), /⭐⭐⭐⭐ Оценка визита/);
  await p.locator("#o-rkb button", { hasText: "/stats" }).click();
  assert.match(await p.lastO(), /Средняя оценка: 4\.0/);
  await p.close();
});

test("симулятор: нет горизонтальной прокрутки на телефоне", async () => {
  const p = await open(browser, "demo/bot.html", { width: 375, clock: CLOCK });
  assert.ok((await p.evaluate(() => document.documentElement.scrollWidth)) <= 375);
  await p.close();
});

test("симулятор: переключение на груминг — другие услуги, комментарий с 🐾, понедельник выходной", async () => {
  const p = await setup(); // CLOCK — понедельник
  await p.click('[data-niche="grooming"]');
  assert.equal(await p.textContent("h1 .biz-name"), "Груминг «Пушистый хвост»");
  await p.menu("Записаться");
  const services = await p.kb().allTextContents();
  assert.ok(services.some((s) => s.startsWith("Комплекс: мелкие породы")));
  await p.kb().nth(1).click();
  const days = await p.kb().allTextContents();
  assert.ok(days.every((d) => !d.includes("(пн)")), "в понедельник салон не работает");
  await p.kb().first().click();
  await p.kb().first().click();
  await p.say("Анна");
  await p.locator("#c-rkb button", { hasText: "Поделиться" }).click();
  assert.match(await p.lastC(), /породу и кличку/);
  await p.say("шпиц Боня");
  assert.match(await p.lastC(), /🐾 шпиц Боня[\s\S]*Анна/);
  await p.kb().filter({ hasText: "Записаться" }).click();
  assert.match(await p.lastO(), /Комплекс: мелкие породы — 2800 ₽/);
  assert.deepEqual(p.errors, []);
  await p.close();
});

test("симулятор: ссылка #grooming сразу открывает груминг", async () => {
  const p = await open(browser, "demo/bot.html", { hash: "#grooming", clock: CLOCK });
  assert.equal(await p.getAttribute('[data-niche="grooming"]', "aria-pressed"), "true");
  assert.match(await p.$$eval("#c-feed .msg", (m) => m[1].innerText), /Пушистый хвост/);
  await p.close();
});
