// Общие помощники: браузер Chromium и открытие страниц сайта по file://
const path = require("node:path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const url = (file, hash = "") => "file://" + path.join(ROOT, file) + hash;

async function launch() {
  // в облачной среде Chromium лежит в /opt/pw-browsers, локально — там, куда поставил `npx playwright install`
  const fs = require("node:fs");
  const exe = "/opt/pw-browsers/chromium";
  return chromium.launch(fs.existsSync(exe) ? { executablePath: exe } : {});
}

// Открывает страницу и собирает JS-ошибки. clock — время "сейчас" для страницы (Date), опционально.
async function open(browser, file, { width = 1280, hash = "", clock } = {}) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  // внешние ресурсы (шрифты, карта) не нужны для тестов и в CI могут быть недоступны
  await page.route(/^https?:\/\//, (r) => r.abort());
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push(e.message));
  if (clock) await page.clock.setFixedTime(new Date(clock));
  await page.goto(url(file, hash));
  return page;
}

module.exports = { launch, open, url, ROOT };
