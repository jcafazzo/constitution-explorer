// #/library: the Technical Library.
//
//  #/library                 the shelves: every volume in library/volumes.js, spines out
//  #/library/lineage         how the volumes follow one another, 1973 to 1991
//  #/library/<slug>          one volume: its book if it can be opened, otherwise the shelf with
//  #/library/<slug>/<page>   that volume pulled out and its card showing
//
// The shelf is plain HTML and CSS (buttons, not WebGL), so it works by keyboard, at phone width
// and where WebGL is switched off. The spines are this site's own typographic drawings. They do
// not reproduce the real covers. A volume opens when its page manifest loads (see loadManifest);
// the scans themselves are private and never published. The lower shelf holds fan works and one
// scholarly chapter; each card and each book repeats the credits printed in the document itself.
import {renderBook} from './book.js?v=b12';
import {VOLUMES, SHELVES, volumeBySlug, loadManifest} from './library/volumes.js?v=lv3';

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
const CRUMB = '<a href="#/library">TECHNICAL LIBRARY</a>';

// Can this volume be opened here? Its presenter must be built, and it needs a scan unless it
// is allowed to open on blank sheets.
const canOpen = (vol, manifest) => !!vol.book && vol.presenter === 'book' && (!!manifest || vol.book.opensWithoutScan);

export function renderLibrary(main, path) {
 let alive = true, inner = null;
 const slug = path.split('/')[2] || '';
 const done = () => { alive = false; inner?.(); main.classList.remove('book-route', 'lib-route'); };
 if (slug === 'lineage') { inner = lineage(main); return done; }
 const vol = slug ? volumeBySlug(slug) : null;
 if (vol?.book && vol.presenter === 'book') {
  main.classList.add('book-route', 'lib-route');
  main.innerHTML = `<div class="folio"><span>${CRUMB} / ${esc(vol.short.toUpperCase())}</span><span>${vol.year}</span></div><p class="lib-wait" role="status">Taking the volume down…</p>`;
  loadManifest(vol).then(m => {
   if (!alive) return;
   if (canOpen(vol, m)) { main.classList.remove('lib-route'); inner = renderBook(main, path, {volume: vol, base: '#/library/' + vol.slug, crumb: CRUMB, manifest: m}); }
   else inner = shelf(main, vol);
  });
  return done;
 }
 inner = shelf(main, vol);
 return done;
}

// ---------- the shelf ----------
function shelf(main, selected) {
 let alive = true, timer = 0, current = null;
 const manifests = new Map();                       // slug -> manifest | null, once known
 main.classList.add('book-route', 'lib-route');
 const years = VOLUMES.map(v => v.year), first = Math.min(...years), last = Math.max(...years);
 const no = v => String(VOLUMES.indexOf(v) + 1).padStart(2, '0');
 const fan = v => v.shelf === 'fan';
 main.innerHTML = `<div class="folio"><span><a href="#/">COMMAND SECTION</a> / TECHNICAL LIBRARY</span><span>${VOLUMES.length} VOLUMES · ${first}–${last}</span></div>
<section class="lib" aria-labelledby="lib-title">
 <h1 id="lib-title" class="sr-only">Technical library</h1>
 <div class="lib-case">
  <p class="lib-hint" id="lib-hint">Choose a volume to take it down. Arrow keys move along the shelves.</p>
  ${SHELVES.map(sh => `<h2 class="lib-shelf-name" id="lib-sh-${sh.id}"><span>${esc(sh.name)}</span><i>${sh.note}</i></h2>
  <ol class="lib-shelf" aria-labelledby="lib-sh-${sh.id}" aria-describedby="lib-hint">
   ${VOLUMES.filter(v => v.shelf === sh.id).map(v => `<li style="--w:${v.spine.w};--h:${v.spine.h};--bg:${v.spine.bg};--fg:${v.spine.fg};--ac:${v.spine.accent}">
    <button class="lib-spine lib-${v.spine.kind}" data-slug="${v.slug}" aria-expanded="false" aria-controls="lib-card">
     <span class="lib-sp-no" aria-hidden="true">${no(v)}</span>
     <span class="lib-sp-title">${v.spine.lines.map(l => `<span>${esc(l)}</span>`).join('')}</span>
     <span class="lib-sp-foot" aria-hidden="true">${esc(v.spine.foot)}</span>
     <span class="sr-only">. ${esc(v.title)}, ${v.year}. <span data-status>Checking for ${fan(v) ? 'the file' : 'a scan'}.</span></span>
    </button>
    <span class="lib-tag" aria-hidden="true"><b>${v.year}</b><i data-tag>…</i></span>
   </li>`).join('')}
  </ol>
  <div class="lib-plank" aria-hidden="true"></div>`).join('\n')}
 </div>
 <div class="lib-card" id="lib-card" tabindex="-1"></div>
</section>
<section class="lib-notes" aria-label="About the library">
 <div><strong>01 / THE SHELF</strong><p>Fourteen volumes on two shelves. The upper shelf holds five publications, from Franz Joseph’s blueprints and manual of 1975 to the <em>Next Generation</em> manual of 1991. The lower shelf holds nine later documents: fan-made references and plans, and one scholarly chapter. The spines are drawn for this site. They are not copies of the real covers.</p></div>
 <div><strong>02 / THE PAGES AND THE CREDITS</strong><p>Every volume is the work of the people named on its card. The credits there are copied from the document’s own pages, and each book repeats them in full under its pages. A volume opens only from its owner’s copy on their own computer. The pages are never published with this site, so here most volumes stay on the shelf with a card.</p></div>
 <div><strong>03 / THE LINEAGE</strong><p>How one volume led to the next, with a source for each statement. <a class="lib-link" href="#/library/lineage">Read the lineage ›</a></p></div>
</section>`;
 const $ = s => main.querySelector(s);
 const card = $('#lib-card');
 const buttons = [...main.querySelectorAll('.lib-spine')];
 const btnFor = slug => buttons.find(b => b.dataset.slug === slug);

 const intro = () => {
  card.innerHTML = `<span class="eyebrow">Technical library</span><h2>${VOLUMES.length} volumes, ${first}–${last}</h2>
<p>Each spine is a button. A volume whose pages are on this computer opens as a book. The others come off the shelf with a card that says what the volume is and who made it.</p>
${SHELVES.map(sh => `<h3 class="lib-list-name">${esc(sh.name)}</h3><ul class="lib-list">${VOLUMES.filter(v => v.shelf === sh.id).map(v => `<li><a href="#/library/${v.slug}">${esc(v.title)}</a> <span>${v.year}</span></li>`).join('')}</ul>`).join('')}
<p><a class="lib-link" href="#/library/lineage">The lineage, 1973–1991 ›</a></p>`;
 };
 const scanLine = (v) => {
  if (!manifests.has(v.slug)) return fan(v) ? 'Checking for the file…' : 'Checking for a scan…';
  const m = manifests.get(v.slug);
  if (fan(v)) return m ? `The owner’s copy is on this computer. It opens as a book of ${m.count} pages.` : 'The pages are not here.';
  if (canOpen(v, m)) return m ? `A scan of ${m.count} pages is on this computer.` : 'No scan has been added yet. The book opens on blank, numbered sheets.';
  if (m) return `A scan is on this computer, but the ${v.presenterName} that will show it has not been built yet.`;
  return 'No scan has been added yet.';
 };
 const showCard = (v) => {
  const open = manifests.has(v.slug) && canOpen(v, manifests.get(v.slug));
  const built = v.presenter === 'book';
  const row = (k, t) => `<div><dt>${esc(k)}</dt><dd>${t}</dd></div>`;
  const why = fan(v)
   ? ' This document is the work of the people credited above. It opens only from the owner’s copy of the file, and its pages are not published with this site.'
   : ' Pages are copyrighted and are never published with this site. The volume opens once its owner scans their own copy on their own computer.';
  card.innerHTML = `<span class="eyebrow">Volume ${no(v)} · ${v.year}</span><h2>${esc(v.title)}</h2>
${v.blurb ? `<p>${esc(v.blurb)}</p>` : ''}
<dl>
 ${row(fan(v) ? 'Issued' : 'Published', `${esc(v.publisher)}, ${esc(v.date)}`)}
 ${row(fan(v) ? 'By' : 'Credits', esc(v.credits))}
 ${row('Form', esc(v.form))}
 ${fan(v) ? '' : row('Shown as', built ? 'A book, with pages that turn.' : `A ${esc(v.presenterName)}. It has not been built yet.`)}
 ${v.explorer ? row('Explorer layer', esc(v.explorer)) : ''}
</dl>
${v.attribution ? `<h3 class="lib-list-name">Credits, as the document gives them</h3><dl class="lib-credits">${v.attribution.map(([k, t]) => row(k, esc(t))).join('')}${row('Notice', `“${esc(v.notice)}”`)}</dl>` : ''}
<p class="lib-status" data-card-status><strong>${esc(scanLine(v))}</strong>${open ? '' : why}</p>
<p class="lib-actions">${open ? `<a class="lib-btn" href="#/library/${v.slug}">Open the book</a>` : ''}${v.link ? `<a class="lib-btn" href="${v.link[1]}" target="_blank" rel="noopener">${esc(v.link[0])}</a>` : ''}<button class="lib-btn" data-back>Put it back</button></p>`;
  card.scrollTop = 0;
 };
 const select = (v, {focusCard = false, replace = true} = {}) => {
  current = v;
  buttons.forEach(b => { const on = !!v && b.dataset.slug === v.slug; b.classList.toggle('out', on); b.setAttribute('aria-expanded', String(on)); });
  if (v) showCard(v); else intro();
  if (replace) { const h = v ? '#/library/' + v.slug : '#/library'; try { if (location.hash !== h) history.replaceState(null, '', h); } catch {} }
  if (focusCard && v) card.focus({preventScroll: !matchMedia('(max-width: 900px)').matches});
 };
 const choose = (v) => {
  clearTimeout(timer);
  const known = manifests.has(v.slug);
  if (known && canOpen(v, manifests.get(v.slug))) {
   // Pull it out, then open it.
   buttons.forEach(b => { b.classList.toggle('out', b.dataset.slug === v.slug); });
   const go = () => { if (alive) location.hash = '#/library/' + v.slug; };
   if (reduceMQ.matches) go(); else timer = setTimeout(go, 380);
   return;
  }
  if (current === v) { select(null); btnFor(v.slug)?.focus(); return; }
  select(v, {focusCard: true});
 };
 main.querySelector('.lib-case').addEventListener('click', (e) => { const b = e.target.closest('.lib-spine'); if (b) choose(volumeBySlug(b.dataset.slug)); });
 main.querySelector('.lib-case').addEventListener('keydown', (e) => {
  const i = buttons.indexOf(e.target.closest?.('.lib-spine')); if (i < 0) return;
  const to = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? buttons.length - 1 : -1;
  if (to < 0 || to >= buttons.length) return;
  e.preventDefault(); buttons[to].focus();
 });
 card.addEventListener('click', (e) => { if (e.target.closest('[data-back]')) { const v = current; select(null); if (v) btnFor(v.slug)?.focus(); } });
 card.addEventListener('keydown', (e) => { if (e.key === 'Escape' && current) { const v = current; select(null); btnFor(v.slug)?.focus(); } });

 select(selected || null, {replace: !selected});
 // An unknown slug, or a page number on a volume that cannot open, falls back to the plain address.
 { const h = selected ? '#/library/' + selected.slug : '#/library'; try { if (location.hash !== h) history.replaceState(null, '', h); } catch {} }

 VOLUMES.forEach(v => loadManifest(v).then(m => {
  if (!alive) return;
  manifests.set(v.slug, m);
  const b = btnFor(v.slug), open = canOpen(v, m);
  b.querySelector('[data-status]').textContent = open ? (m ? 'Opens as a book.' : 'Opens on blank sheets; no scan added yet.') : m ? 'Scanned, but its presenter is not built yet.' : fan(v) ? 'The pages are not here.' : 'No scan added yet.';
  b.parentElement.querySelector('[data-tag]').textContent = fan(v) ? (m ? 'File' : 'No file') : m ? 'Scan' : 'No scan';
  b.parentElement.classList.toggle('has-scan', !!m);
  if (current === v) showCard(v);
 }));

 return () => { alive = false; clearTimeout(timer); };
}

// ---------- the lineage ----------
// Every statement below is taken from model-source/book/origins.md (which grades each claim and
// names its source) or from the catalogue table in model-source/library/PLAN.md. Nothing is added
// from memory. Where origins.md marks a claim as resting on one source, the entry says so.
const SRC = {
 timeline: ['Franz Joseph timeline', 'http://www.trekplace.com/fj-timeline.html'],
 karen: ['Karen Dick interview', 'http://www.trekplace.com/fj-kdint01.html'],
 fj76: ['1976 interview', 'http://www.trekplace.com/fj-fjwilliamsint01.html'],
 newitt: ['Newitt interview', 'http://www.trekplace.com/fj-fjnewittint01.html'],
 rehak: ['Rehak', 'https://graphic-engine.swarthmore.edu/franz-joseph-and-star-treks-blueprint-culture/'],
 ma: ['Memory Alpha', 'https://memory-alpha.fandom.com/wiki/Star_Trek_Blueprints'],
 list: ['Wikipedia list', 'https://en.wikipedia.org/wiki/List_of_Star_Trek_technical_manuals'],
 wfj: ['Wikipedia, Franz Joseph', 'https://en.wikipedia.org/wiki/Franz_Schnaubelt'],
};
const cite = (...k) => `<span class="lib-cite">${k.map(x => typeof x === 'string' && SRC[x] ? `<a href="${SRC[x][1]}" target="_blank" rel="noopener">${SRC[x][0]}</a>` : esc(x)).join(' · ')}</span>`;
const vlink = (slug, text) => `<a class="lib-vol" href="#/library/${slug}">${text} ›</a>`;
const LINEAGE = [
 ['14 Apr 1973', `Franz Joseph goes to a meeting of S.T.A.R. San Diego, a <em>Star Trek</em> fan club, with his daughter Karen. The next day he draws the hand phaser and the communicator.`, cite('timeline', 'newitt')],
 ['Sep–Dec 1973', `He draws the <em>Booklet of General Ship’s Plans</em>, the Blueprints, as a side project in the middle of the manual. He needs a full ship layout before he can draw the interiors.`, cite('fj76', 'timeline')],
 ['Apr 1974', `The first edition: 500 hand-cut, hand-stapled diazo booklets, assembled by club members in his house and sold at Equicon ’74 under a one-off Paramount licence. 410 are sold and 450 more are requested.`, cite('timeline', 'karen', 'rehak')],
 ['30 May 1974', `Paramount’s Lou Mindling sends the work to Judy-Lynn del Rey at Ballantine Books.`, cite('timeline', 'from his work log; one source')],
 ['3 Dec 1974', `The Blueprints contract is signed.`, cite('timeline', 'one source')],
 ['12 May 1975', `Paramount agrees not to contest copyright in Franz Joseph’s name.`, cite('timeline', 'one source')],
 ['Spring 1975', `Ballantine publishes <em>Star Trek Blueprints</em>: twelve large sheets in a plastic pouch. The sources differ on the month. The timeline has them in stores on 24 May, Memory Alpha says April and Rehak says May. The timeline counts 210,000 sets produced by 18 July. ${vlink('blueprints', 'Volume 01')}`, cite('timeline', 'ma', 'rehak')],
 ['Nov 1975', `Ballantine publishes the <em>Star Fleet Technical Manual</em>, about six months after the Blueprints. ${vlink('manual', 'Volume 02')}`, cite('timeline', 'ma')],
 ['1977', `Fans and licensees follow. The fan-made <em>Star Fleet Medical Reference Manual</em> appears, and Lou Zocchi’s <em>Star Fleet Battle Manual</em> is licensed from Franz Joseph.`, cite('newitt', 'rehak', 'wfj')],
 ['1979', `<em>Star Fleet Battles</em> (Task Force Games) is licensed from Franz Joseph Designs.`, cite('wfj')],
 ['Aug 1980', `Bantam publishes <em>Star Trek Maps</em>: a box of four four-colour wall maps and a booklet. Catalogue records credit Jeffrey Maynard with design and coordination and Geoffrey Mandel with the astronomical art. ${vlink('maps', 'Volume 03')}`, cite('catalogue records, as listed in this project’s library plan')],
 ['1987', `Pocket Books publishes <em>Mr. Scott’s Guide to the Enterprise</em> by Shane Johnson, one of the official successors. ${vlink('mr-scotts-guide', 'Volume 04')}`, cite('list', 'rehak')],
 ['1991', `Pocket Books publishes the <em>Star Trek: The Next Generation Technical Manual</em> by Rick Sternbach and Michael Okuda. ${vlink('tng-technical-manual', 'Volume 05')}`, cite('list', 'rehak')],
];

function lineage(main) {
 main.classList.add('book-route', 'lib-route');
 main.innerHTML = `<div class="folio"><span>${CRUMB} / LINEAGE</span><span>1973–1991</span></div>
<section class="bk-history lib-lineage" aria-labelledby="lib-lin-title">
 <header><span class="eyebrow">Technical library · Lineage</span><h1 id="lib-lin-title">From the Equicon blueprints to the 1991 manual</h1>
 <p class="bk-lede">The five published volumes on the upper shelf form one line of descent. It starts with a set of ship’s plans that Franz Joseph drew in late 1973 and sold at a convention, and runs to the studio’s own technical manual eighteen years later. Each entry names where the statement comes from.</p>
 <p class="lib-back"><a class="lib-link" href="#/library">‹ Back to the shelf</a></p></header>
 <ol class="bk-timeline">
  ${LINEAGE.map(([t, p, c]) => `<li><time>${t}</time><p>${p} ${c}</p></li>`).join('\n  ')}
 </ol>
 <div class="bk-asides">
  <div><h3>A new kind of book</h3><p>The Blueprints and the manual started the genre of technical manuals and blueprints for fictional spacecraft. That the later official books follow in this line is well attested. How much they owe to Franz Joseph’s work is the commentators’ interpretation. ${cite('wfj', 'list', 'rehak')}</p></div>
  <div><h3>Whose designs</h3><p>The copyright stayed in Franz Joseph’s name. His daughter Karen lists that among the reasons for the rift with Gene Roddenberry: neither Roddenberry nor Paramount owned the designs. That is her account alone. The manual has never been treated as canon. ${cite('karen', 'timeline', 'ma')}</p></div>
  <div><h3>Opinion, marked as such</h3><p>Some fans call <em>Star Trek Maps</em> the manual’s truest sequel. That is an opinion. It is not a finding of the sources used here.</p></div>
  <div><h3>Not on the shelf</h3><p>A <em>Deep Space Nine</em> technical manual followed in 1998. ${cite('list')} The research file also records Klingon and Romulan blueprints and Geoffrey Mandel’s <em>Starfleet Handbook</em> among the fan-made successors. ${cite('newitt', 'rehak')} A 2007 revival issue of the Handbook stands on the lower shelf, with the later fan works. ${vlink('star-fleet-handbook-14', 'Volume 09')}</p></div>
 </div>
 <p class="bk-sources">Sources: Karen Dick and Greg Tyler, <a href="${SRC.timeline[1]}" target="_blank" rel="noopener">Franz Joseph timeline</a> (1999, from his work log); <a href="${SRC.karen[1]}" target="_blank" rel="noopener">interview with Karen Dick</a> (1999); Paul Newitt, <a href="${SRC.newitt[1]}" target="_blank" rel="noopener">interview with Franz Joseph</a> (<em>Enterprise Incidents</em>, 1983–84); Williams and Durrans, <a href="${SRC.fj76[1]}" target="_blank" rel="noopener">1976 interview</a>; Bob Rehak, <a href="${SRC.rehak[1]}" target="_blank" rel="noopener">Franz Joseph and Star Trek’s blueprint culture</a> (2012); <a href="${SRC.ma[1]}" target="_blank" rel="noopener">Memory Alpha, Star Trek Blueprints</a>; Wikipedia, <a href="${SRC.list[1]}" target="_blank" rel="noopener">List of Star Trek technical manuals</a> and <a href="${SRC.wfj[1]}" target="_blank" rel="noopener">Franz Joseph</a>. The research behind this page is in the repository at <code>model-source/book/origins.md</code>, which grades every claim. Dates from the timeline alone rest on Franz Joseph’s own work log and have not been checked against other records.</p>
</section>`;
 return () => {};
}
