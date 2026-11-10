// The Technical Library: one entry per volume on the shelf.
//
// Everything that is particular to one book lives here, so the book engine (../book.js) and the
// shelf (../library.js) stay general. A volume is "available" when its page manifest loads; the
// manifests and page images are generated locally from the owner's scans by
// model-source/book/render-pages.py and are never published.
//
// Fields
//  slug       route segment: #/library/<slug>
//  title, short, year, date, publisher, credits, form: catalogue facts (model-source/library/PLAN.md)
//  presenter  'book' (built), 'plan-chest' or 'map-table' (not built yet)
//  explorer   what the explorer layer for this volume will be
//  pages      folder holding manifest.json, sm/ and lg/ (relative to the site root)
//  spine      the shelf drawing: an original typographic design, not a copy of the real cover
//  book       settings for the book engine, for volumes that use it:
//    trim           page width / height, used until the manifest gives its own `aspect`
//    fallbackCount  number of pages to show as blank sheets when there is no scan
//    opensWithoutScan  true when the book may be opened on blank, numbered sheets
//    store          localStorage key for reader preferences
//    folio, heading, loading, name, histTitle: wording
//    editions       [{id, label, cover: 'case' | 'self', needsScan, cardLeaves, closed, closedBack}]
//                   'case': separate boards wrap the page block (drawn, with `coverTitle`).
//                   'self': the first and last scanned pages are the covers.
//    coverTitle     lines of lettering for a drawn case: [text, size, y] as fractions of the board
//    blankTints     {page: colour} for blank sheets that are not white
//    toc, tocNote   contents by scanned page
//    about(ctx), history(ctx), noScan: HTML; ctx = {standalone}

const MANUAL_TOC = [
 ['Front matter', [[2, 'Title sheet'], [3, 'Title page'], [4, 'Authorisation'], [5, 'Foreword I'], [7, 'Foreword II'], [8, 'Contents']]],
 ['General section', [[10, 'Section divider'], [13, 'Articles of Federation'], [33, 'Treaty of Peace'], [35, 'United Federation: banner and seal'], [37, 'United Nations'], [39, 'Planetary Confederation'], [41, 'United Planets'], [43, 'Star Empire'], [45, 'Alpha Centauri'], [47, 'Official type style'], [49, 'Uniform colour code']]],
 ['Command section', [[50, 'Section divider'], [53, 'Star Fleet Armed Forces'], [57, 'Star Fleet Academy'], [58, 'Fleet Headquarters'], [65, 'Insignia and rank'], [66, 'Duty uniforms and patterns'], [74, 'Fleet ship classifications'], [75, 'Heavy cruiser class'], [77, 'Destroyer class'], [79, 'Scout class'], [81, 'Transport/tug class'], [83, 'Transport containers'], [86, 'Mk IV starliner'], [88, 'Dreadnought class'], [90, 'Shuttlecraft'], [92, 'Staterooms'], [94, 'Main bridge'], [96, 'Command module and stations'], [102, 'Security section'], [103, 'Hand phasers'], [106, 'Ray gun']]],
 ['Sciences section', [[107, 'Section divider'], [110, 'Command intelligence'], [112, 'Sciences tricorder'], [115, 'Galactic coordinate system'], [119, 'Standard orbits'], [120, 'Milky Way galaxy'], [122, 'United Federation chart'], [123, 'Medical section'], [124, 'Medical instruments']]],
 ['Support services', [[133, 'Section divider'], [135, 'Communications'], [137, 'Communicator'], [139, 'Universal translator'], [140, 'Engineering'], [143, 'Impulse power unit'], [144, 'Main propulsion'], [145, 'Transporter'], [149, 'Hangar deck']]],
 ['Miscellaneous section', [[151, 'Vulcan lyrette'], [152, 'Tri-dimensional chess'], [154, 'Section divider'], [155, 'Star Fleet Command'], [156, 'Record forms']]],
];

const manualAbout = ({standalone: SA}) => `<section class="bk-notes" aria-label="About this edition">
 <div><strong>01 / THE OBJECT</strong><p>Ballantine Books published Franz Joseph’s manual in November 1975, stardate 7511.01 on the copyright page. The first printing was a red book in a removable black binder, with the words <em>Star Trek</em> only on a throwaway over-jacket. Later printings were paperbacks with printed covers.</p></div>
 <div><strong>02 / THIS COPY</strong><p>The pages are the owner’s own copy, a later paperback printing, scanned at 150 dpi. They are cleaned and sharpened on the owner’s computer${SA ? '. This copy is private to the owner’s account' : ' and are not published with this site'}. Choose <em>Owner’s copy</em> to read it in its own printed cover.</p></div>
 <div><strong>03 / THE RECONSTRUCTION</strong><p>The binder is drawn from booksellers’ descriptions, not from a photograph, so its lettering layout is an approximation. Leaves bend by arc length from a glued spine. Paper grain, gutter shading and stack edges are rendered live.</p></div>
</section>`;

const manualHistory = () => `<section class="bk-history" id="bk-history" aria-labelledby="bk-hist-title">
 <header><span class="eyebrow">Technical order 00 · Provenance</span><h2 id="bk-hist-title">How the manual came to be</h2>
 <p class="bk-lede">Franz Joseph Schnaubelt (1914–1994) was a Chicago-born design engineer who spent about thirty years at Convair, later General Dynamics, in San Diego. During the war he drew enemy aircraft from photographs by working their perspective backwards, and he used the same method on frames of <em>Star Trek</em> film. He said plainly that he was not a fan of the show. He wanted its future to be technically and scientifically correct, to give young fans something better than overpriced mimeographed scripts, and to steer them toward real engineering.</p></header>
 <ol class="bk-timeline">
  <li><time>14 Apr 1973</time><p>He takes his daughter Karen, 18, to a meeting of the S.T.A.R. San Diego fan club. He finds the members’ cardboard props poor, says so, and is told to show them how.</p></li>
  <li><time>15 Apr 1973</time><p>He draws the hand phaser and the communicator from film-clip slides. <button data-page="103">See the phasers ›</button></p></li>
  <li><time>Spring 1973</time><p>Fans arrive with wish-lists, and he realises they are asking for a technical manual. He writes to Gene Roddenberry, who encourages him.</p></li>
  <li><time>Sep–Dec 1973</time><p>As a side project he draws the <em>Booklet of General Ship’s Plans</em>, because he needs a full ship layout before he can draw the interiors.</p></li>
  <li><time>Apr 1974</time><p>Club members hand-assemble 500 blueprint sets in his house, and they are sold at Equicon ’74.</p></li>
  <li><time>May 1974</time><p>Paramount’s Lou Mindling sends the work to Ballantine Books. The blueprints are published a year later.</p></li>
  <li><time>Aug 1975</time><p>He ships the manual’s art: about 400 hours of research and 1,000 hours of drawing, all by hand.</p></li>
  <li><time>Nov 1975</time><p>The manual is published. The first printing is raised from 250,000 to 450,000 copies, against a typical first run of about 20,000. It is reported to reach #1 on the <em>New York Times</em> list that winter.</p></li>
  <li><time>1979–1984</time><p>Ship names from the manual are heard in <em>The Motion Picture</em>, and its pages appear on bridge displays in <em>Star Trek II</em> and <em>III</em>. <button data-page="74">See the classifications page ›</button></p></li>
  <li><time>2 Jun 1994</time><p>He dies weeks before his eightieth birthday. Karen carries on his work as Franz Joseph Designs.</p></li>
 </ol>
 <div class="bk-asides">
  <div><h3>Why the book is red</h3><p>His contract kept the words “Star Trek” off his work, so Ballantine put them on a removable over-jacket. He supplied a colour chip for the exact red. He kept the credits minimal so the book would read as a genuine Star Fleet document, and he answered fan mail in character on Star Fleet stationery.</p></div>
  <div><h3>Never canon, always present</h3><p>Relations with Roddenberry soured over a lost merchandising deal, a dispute over props for his <em>Planet Earth</em> pilot, the size of a credit line, and the copyright staying in Franz Joseph’s name. The manual has never been treated as canon. Even so, it started the genre of technical manuals for fictional spacecraft, and the game <em>Star Fleet Battles</em> was licensed from his estate.</p></div>
  <div><h3>Look in this copy</h3><p>Memory Alpha reports a printing quirk: the two anabolic protoplaser orders run in reverse order, as if that sheet were bound on the wrong edge. <button data-page="130">Open them ›</button></p></div>
 </div>
 <p class="bk-sources">Sources: Karen Dick and Greg Tyler, <a href="http://www.trekplace.com/fj-timeline.html" target="_blank" rel="noopener">Franz Joseph timeline</a> (1999, from his work log); <a href="http://www.trekplace.com/fj-kdint01.html" target="_blank" rel="noopener">interview with Karen Dick</a> (1999); Paul Newitt, <a href="http://www.trekplace.com/fj-fjnewittint01.html" target="_blank" rel="noopener">interview with Franz Joseph</a> (<em>Enterprise Incidents</em>, 1983–84); Williams and Durrans, <a href="http://www.trekplace.com/fj-fjwilliamsint01.html" target="_blank" rel="noopener">1976 interview</a>; Bob Rehak, <a href="https://graphic-engine.swarthmore.edu/franz-joseph-and-star-treks-blueprint-culture/" target="_blank" rel="noopener">Franz Joseph and Star Trek’s blueprint culture</a> (2012); <a href="https://memory-alpha.fandom.com/wiki/Star_Trek_Star_Fleet_Technical_Manual" target="_blank" rel="noopener">Memory Alpha</a>; <a href="https://en.wikipedia.org/wiki/Star_Trek_Star_Fleet_Technical_Manual" target="_blank" rel="noopener">Wikipedia</a>. The print runs and the #1 ranking come from the family’s records and have not been checked against the 1975 archives.</p>
</section>`;

export const VOLUMES = [
 {
  slug: 'blueprints', title: 'Star Trek Blueprints', short: 'Blueprints', year: 1975, date: 'Spring 1975',
  publisher: 'Ballantine Books', credits: 'Franz Joseph',
  form: 'Twelve large sheets in a plastic pouch.',
  presenter: 'plan-chest', presenterName: 'plan chest',
  explorer: 'A deck-by-deck index of the sheets, with the Constitution model’s sections laid over them and links to the manual’s interior pages (92–101 and 143–150).',
  pages: 'library/blueprints/pages/',
  spine: {w: 30, h: .9, bg: '#1d3a5c', fg: '#e6edf2', accent: '#8fb2cf', kind: 'pouch', lines: ['BLUEPRINTS'], foot: '12 SHEETS'},
 },
 {
  slug: 'manual', title: 'Star Fleet Technical Manual', short: 'The manual', year: 1975, date: 'November 1975',
  publisher: 'Ballantine Books', credits: 'Franz Joseph',
  form: 'A red book in a removable black binder (first printing); later printings were paperbacks.',
  presenter: 'book', presenterName: 'book',
  explorer: 'Already here: the Constitution class study, the fleet comparison and the equipment locker are all built from this book.',
  pages: 'book/pages/',
  spine: {w: 64, h: .96, bg: '#0b0b0c', fg: '#c9a34e', accent: '#c9a34e', kind: 'binder', lines: ['STAR FLEET', 'TECHNICAL MANUAL'], foot: 'TM:379260'},
  book: {
   trim: 0.7712, fallbackCount: 160, opensWithoutScan: true, store: 'sftm-book-v1',
   folio: 'THE MANUAL, 1975', folioRight: 'TM: 379260 · STARDATE 7511.01',
   heading: 'Star Fleet Technical Manual: virtual book', loading: 'Opening the manual…', name: 'the manual',
   histTitle: 'How the manual came to be', tocEyebrow: 'Technical orders',
   editions: [
    {id: 'binder', label: '1975 binder', cover: 'case', cardLeaves: [2], closed: 'Binder, closed', closedBack: 'Binder, closed (back)'},
    {id: 'copy', label: 'Owner’s copy', cover: 'self', needsScan: true, closed: 'Front cover', closedBack: 'Back cover'},
   ],
   coverTitle: [['STAR FLEET', .052, .215], ['TECHNICAL', .074, .305], ['MANUAL', .074, .39]],
   blankTints: {2: '#c8261f', 158: '#c8261f'},
   toc: MANUAL_TOC, tocNote: 'Numbers are pages of the scanned copy; the manual itself is not paginated.',
   about: manualAbout, history: manualHistory,
   noScan: '<strong>The pages are not published here.</strong> The manual is a copyrighted book, so this public site shows the binder and blank, numbered sheets. On the owner’s computer the pages come from their own scan: run <code>python3 model-source/book/render-pages.py &lt;scan.pdf&gt;</code> and serve <code>dist/</code> locally.',
  },
 },
 {
  slug: 'maps', title: 'Star Trek Maps', short: 'Maps', year: 1980, date: 'August 1980',
  publisher: 'Bantam Books', credits: 'Jeffrey Maynard (design and coordination); Geoffrey Mandel (astronomical art)',
  form: 'A box holding four four-colour wall maps and an instruction booklet.',
  presenter: 'map-table', presenterName: 'map table',
  explorer: 'An interactive chart of the United Federation, tied to the manual’s galactic coordinate system (page 115), standard orbits (page 119) and Federation chart (page 122).',
  pages: 'library/maps/pages/',
  spine: {w: 84, h: .74, bg: '#e9e4d2', fg: '#202321', accent: '#a72c25', kind: 'box', lines: ['MAPS'], foot: '4 CHARTS · BOOKLET'},
 },
 {
  slug: 'mr-scotts-guide', title: 'Mr. Scott’s Guide to the Enterprise', short: 'Mr. Scott’s Guide', year: 1987, date: '1987',
  publisher: 'Pocket Books', credits: 'Shane Johnson',
  form: 'Trade paperback.',
  presenter: 'book', presenterName: 'book',
  explorer: 'The refit Enterprise of the first four films, as a new 3D study to set beside the original Constitution class.',
  pages: 'library/mr-scotts-guide/pages/',
  spine: {w: 34, h: .86, bg: '#a72c25', fg: '#fffefa', accent: '#f4f2e9', kind: 'paperback', lines: ['MR. SCOTT’S GUIDE'], foot: 'NCC-1701 REFIT'},
  book: paperback('Mr. Scott’s Guide to the Enterprise', 'MR. SCOTT’S GUIDE, 1987', 'sftm-lib-mr-scotts-guide-v1'),
 },
 {
  slug: 'tng-technical-manual', title: 'Star Trek: The Next Generation Technical Manual', short: 'TNG Technical Manual', year: 1991, date: '1991',
  publisher: 'Pocket Books', credits: 'Rick Sternbach and Michael Okuda',
  form: 'Trade paperback.',
  presenter: 'book', presenterName: 'book',
  explorer: 'Optional: a Galaxy class study.',
  pages: 'library/tng-technical-manual/pages/',
  spine: {w: 40, h: .86, bg: '#686a60', fg: '#fffefa', accent: '#d8b25a', kind: 'paperback', lines: ['TNG TECHNICAL MANUAL'], foot: 'GALAXY CLASS'},
  book: paperback('Star Trek: The Next Generation Technical Manual', 'TNG TECHNICAL MANUAL, 1991', 'sftm-lib-tng-technical-manual-v1'),
 },
];

// A plain paperback read from a scan: the first and last scanned pages are its covers.
function paperback(title, folio, store) {
 return {
  trim: 0.7712, fallbackCount: 0, opensWithoutScan: false, store,
  folio, folioRight: 'OWNER’S COPY',
  heading: `${title}: virtual book`, loading: 'Opening the book…', name: 'the book', tocEyebrow: 'Contents',
  editions: [{id: 'copy', label: 'Owner’s copy', cover: 'self', needsScan: true, closed: 'Front cover', closedBack: 'Back cover'}],
  toc: [], tocNote: 'Numbers are pages of the scanned copy.',
  about: () => '', history: null, noScan: '',
 };
}

export const MANUAL = VOLUMES.find(v => v.slug === 'manual');
export const volumeBySlug = slug => VOLUMES.find(v => v.slug === slug) || null;

// A volume is available when its manifest loads and lists at least one page.
const manifests = new Map();
export function loadManifest(vol) {
 if (!manifests.has(vol.slug)) {
  manifests.set(vol.slug, fetch(vol.pages + 'manifest.json', {cache: 'no-cache'})
   .then(r => r.ok ? r.json() : null)
   .then(m => m && m.count > 0 ? m : null)
   .catch(() => null));
 }
 return manifests.get(vol.slug);
}
