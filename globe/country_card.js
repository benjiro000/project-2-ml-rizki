/* country_card.js
 * The hover card for the coffee globe, drawn in the terminal look you saved:
 * a thin rail down the left, ◆ for the open section, ◇ for the others (dim one-line summary).
 *
 * It only needs three things from the globe page:
 *   const card = CountryCard.create({ factsUrl: "data/country_facts.json" });
 *   globe.onPolygonHover(d => card.hover(d))      // d is a country feature or null
 *        .onPolygonClick(d => card.click(d));     // click pins the card, click the sea unpins
 *   card.setEnabled(true or false)                // wire this to the existing toggle
 * and, if you want to colour the countries:  card.tone(feature)  ->  "measured" | "other" | "none"
 *
 * Every number on the card comes from data/country_facts.json (built by src/build_country_facts.py)
 * and shows where it came from. Anything missing says "no data" instead of guessing.
 */
(function (global) {
  "use strict";

  const CSS = `
  .cc-panel{position:fixed;top:16px;right:16px;width:min(440px,calc(100vw - 32px));max-height:calc(100vh - 32px);
    overflow:auto;box-sizing:border-box;padding:14px 16px 12px;background:rgba(13,17,23,.93);color:#e6edf3;
    border:1px solid #2b3440;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.45);z-index:20;
    font:12.5px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;transition:opacity .15s;}
  .cc-panel[hidden]{display:none}
  .cc-panel.cc-idle{opacity:.6}
  .cc-panel a{color:#d9a05b;text-decoration:none}
  .cc-panel a:hover{text-decoration:underline}
  .cc-dim{color:#7d8590}
  .cc-bad{color:#e5786d}
  .cc-head{font-weight:600;color:#fff;margin-bottom:2px}
  .cc-head .cc-dim{font-weight:400}
  .cc-rail{border-left:1px solid #3a4350;margin-left:.5ch;padding-top:2px}
  .cc-sec{position:relative;padding:2px 0 2px 2.2ch;cursor:pointer}
  .cc-mark{position:absolute;left:-.5ch;top:2px;background:#0d1117;color:#7d8590;line-height:1.4}
  .cc-sec.cc-open .cc-mark{color:#d9a05b}
  .cc-title{color:#e6edf3}
  .cc-sec:not(.cc-open) .cc-title{color:#aab2bd}
  .cc-lines{margin-top:2px;cursor:default}
  .cc-line{white-space:pre-wrap;word-break:break-word}
  .cc-note{color:#7d8590;white-space:pre-wrap;margin-top:3px}
  .cc-foot{margin-top:8px;padding-top:6px;border-top:1px solid #222b36;color:#7d8590;font-size:11.5px}
  @media (max-width:640px){.cc-panel{top:auto;bottom:0;right:0;left:0;width:auto;max-height:55vh;border-radius:10px 10px 0 0}}
  `;

  const NAMES = { cqi: "CQI", fao: "FAOSTAT", psd: "USDA PSD" };
  // [label shown, CQI class it counts, key used in literature_cards.json]
  const PROCESS_CHECKLIST = [
    ["washed", "washed", "washed"],
    ["natural", "natural", "natural"],
    ["honey (pulped natural)", "honey", "honey"],
    ["wet-hulled", null, "wet-hulled"],
    ["anaerobic / other fermentation", null, "anaerobic"],
    ["carbonic maceration", null, "carbonic-maceration"],
    ["civet (luwak)", null, "luwak"],
    ["drying method", null, "drying"],
  ];
  // CQI's coarse processing names, each lot counted in exactly one class
  function cqiClass(name) {
    const n = String(name).toLowerCase();
    if (/pulped|honey/.test(n)) return "honey";
    if (/semi/.test(n)) return "semi";
    if (/natural|dry/.test(n)) return "natural";
    if (/washed|wet/.test(n)) return "washed";
    return "other";
  }
  const cupLabel = (k) => (k === "Cupper.Points" ? "Overall" : k);
  const CUP_PARTS = ["Aroma", "Flavor", "Aftertaste", "Acidity", "Body", "Balance", "Cupper.Points"];

  const nf = new Intl.NumberFormat("en");
  const fmt = (v) => nf.format(Math.round(v));
  const big = (v) => (v >= 1e6 ? Number((v / 1e6).toFixed(2)).toString() + " M" : fmt(v));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const bar = (frac, w = 14) => { const k = Math.max(0, Math.min(w, Math.round(frac * w))); return "█".repeat(k) + "░".repeat(w - k); };
  const sign = (v) => (v > 0 ? "+" : v < 0 ? "−" : "±") + Math.abs(v).toFixed(2);
  const dim = (s) => `<span class="cc-dim">${s}</span>`;

  function create(opts) {
    const o = Object.assign({ factsUrl: "data/country_facts.json", isoOf: (f) => f.properties.ADM0_A3, nameOf: (f) => f.properties.NAME }, opts || {});
    const st = { facts: null, error: null, enabled: true, hovered: null, pinned: null, open: 0, listeners: [] };

    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
    const panel = document.createElement("div");
    panel.className = "cc-panel";
    panel.hidden = true;
    document.body.appendChild(panel);

    const ready = fetch(o.factsUrl)
      .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then((j) => { st.facts = j; render(); })
      .catch((e) => { st.error = e.message || String(e); render(); });

    const country = (feat) => (feat && st.facts ? st.facts.countries[o.isoOf(feat)] || null : null);
    const minLots = () => (st.facts && st.facts.min_lots) || 10;

    // ---------- source tags ----------
    function src(id, year) {
      const s = st.facts && st.facts.sources && st.facts.sources[id];
      const label = NAMES[id] || (s && (s.short || s.label)) || id;
      const text = esc(label) + (year ? " " + esc(year) : "");
      return s && s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener" title="${esc(s.label || label)}">${text}</a>` : text;
    }
    const noData = (why) => [`<span class="cc-dim">no data yet</span>`].concat(why ? [`<div class="cc-note">${why}</div>`] : []);

    // ---------- the six sections: each returns { summary, lines } ----------
    const SECTIONS = [
      { title: "Land under coffee", build(c) {
        if (!c || !c.land) return { summary: null, lines: noData("Fills from FAOSTAT (data/external/faostat_coffee.csv) or USDA PSD.") };
        const l = c.land;
        return {
          summary: `${big(l.ha)} ha · ${NAMES[l.src]} ${l.year}`,
          lines: [`area harvested   ${fmt(l.ha)} ha   ${src(l.src, l.year)}`,
                  `<div class="cc-note">Area harvested is the land picked in that year, not all land planted with coffee.</div>`],
        };
      } },
      { title: "Production per year", build(c) {
        const bt = c && c.by_type, tot = c && c.total;
        if (!tot && !(bt && bt.total_t)) return { summary: null, lines: noData("Fills from FAOSTAT (total) and USDA PSD (arabica / robusta / other).") };
        const lines = [];
        const main = tot ? { t: tot.t, tag: src(tot.src, tot.year) } : { t: bt.total_t, tag: src("psd", bt.market_year + "/" + String(bt.market_year + 1).slice(-2)) };
        lines.push(`total   ${fmt(main.t)} t   ${main.tag}`);
        if (bt && (bt.arabica_t || bt.robusta_t || bt.other_t)) {
          const base = bt.total_t || (bt.arabica_t || 0) + (bt.robusta_t || 0) + (bt.other_t || 0);
          lines.push(dim(`by type, USDA PSD market year ${bt.market_year}/${String(bt.market_year + 1).slice(-2)}:`));
          [["arabica", bt.arabica_t], ["robusta", bt.robusta_t], ["other", bt.other_t]].forEach(([k, v]) => {
            if (v) lines.push(`  ${k.padEnd(8)} ${fmt(v).padStart(11)} t  ${bar(v / base, 10)} ${Math.round((100 * v) / base)} %`);
          });
        } else {
          lines.push(dim("by type: no data yet (USDA PSD has no arabica / robusta split for this country)"));
        }
        if (tot && bt && bt.total_t && Math.abs(tot.t - bt.total_t) / tot.t > 0.1) {
          lines.push(`<div class="cc-note">FAOSTAT (${fmt(tot.t)} t) and PSD (${fmt(bt.total_t)} t) differ by more than 10 %: different years and definitions. Both are shown as published.</div>`);
        }
        return { summary: `${fmt(main.t)} t per year`, lines };
      } },
      { title: "Varieties and cultivars", build(c) {
        const v = c && c.cqi && c.cqi.varieties;
        const litV = c && c.literature && c.literature.varieties;
        const lines = [];
        let summary = null;
        if (v && !v.not_enough) {
          const total = v.n;
          summary = v.top.slice(0, 3).map((t) => t[0]).join(", ") + (v.top.length > 3 ? ", …" : "");
          lines.push(dim(`seen in ${v.n} CQI lots (${v.missing} lots list none)`));
          v.top.forEach(([k, n]) => lines.push(`${esc(k).padEnd(12)} ${String(n).padStart(4)}  ${bar(n / total, 12)}`));
          if (v.rest) lines.push(dim(`+ ${v.rest} lots of rarer varieties`));
          lines.push(`<div class="cc-note">This is what the reviewed lots were, not a census of everything grown there.</div>`);
        } else if (v) {
          summary = `not enough data (${v.n} lots)`;
          lines.push(dim(`not enough data: ${v.n} lots list a variety, the card needs ${minLots()}`));
        }
        if (litV && litV.length) {
          lines.push(dim("from papers:"));
          litV.forEach((x) => lines.push(`${esc(x.name)}  ${x.note ? esc(x.note) + "  " : ""}${src(x.src)}`));
          summary = summary || litV.slice(0, 3).map((x) => x.name).join(", ");
        }
        if (!lines.length) return { summary: null, lines: noData("This country has no CQI lots in our table.") };
        return { summary, lines };
      } },
      { title: "Altitude range", build(c) {
        const a = c && c.cqi && c.cqi.altitude;
        if (!a) return { summary: null, lines: noData("This country has no CQI lots in our table.") };
        if (a.not_enough) return { summary: `not enough data (${a.n} lots)`, lines: [dim(`only ${a.n} lots report an altitude, the card needs ${minLots()}`)] };
        return {
          summary: `${fmt(a.p10)}–${fmt(a.p90)} m · median ${fmt(a.median)} m`,
          lines: [`typical (10–90 %)   ${fmt(a.p10)}–${fmt(a.p90)} m`, `median              ${fmt(a.median)} m`,
                  `lowest / highest    ${fmt(a.min)} / ${fmt(a.max)} m`, dim(`from ${a.n} CQI lots that report an altitude`),
                  `<div class="cc-note">Each lot's altitude is the middle of its reported range, so this is the range of reviewed lots, not of the whole country.</div>`],
        };
      } },
      { title: "Composition and processing", build(c) {
        const lit = (c && c.literature) || {};
        const comp = lit.composition || [];
        const fine = lit.processing_fine || [];
        const proc = c && c.cqi && c.cqi.processing;
        const lines = [];
        if (comp.length) {
          lines.push(dim("measured in papers (one line per study sample set):"));
          lines.push(dim("units differ between studies (fresh vs dry weight): compare lines only within one study"));
          comp.forEach((m) => {
            const meta = [m.n_samples != null ? "n " + m.n_samples : null, m.altitude_m ? m.altitude_m + " m" : null,
                          m.harvest_year ? "harvest " + m.harvest_year : null, m.processing || "processing not stated", m.species].filter(Boolean).join(" · ");
            const hasRange = m.min != null && m.max != null;
            const value = hasRange ? (m.min === m.max ? m.min : m.min + "–" + m.max) : (m.mean != null ? "mean " + m.mean : "no value");
            lines.push(`<span title="${esc(m.where || "")}">${esc(m.compound).padEnd(18)} ${esc(value)} ${esc(m.unit || "")}</span>`);
            lines.push(`  ${dim(esc(meta))}  ${src(m.src)}`);
          });
        } else {
          lines.push(dim("composition (caffeine, chlorogenic acids, trigonelline, protein, lipids, sugars): no data yet"));
        }
        lines.push("&nbsp;");
        lines.push(dim("processing, ☑ found · ☐ no source yet:"));
        const counts = {};
        (proc && !proc.not_enough ? proc.top : []).forEach(([name, n]) => { const k = cqiClass(name); counts[k] = (counts[k] || 0) + n; });
        PROCESS_CHECKLIST.forEach(([label, cls, key]) => {
          const parts = [];
          if (cls && counts[cls]) parts.push(`${counts[cls]} CQI lots`);
          fine.filter((f) => f.type === key).forEach((f) => parts.push((f.note ? esc(f.note) + " " : "") + src(f.src)));
          lines.push(parts.length ? `☑ ${esc(label)}   ${parts.join(" · ")}` : dim("☐ " + esc(label)));
        });
        const extra = [["semi", "semi-washed / semi-pulped"], ["other", "other / unclassified"]].filter(([k]) => counts[k]).map(([k, l]) => `${l} ${counts[k]}`);
        if (extra.length) lines.push(dim("also in CQI: " + extra.join(" · ") + " lots"));
        if (proc && proc.not_enough) lines.push(dim(`CQI mix hidden: only ${proc.n} lots list a method, the card needs ${minLots()}`));
        const found = comp.length;
        return { summary: found ? `${found} measurement${found === 1 ? "" : "s"} from papers` : "no composition data yet", lines };
      } },
      { title: "Cup profile (CQI)", build(c) {
        const cup = c && c.cqi && c.cqi.cup;
        if (!cup) return { summary: null, lines: noData("This country has no Arabica lots in our table.") };
        if (cup.not_enough) return { summary: `not enough data (${cup.n} Arabica lots)`, lines: [dim(`only ${cup.n} Arabica lots, the card needs ${minLots()}`)] };
        const d = cup.delta;
        const ranked = CUP_PARTS.slice().sort((a, b) => Math.abs(d[b]) - Math.abs(d[a]));
        const lines = [dim(`difference from the average Arabica lot, ${cup.n} lots:`)];
        CUP_PARTS.forEach((k) => {
          const v = d[k], w = 6, kk = Math.round(Math.min(Math.abs(v), 0.5) / 0.5 * w);
          const left = v < 0 ? "░".repeat(w - kk) + "█".repeat(kk) : "░".repeat(w);
          const right = v > 0 ? "█".repeat(kk) + "░".repeat(w - kk) : "░".repeat(w);
          lines.push(`${cupLabel(k).padEnd(11)} ${sign(v).padStart(6)}  ${left}┊${right}`);
        });
        lines.push(`<div class="cc-note">Cup scores are sensory scores from Q-graders, not chemistry. Scale of each bar: ±0.5 points.</div>`);
        return { summary: "vs average: " + ranked.slice(0, 2).map((k) => `${cupLabel(k)} ${sign(d[k])}`).join(" · "), lines };
      } },
    ];

    // ---------- drawing ----------
    function render() {
      panel.hidden = !st.enabled;
      if (!st.enabled) return;
      const feat = st.pinned || st.hovered;
      panel.classList.toggle("cc-idle", !st.pinned && !st.hovered);
      if (st.error) {
        panel.innerHTML = `<div class="cc-head">┌ Coffee facts</div><div class="cc-rail"><div class="cc-sec cc-open"><span class="cc-mark">◆</span>
          <span class="cc-title cc-bad">Could not load ${esc(o.factsUrl)}</span><div class="cc-lines"><div class="cc-line">${esc(st.error)}</div>
          <div class="cc-note">Open this page through a local server (python -m http.server 8000 inside the globe folder) and run src/build_country_facts.py first.</div></div></div></div>`;
        return;
      }
      if (!st.facts) { panel.innerHTML = `<div class="cc-head">┌ Coffee facts</div>${dim("loading…")}`; return; }
      if (!feat) {
        panel.innerHTML = `<div class="cc-head">┌ Coffee facts</div><div class="cc-rail"><div class="cc-sec"><span class="cc-mark">◇</span>${dim("hover a country")}</div></div>
          <div class="cc-foot">click a country to pin it · F show / hide</div>`;
        return;
      }
      const c = country(feat), name = (c && c.name) || o.nameOf(feat), iso = o.isoOf(feat);
      const n = c && c.cqi;
      const headInfo = n ? `${n.n_lots} CQI lots (${n.n_arabica} arabica${n.n_robusta ? ", " + n.n_robusta + " robusta" : ""})` : "no CQI lots";
      let html = `<div class="cc-head">┌ ${esc(name)} <span class="cc-dim">· ${esc(iso)} · ${headInfo}${st.pinned ? " · pinned" : ""}</span></div><div class="cc-rail">`;
      if (!c) {
        html += `<div class="cc-sec"><span class="cc-mark">◇</span>${dim("no coffee data for this country in our sources")}</div></div>`;
      } else {
        SECTIONS.forEach((s, i) => {
          const r = s.build(c), open = i === st.open;
          html += `<div class="cc-sec${open ? " cc-open" : ""}" data-i="${i}"><span class="cc-mark">${open ? "◆" : "◇"}</span>`;
          html += `<span class="cc-title">${i + 1}  ${esc(s.title)}</span>`;
          if (open) html += `<div class="cc-lines">${r.lines.map((l) => (l.startsWith("<div") ? l : `<div class="cc-line">${l}</div>`)).join("")}</div>`;
          else html += `  <span class="cc-dim">${r.summary == null ? "no data" : esc(r.summary)}</span>`;
          html += `</div>`;
        });
        html += `</div>`;
      }
      const litIds = c && c.literature ? Array.from(new Set((JSON.stringify(c.literature).match(/"src":"[^"]+"/g) || []).map((m) => m.slice(7, -1)))) : [];
      const used = ["cqi", "fao", "psd"].concat(litIds).filter((k) => st.facts.sources && st.facts.sources[k]).map((k) => src(k));
      html += `<div class="cc-foot">↑/↓ or 1–6 open a section · click a country to pin · Esc unpin · F show / hide<br>sources: ${used.join(" · ")}</div>`;
      panel.innerHTML = html;
    }

    panel.addEventListener("click", (e) => {
      const sec = e.target.closest && e.target.closest(".cc-sec[data-i]");
      if (sec && !e.target.closest("a")) { st.open = Number(sec.dataset.i); render(); }
    });
    document.addEventListener("keydown", (e) => {
      if (/input|textarea|select/i.test((e.target && e.target.tagName) || "")) return;
      if (e.key === "ArrowDown" || e.key === "ArrowUp") { st.open = (st.open + (e.key === "ArrowDown" ? 1 : SECTIONS.length - 1)) % SECTIONS.length; e.preventDefault(); render(); }
      else if (/^[1-6]$/.test(e.key)) { st.open = Number(e.key) - 1; render(); }
      else if (e.key === "Escape") { st.pinned = null; render(); st.listeners.forEach((f) => f()); }
      else if (e.key.toLowerCase() === "f" && !e.metaKey && !e.ctrlKey) { api.setEnabled(!st.enabled); }
    });

    const api = {
      ready,
      get pinned() { return st.pinned; },
      get enabled() { return st.enabled; },
      hover(feat) { st.hovered = feat || null; if (!st.pinned) render(); },
      click(feat) {
        st.pinned = feat && feat !== st.pinned ? feat : null;
        render();
        st.listeners.forEach((f) => f());
      },
      setEnabled(on) { st.enabled = !!on; render(); st.listeners.forEach((f) => f()); },
      onChange(fn) { st.listeners.push(fn); },
      tone(feat) {
        const c = country(feat);
        if (!c) return "none";
        if (c.cqi && c.cqi.n_lots >= minLots()) return "measured";
        return c.land || c.total || c.by_type || c.literature || c.cqi ? "other" : "none";
      },
    };
    render();
    return api;
  }

  global.CountryCard = { create };
})(window);