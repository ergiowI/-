// Скрины и проверка демо. Запуск из корня репозитория:
//   node tools/screens.js site bikar-site L1-bikar
//   node tools/screens.js bot olga-massage-bot L2-olga
// Делает screens/<имя>-glavnaya.png и screens/<имя>-zayavka.png, для бота ещё banner.png и avatar.png,
// и проверяет: нет ошибок JS, нет горизонтальной прокрутки, запись проходит.
let pw; try { pw = require('playwright'); } catch (e) { pw = require('/opt/node-tools/node_modules/playwright'); }
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const [kind, slug, name] = process.argv.slice(2);
if (!['site', 'bot'].includes(kind) || !slug || !name) { console.log('usage: node tools/screens.js site|bot <папка> <имя скрина>'); process.exit(1); }
const url = 'file://' + path.join(ROOT, slug, kind === 'site' ? 'index.html' : 'demo.html');
(async () => {
  const b = await pw.chromium.launch();
  if (kind === 'bot') for (const [f, w, h] of [['banner', 1280, 640], ['avatar', 640, 640]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto('file://' + path.join(__dirname, '.build', `${f}-${slug}.html`)); await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(ROOT, slug, f + '.png') }); await p.close();
  }
  for (const [w, h, shots] of [[1280, 900, false], [390, 844, true]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: shots ? 2 : 1 });
    const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto(url); await p.waitForTimeout(500);
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    let ok;
    if (kind === 'site') {
      if (shots) await p.screenshot({ path: path.join(ROOT, 'screens', name + '-glavnaya.png') });
      await p.locator('#fService button').nth(2).click();
      await p.locator('#fTime button:not([disabled])').nth(1).click();
      await p.fill('#fName', 'Андрей'); await p.fill('#fPhone', '+7 921 555-12-34');
      await p.locator('#send').click();
      ok = await p.locator('.done').count() > 0;
      if (shots) await p.locator('#summary').screenshot({ path: path.join(ROOT, 'screens', name + '-zayavka.png') });
    } else {
      await p.locator('#steps .services .opt').nth(2).click();
      await p.evaluate(() => document.getElementById('app').scrollTop = 0); await p.waitForTimeout(400);
      if (shots) await p.locator('.phone').screenshot({ path: path.join(ROOT, 'screens', name + '-glavnaya.png') });
      await p.locator('#steps .times .opt:not([disabled])').nth(1).click();
      await p.locator('#go').click(); await p.waitForTimeout(600);
      ok = await p.locator('#done').isVisible();
      if (shots) await p.locator('.side .card').first().screenshot({ path: path.join(ROOT, 'screens', name + '-zayavka.png') });
    }
    console.log(`${slug} ${w}px: запись ${ok ? 'ок' : 'НЕ ПРОШЛА'}, ширина ${sw}${sw > w ? ' (ЕСТЬ ГОРИЗОНТАЛЬНАЯ ПРОКРУТКА)' : ''}${errs.length ? ', ошибки: ' + errs.join('; ') : ''}`);
    await p.close();
  }
  if (kind === 'site') {
    const p = await b.newPage({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
    await p.goto(url);
    console.log(`${slug} без JS: форма скрыта — ${!(await p.locator('#bookForm').isVisible())}, кнопка WhatsApp — ${await p.locator('#summary a').getAttribute('href')}`);
    await p.close();
  }
  await b.close();
})();
