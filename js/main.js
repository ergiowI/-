// Рендерит страницу из объекта SITE (js/config.js). Здесь менять ничего не нужно.
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

document.title = SITE.name;
$("logo").textContent = SITE.name;
$("hero-title").textContent = SITE.name;
$("hero-text").textContent = SITE.tagline;
document.querySelectorAll("[data-cta]").forEach((a) => { a.href = SITE.botLink; a.textContent = SITE.ctaText; });

$("services-title").textContent = SITE.servicesTitle;
$("services-list").innerHTML = SITE.services
  .map((s) => `<li><div>${esc(s.name)}<small>${esc(s.duration)}</small></div><span class="price">${esc(s.price)}</span></li>`)
  .join("");

$("why-title").textContent = SITE.whyTitle;
$("why-list").innerHTML = SITE.why
  .map((w) => `<div class="card"><div class="icon">${esc(w.icon)}</div><h3>${esc(w.title)}</h3><p>${esc(w.text)}</p></div>`)
  .join("");

$("works-title").textContent = SITE.worksTitle;
// если в works указан путь к картинке (.jpg/.png/.webp), показываем фото, иначе заглушку с подписью
$("works-list").innerHTML = SITE.works
  .map((w) => (/\.(jpe?g|png|webp)$/i.test(w) ? `<div class="work"><img src="${esc(w)}" alt="Наша работа" loading="lazy"></div>` : `<div class="work">${esc(w)}</div>`))
  .join("");

$("reviews-title").textContent = SITE.reviewsTitle;
$("reviews-list").innerHTML = SITE.reviews
  .map((r) => `<div class="card"><div class="stars">${"★".repeat(r.stars)}${"☆".repeat(5 - r.stars)}</div><p>«${esc(r.text)}»</p><strong>${esc(r.name)}</strong></div>`)
  .join("");
$("reviews-note").textContent = SITE.reviewsNote;

$("contacts-title").textContent = SITE.contactsTitle;
const tel = SITE.phone.replace(/[^\d+]/g, "");
$("contacts-list").innerHTML =
  `<li>📍 ${esc(SITE.address)}</li><li>📞 <a href="tel:${esc(tel)}">${esc(SITE.phone)}</a></li><li>🕒 ${esc(SITE.hours)}</li>`;
const { lat, lon } = SITE.map, d = 0.006;
$("map").src = `https://www.openstreetmap.org/export/embed.html?bbox=${lon - d},${lat - d / 2},${lon + d},${lat + d / 2}&layer=mapnik&marker=${lat},${lon}`;
$("footer").textContent = `© ${new Date().getFullYear()} ${SITE.name} · ${SITE.footer}`;
