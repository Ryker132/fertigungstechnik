const COURSE = window.COURSE;

const INDEX = [];
for (const mod of COURSE.modules) {
  for (const sec of mod.sections) {
    sec.slides.forEach((slide, i) => {
      INDEX.push({
        mod,
        sec,
        i,
        slide,
        hay: `${slide.title} ${slide.plain}`.toLowerCase(),
      });
    });
  }
}

const app = document.getElementById("app");
const lightbox = document.getElementById("lightbox");

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));
}

function imgOf(file, n) {
  return `slides/${file}/${String(n).padStart(3, "0")}.jpg`;
}

function findMod(id) {
  return COURSE.modules.find((mod) => mod.id === id);
}

function findSec(mod, id) {
  return mod?.sections.find((sec) => sec.id === id);
}

function groupsOf(slides) {
  const groups = [];
  slides.forEach((slide, index) => {
    const key = slide.title.replace(/\s+/g, " ").trim().toLowerCase();
    const last = groups[groups.length - 1];
    if (last && last.key === key) last.end = index;
    else groups.push({ key, title: slide.title, start: index, end: index });
  });
  return groups;
}

function slideCount(mod) {
  return mod.sections.reduce((sum, sec) => sum + sec.slides.length, 0);
}

function globalPos(modId, secId, index) {
  let at = 0;
  let total = 0;
  let current = 0;
  for (const mod of COURSE.modules) {
    for (const sec of mod.sections) {
      for (let i = 0; i < sec.slides.length; i += 1) {
        if (mod.id === modId && sec.id === secId && i === index) current = total;
        total += 1;
      }
    }
  }
  return { current, total, at };
}

function hrefSlide(mod, sec, index) {
  return `#/m/${mod.id}/s/${sec.id}/i/${index}`;
}

function shell(inner, modId) {
  document.body.dataset.mod = modId || "";
  const route = parseHash();
  let meter = "";
  if (route.view === "slide") {
    const pos = globalPos(route.mod, route.sec, route.i);
    const pct = pos.total ? ((pos.current + 1) / pos.total) * 100 : 0;
    meter = `<div class="meter"><span style="width:${pct}%"></span></div>`;
  }
  app.innerHTML = `
    <header class="top">
      <a class="brand" href="#/">
        <strong>Fertigungstechnik I</strong>
        <span>entlang der Folien</span>
      </a>
      <form class="search" id="qform">
        <input name="q" type="search" placeholder="Begriff aus den Folien" aria-label="Suche" value="${esc(route.view === "search" ? route.q : "")}">
        <button type="submit">Suchen</button>
      </form>
      ${meter}
    </header>
    <main class="wrap">${inner}</main>
  `;
  window.scrollTo(0, 0);
}

function parseHash() {
  const parts = (location.hash.replace(/^#/, "") || "/").split("/").filter(Boolean);
  if (parts[0] === "m" && parts[1]) {
    if (parts[2] === "s" && parts[3]) {
      if (parts[4] === "i" && parts[5] != null) {
        return { view: "slide", mod: parts[1], sec: parts[3], i: Number(parts[5]) || 0 };
      }
      return { view: "section", mod: parts[1], sec: parts[3] };
    }
    return { view: "module", mod: parts[1] };
  }
  if (parts[0] === "suche") {
    return { view: "search", q: decodeURIComponent(parts.slice(1).join("/")) };
  }
  return { view: "home" };
}

function renderEl(el) {
  if (el.t === "p") return `<p>${esc(el.text)}</p>`;
  if (el.t === "label") return `<p class="label">${esc(el.text)}</p>`;
  if (el.t === "source") return `<p class="source">${esc(el.text)}</p>`;
  if (el.t === "ul") return `<ul>${el.items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
  if (el.t === "ol") return `<ol>${el.items.map((item) => `<li>${esc(item)}</li>`).join("")}</ol>`;
  if (el.t === "cols") {
    return `<div class="cols">${el.cols.map((col) => `<div>${col.map(renderEl).join("")}</div>`).join("")}</div>`;
  }
  return "";
}

function renderBlocks(blocks) {
  let leadUsed = false;
  return blocks.map((el) => {
    if (!leadUsed && el.t === "p" && el.text.length > 80) {
      leadUsed = true;
      return `<p class="lead">${esc(el.text)}</p>`;
    }
    return renderEl(el);
  }).join("");
}

function frame(file, n, title) {
  const src = imgOf(file, n);
  return `
    <figure class="frame">
      <button type="button" data-zoom="${esc(src)}" data-alt="${esc(title)}" aria-label="Folie ${n} vergrößern">
        <img src="${esc(src)}" alt="${esc(title)}">
      </button>
      <figcaption class="cap"><span>Folie ${n}</span><span>Original vergrößern</span></figcaption>
    </figure>
  `;
}

function home() {
  const saved = localStorage.getItem("ft-atlas-hash");
  const din = COURSE.din.map((group) => {
    const body = `<span class="name">${esc(group.name)}</span><span class="verb">${esc(group.verb)}</span>`;
    if (!group.mod) return `<div class="tile off">${body}</div>`;
    return `<a href="#/m/${group.mod}">${body}</a>`;
  }).join("");

  const goals = COURSE.lernziele.map((item) => `<li>${esc(item)}</li>`).join("");
  const chips = COURSE.begriff.map((item) => `<span class="chip">${esc(item)}</span>`).join("");
  const sub = COURSE.subziele.map((item) => `<li>${esc(item)}</li>`).join("");
  const factors = COURSE.auswahl.map((group) => `
    <article class="factor">
      <h3>${esc(group.title)}</h3>
      <ul>${group.items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
    </article>
  `).join("");

  const gallery = COURSE.gallery.map((item) => `
    <figure>
      <button type="button" data-zoom="${esc(imgOf(item.file, item.n))}" data-alt="${esc(item.title)}">
        <img src="${esc(imgOf(item.file, item.n))}" alt="${esc(item.title)}">
      </button>
      <figcaption>
        <a href="${hrefSlide(findMod(item.mod), findSec(findMod(item.mod), item.sec), item.i)}">Folie ${item.n} · ${esc(item.title)}</a>
      </figcaption>
    </figure>
  `).join("");

  const head = COURSE.arten.columns.map((col) => `<th>${esc(col)}</th>`).join("");
  const rows = COURSE.arten.rows.map((row) => `
    <tr><th>${esc(row[0])}</th>${row.slice(1).map((cell) => `<td>${esc(cell)}</td>`).join("")}</tr>
  `).join("");

  const steps = COURSE.modules.map((mod) => {
    const gap = mod.id === "beschichten"
      ? `<div class="step gap-note"><span class="idx">DIN 8580</span><span><b>Fügen</b><small>Zusammenhalt vermehren. In den Inhaltsverzeichnissen genannt. Im Ordner liegt kein Foliensatz dazu.</small></span><span></span></div>`
      : "";
    return `${gap}<a class="step" href="#/m/${mod.id}">
      <span class="idx">${esc(mod.kicker)}</span>
      <span><b>${esc(mod.title)}</b><small>${esc(mod.verb)} ${slideCount(mod)} Folien · ${esc(mod.source)}</small></span>
      <span>Öffnen</span>
    </a>`;
  }).join("");

  shell(`
    <section class="hero">
      <div>
        <p class="kicker">${esc(COURSE.place)} · ${esc(COURSE.term)}</p>
        <h1>${esc(COURSE.title)}</h1>
        <p class="lede">Zuerst die Hauptgruppen, dann jedes Modul im Ganzen, danach jede Folie einzeln. Übernommen ist nur, was auf den Folien von ${esc(COURSE.professor)} steht.</p>
        <p class="meta"><strong>${esc(COURSE.school)}</strong><br>${esc(COURSE.program)}<br>${esc(COURSE.module)} · ${esc(COURSE.chair)}</p>
        ${saved ? `<p class="meta"><a class="btn" href="${esc(saved)}">Weiterlernen</a></p>` : ""}
      </div>
      <aside class="hero-side">
        <h2>Lernziele</h2>
        <ol>${goals}</ol>
      </aside>
    </section>

    <div class="section-head">
      <div>
        <h2>Einteilung der Fertigungsverfahren</h2>
        <p>DIN 8580, Folie 12. Fügen und Stoffeigenschaft ändern stehen auf der Folie, haben hier aber kein eigenes Modul.</p>
      </div>
    </div>
    <div class="din">${din}</div>

    <div class="section-head">
      <div>
        <h2>Was Fertigungstechnik beinhaltet</h2>
        <p>Folie 11</p>
      </div>
    </div>
    <div class="chips">${chips}</div>

    <div class="section-head">
      <div>
        <h2>Die Karten aus der Vorlesung</h2>
        <p>Dieselben Folien, unverändert. Antippen vergrößert sie.</p>
      </div>
    </div>
    <div class="gallery">${gallery}</div>

    <div class="section-head">
      <div>
        <h2>Auswahl und Vergleich der Fertigungsarten</h2>
        <p>Modul 7, vor den einzelnen Verfahren als Maßstab. Wortlaut der Folien 4 bis 6.</p>
      </div>
      <a class="btn ghost" href="#/m/grundlagen">Modul 7 ganz</a>
    </div>
    <div class="grid-2">
      <article class="card">
        <h3>Ziele</h3>
        <ul>${COURSE.ziele.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
        <h3>Sub-Ziele</h3>
        <ul>${sub}</ul>
      </article>
      <div class="factors">${factors}</div>
    </div>

    <div class="section-head">
      <div>
        <h2>Einteilungskriterien der Fertigungsarten</h2>
        <p>Folie 8 in Modul 7. Dieselbe Tabelle, zum Lesen gesetzt. Die Originalfolie liegt in der Kartenreihe oben.</p>
      </div>
    </div>
    <div class="card table-wrap">
      <table>
        <thead><tr><th>Einteilungskriterien</th>${head}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>

    <div class="section-head">
      <div>
        <h2>Dann jedes Modul</h2>
        <p>${INDEX.length} Folien in der Reihenfolge der Vorlesung.</p>
      </div>
    </div>
    <div class="path">${steps}</div>
    <p class="foot">Quellen auf den Folien bleiben Quellen. Es ist nichts aus Lehrbüchern ergänzt, was nicht auf der Folie steht.</p>
  `);
}

function moduleView(id) {
  const mod = findMod(id);
  if (!mod) return home();
  const sections = mod.sections.map((sec) => {
    const groups = groupsOf(sec.slides);
    const preview = groups.slice(0, 6).map((group) => group.title).join(" · ");
    const more = groups.length > 6 ? ` · und ${groups.length - 6} weitere` : "";
    return `<a href="#/m/${mod.id}/s/${sec.id}">
      <div class="toprow">
        <span><span class="code">${esc(sec.code || mod.source)}</span><br><b>${esc(sec.title)}</b></span>
        <span class="quiet">${sec.slides.length} Folien</span>
      </div>
      <p class="preview">${esc(preview)}${esc(more)}</p>
    </a>`;
  }).join("");
  shell(`
    <nav class="crumbs"><a href="#/">Überblick</a> <span>/</span> <span>${esc(mod.title)}</span></nav>
    <header class="mod-head">
      <p class="kicker" style="color:var(--accent)">${esc(mod.kicker)} · ${esc(mod.source)}</p>
      <h2>${esc(mod.title)}</h2>
      ${mod.verb ? `<p class="verb">${esc(mod.verb)}</p>` : ""}
      ${mod.definition ? `<p class="definition">${esc(mod.definition)}</p>` : ""}
    </header>
    <div class="section-head"><div><h2>Aufbau laut Inhaltsverzeichnis</h2><p>Zuerst der Abschnitt, danach jede Folie.</p></div></div>
    <div class="sec-list">${sections}</div>
  `, mod.id);
}

function sectionView(modId, secId) {
  const mod = findMod(modId);
  const sec = findSec(mod, secId);
  if (!sec) return moduleView(modId);
  const groups = groupsOf(sec.slides);
  const items = groups.map((group) => {
    const from = sec.slides[group.start].n;
    const to = sec.slides[group.end].n;
    const span = from === to ? `Folie ${from}` : `Folien ${from}–${to}`;
    return `<a href="${hrefSlide(mod, sec, group.start)}">
      <span class="dot"></span>
      <span>${esc(group.title)}</span>
      <span class="quiet">${span}</span>
    </a>`;
  }).join("");
  shell(`
    <nav class="crumbs">
      <a href="#/">Überblick</a> <span>/</span>
      <a href="#/m/${mod.id}">${esc(mod.title)}</a> <span>/</span>
      <span>${esc(sec.title)}</span>
    </nav>
    <header class="mod-head">
      <p class="code">${esc(sec.code)}</p>
      <h2>${esc(sec.title)}</h2>
      <p class="quiet">${sec.slides.length} Folien, in der Reihenfolge der Vorlesung. ${groups.length} Themenwechsel.</p>
    </header>
    <p><a class="btn" href="${hrefSlide(mod, sec, 0)}">Mit der ersten Folie beginnen</a></p>
    <div class="timeline">${items}</div>
  `, mod.id);
}

function neighbors(mod, sec, index) {
  const prev = index > 0 ? { href: hrefSlide(mod, sec, index - 1), label: "Zurück" } : { href: `#/m/${mod.id}/s/${sec.id}`, label: "Zur Übersicht" };
  if (index < sec.slides.length - 1) {
    return { prev, next: { href: hrefSlide(mod, sec, index + 1), label: "Weiter" } };
  }
  const sIndex = mod.sections.findIndex((item) => item.id === sec.id);
  const nextSec = mod.sections[sIndex + 1];
  if (nextSec) return { prev, next: { href: `#/m/${mod.id}/s/${nextSec.id}`, label: "Nächster Abschnitt" } };
  const mIndex = COURSE.modules.findIndex((item) => item.id === mod.id);
  const nextMod = COURSE.modules[mIndex + 1];
  if (nextMod) return { prev, next: { href: `#/m/${nextMod.id}`, label: "Nächstes Modul" } };
  return { prev, next: { href: "#/", label: "Zum Anfang" } };
}

function slideView(modId, secId, index) {
  const mod = findMod(modId);
  const sec = findSec(mod, secId);
  if (!sec) return moduleView(modId);
  const slide = sec.slides[index];
  if (!slide) return sectionView(modId, secId);
  localStorage.setItem("ft-atlas-hash", hrefSlide(mod, sec, index));
  const groups = groupsOf(sec.slides);
  const pills = groups.map((group) => {
    const on = index >= group.start && index <= group.end;
    const label = group.title.length > 48 ? `${group.title.slice(0, 46)}…` : group.title;
    return `<a class="${on ? "on" : ""}" href="${hrefSlide(mod, sec, group.start)}">${esc(label)}</a>`;
  }).join("");
  const reading = slide.blocks.length
    ? `<article class="reading">
        ${slide.kind === "question" ? `<p class="label">Frage auf der Folie</p>` : `<p class="code">${esc(sec.code)} · Folie ${slide.n}</p>`}
        <h2>${esc(slide.title)}</h2>
        ${renderBlocks(slide.blocks)}
      </article>`
    : "";
  const figure = slide.kind === "figure" || !slide.blocks.length;
  const nav = neighbors(mod, sec, index);
  shell(`
    <nav class="crumbs">
      <a href="#/">Überblick</a> <span>/</span>
      <a href="#/m/${mod.id}">${esc(mod.title)}</a> <span>/</span>
      <a href="#/m/${mod.id}/s/${sec.id}">${esc(sec.title)}</a> <span>/</span>
      <span>${index + 1} / ${sec.slides.length}</span>
    </nav>
    <div class="pills">${pills}</div>
    <div class="stage ${figure ? "figure" : ""}">
      ${figure ? "" : reading}
      ${frame(slide.file, slide.n, slide.title)}
      ${figure ? reading : ""}
    </div>
    <div class="dock">
      <a class="btn ghost" id="prev" href="${nav.prev.href}">${esc(nav.prev.label)}</a>
      <span class="keys">Pfeiltasten blättern · Esc zurück</span>
      <a class="btn" id="next" href="${nav.next.href}">${esc(nav.next.label)}</a>
    </div>
  `, mod.id);
}

function searchView(query) {
  const q = query.trim().toLowerCase();
  const hits = q.length < 2 ? [] : INDEX.filter((item) => item.hay.includes(q)).slice(0, 40);
  const list = !q
    ? `<p class="quiet">Mindestens zwei Buchstaben. Gesucht wird im Wortlaut der Folien.</p>`
    : hits.length
      ? `<div class="results">${hits.map((hit) => `
          <a href="${hrefSlide(hit.mod, hit.sec, hit.i)}">
            <span class="code">${esc(hit.mod.title)} · Folie ${hit.slide.n}</span><br>
            <b>${esc(hit.slide.title)}</b>
          </a>`).join("")}</div>`
      : `<p>Kein Treffer in den Folien für „${esc(query)}“.</p>`;
  shell(`
    <header class="mod-head"><h2>Suche</h2><p class="quiet">${hits.length ? `${hits.length} Treffer` : ""}</p></header>
    ${list}
  `);
}

function render() {
  const route = parseHash();
  if (route.view === "module") moduleView(route.mod);
  else if (route.view === "section") sectionView(route.mod, route.sec);
  else if (route.view === "slide") slideView(route.mod, route.sec, route.i);
  else if (route.view === "search") searchView(route.q);
  else home();
}

app.addEventListener("submit", (event) => {
  if (event.target.id !== "qform") return;
  event.preventDefault();
  const q = new FormData(event.target).get("q")?.toString().trim() || "";
  location.hash = `#/suche/${encodeURIComponent(q)}`;
});

app.addEventListener("click", (event) => {
  const button = event.target.closest("[data-zoom]");
  if (!button) return;
  lightbox.hidden = false;
  lightbox.innerHTML = `<button class="zoom-close" type="button">Schließen</button><img alt="${esc(button.dataset.alt || "")}" src="${esc(button.dataset.zoom)}">`;
});

lightbox.addEventListener("click", () => {
  lightbox.hidden = true;
  lightbox.innerHTML = "";
});

window.addEventListener("hashchange", render);
window.addEventListener("keydown", (event) => {
  if (event.target.matches("input, textarea")) return;
  if (event.key === "Escape") {
    if (!lightbox.hidden) {
      lightbox.hidden = true;
      lightbox.innerHTML = "";
      return;
    }
    history.back();
  }
  if (event.key === "ArrowRight") document.getElementById("next")?.click();
  if (event.key === "ArrowLeft") document.getElementById("prev")?.click();
});

render();
