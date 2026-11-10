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
//  shelf      'published' (default) or 'fan': which shelf it stands on
//  attribution, notice, blurb, link: for 'fan' volumes, the credits copied from the document itself
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
 // ---- The lower shelf: fan works and scholarship, each shown from the owner's copy of the file.
 // Every credit below is copied from the document's own pages (title page, publisher's information,
 // credits or bibliography). `notice` is the document's rights statement, quoted as printed.
 {
  slug: 'ships-of-the-line', shelf: 'fan', title: 'Jaynz Star Fleet, Volume 1: Ships of the Line', short: 'Ships of the Line', year: 2005, date: '2005 (foreword dated January 2005; file dated July 2005)',
  publisher: 'Neale Davidson, a free fan publication', credits: 'Neale Davidson',
  form: 'PDF, 36 letter-size pages.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A fan-made recognition guide to Star Fleet’s ships, set at stardate 7505.00. The foreword is signed by Neale Davidson, who dedicates the guide to his uncle Mike. The file’s first page carries no text layer, so the title here follows the file’s name.',
  attribution: [
   ['Author', 'Neale Davidson (foreword signed January 2005).'],
   ['Starship design credits, as printed', 'Anton, Larson, Loknar and Mackenzie classes: Dana Knutson, for Star Trek: The Role Playing Game (FASA). Capella class: Brian Pimenta, for the Star Trek Concordance (Ballantine Books). Cochise and Taurus classes: Neale Davidson. Constitution class: Matt Jefferies, for Star Trek (Desilu Productions). Decatur class: Todd Guenther, for Starship Design. Hellespont class: Steve Cole, for Star Fleet Battles. Hermes and Saladin classes: Franz Joseph, for the Star Trek Technical Manual (Ballantine Books). Miranda class: Joseph Jennings and Michael Minor, for Star Trek II: The Wrath of Khan (Paramount Pictures). Surya class: Aridas Sofia, for Ships of the Star Fleet.'],
  ],
  notice: 'Star Trek, Starship Enterprise, Constitution Class, and related likenesses are copyrights and trademarks of Paramount Pictures, Inc. This guide has been established for informational and entertainment purposes only. No infringement of copyright or trademark is intended.',
  pages: 'library/ships-of-the-line/pages/',
  spine: {w: 24, h: .86, bg: '#22303f', fg: '#e6edf2', accent: '#8fb2cf', kind: 'paperback', lines: ['SHIPS OF THE LINE'], foot: 'JAYNZ · VOL 1'},
 },
 {
  slug: 'ships-of-the-tech-manual', shelf: 'fan', title: 'Ships of the Star Fleet Technical Manual', short: 'Ships of the Tech Manual', year: 2006, date: '2006 (file dated October 2006)',
  publisher: 'Neale Davidson, a free fan publication', credits: 'Neale Davidson (chief editor)',
  form: 'PDF, 36 letter-size pages. Numbered TM:379260-2, stardate 7304.15.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A fan-made companion to Franz Joseph’s manual that works up the ship classes the manual lists. It carries the manual’s own document number with a suffix, TM:379260-2, and is dedicated “For Micheal G. Davidson”, as printed.',
  attribution: [
   ['Chief editor', 'Neale Davidson (www.pixelsagas.com, as printed).'],
   ['Copyright', '©2006 Neale Davidson.'],
   ['Based on, as printed', 'Star Trek Blueprints, ©1972 Ballantine Books. Star Trek Technical Manual, ©1975 Ballantine Books. Federation Reference Series (Vol. 1–6), ©1985 Star Fleet Printing Office. General Plans: Dollond Class, ©1991–1993 Patrick Lichty.'],
  ],
  notice: 'This document has been established for informational and entertainment purposes only. No infringement of copyright or trademark is intended.',
  pages: 'library/ships-of-the-tech-manual/pages/',
  spine: {w: 30, h: .86, bg: '#0f1012', fg: '#c9a34e', accent: '#c9a34e', kind: 'paperback', lines: ['SHIPS OF THE', 'TECH MANUAL'], foot: 'TM:379260-2'},
 },
 {
  slug: 'starfleet-compendium', shelf: 'fan', title: 'Jaynz’ Guide Series: Ships of Star Fleet, Compendium 01', short: 'Starfleet Compendium', year: 2006, date: '2006 (file dated January 2007)',
  publisher: 'Neale Davidson, a free fan publication (Jaynz’ Guide Series, Federation Star Fleet Series)', credits: 'Neale Davidson (chief editor), with the assistance of Stephen Charles Green',
  form: 'PDF, 158 letter-size pages. Numbered RS:480372-1-REV 01; “updated and approved for Terran year 2272”.',
  presenter: 'book', presenterName: 'book',
  blurb: 'The collected edition of Neale Davidson’s Star Fleet ship guides, set in the year 2272. Its credits page lists the published and fan works it draws on, and that list is repeated here in full.',
  attribution: [
   ['Chief editor', 'Neale Davidson (www.pixelsagas.com, as printed).'],
   ['Assistance', 'Stephen Charles Green.'],
   ['Copyright', '©2006 Neale Davidson.'],
   ['Based on, as printed', 'Star Trek, ©1966–1969 Desilu Productions Inc., ©1967–2006 Paramount Pictures, Inc., ©2006 CBS Studios, Inc. Star Trek Blueprints, ©1972 Ballantine Books. Star Trek Technical Manual, ©1975 Ballantine Books. Mr Scott’s Guide to the Enterprise, ©1980–1987 Pocket Books. Star Trek Spaceflight Chronology, ©1980 Pocket Books. Star Trek: The Motion Picture: 14 Official Blueprints, ©1980 Wallaby Press. Federation Reference Series (Vol. 1–6), ©1985 Star Fleet Printing Office. Star Trek: The Role Playing Game and related works, ©1982–1991 FASA Corp., ©1991–200X Last Unicorn Games, Inc., ©2002–2005 Decipher, Inc. Star Fleet Battles and related works, ©2006 Amarillo Design Bureau (printed “Armarillo”). Star Trek Encyclopedia, ©1994–1999 Pocket Books.'],
  ],
  notice: 'This document has been established for informational and entertainment purposes only. No infringement of copyright or trademark is intended.',
  pages: 'library/starfleet-compendium/pages/',
  spine: {w: 44, h: .86, bg: '#3c4a3e', fg: '#f4f2e9', accent: '#d8b25a', kind: 'paperback', lines: ['SHIPS OF STAR FLEET', 'COMPENDIUM'], foot: 'JAYNZ · 01'},
 },
 {
  slug: 'star-fleet-handbook-14', shelf: 'fan', title: 'Star Fleet Handbook, Volume 14', short: 'Star Fleet Handbook 14', year: 2007, date: '2007 (revived edition)',
  publisher: 'Federation Reference Series Online, a free fanzine', credits: 'Created by Geoffrey Mandel; revived by the Federation Reference Series',
  form: 'PDF of 18 scanned pages. Headed TM:379260-0, authenticated stardate 7812.13.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A revival of Geoffrey Mandel’s 1970s fanzine. The foreword says Mandel and his friends published thirteen issues as a follow-up to the Technical Manual, that material for a never-released fourteenth went into the U.S.S. Enterprise Officer’s Manual, and that the Federation Reference Series revived the title “with the kind permission of SFH creator Geoffery Mandel himself”. This issue spells his first name “Geoffery” throughout.',
  attribution: [
   ['Creator', 'Geoffrey Mandel (printed “Geoffery Mandel”).'],
   ['Revived edition', '© 2007 Federation Reference Series Online, all rights reserved.'],
   ['Page format', 'Based on the efforts of Franz Joseph as seen in the Star Fleet Technical Manual, © 1975 Ballantine Books, all rights reserved (as printed).'],
   ['Contributors', 'The issue takes submissions from readers. Individual pages carry their own credits where the issue gives them.'],
  ],
  notice: 'STAR FLEET HANDBOOK created by Geoffery Mandel. Revived edition (c) 2007 Federation Reference Series Online, all rights reserved. Original page format based on the efforts of Franz Joseph as seen in the STAR FLEET TECHNICAL MANUAL (c) 1975 Ballantine Books, all rights reserved.',
  pages: 'library/star-fleet-handbook-14/pages/',
  spine: {w: 18, h: .86, bg: '#e9e4d2', fg: '#202321', accent: '#a72c25', kind: 'zine', lines: ['FLEET HANDBOOK'], foot: 'NO. 14'},
 },
 {
  slug: 'starship-handbook-3', shelf: 'fan', title: 'Starship Handbook, Volume 3: Alpha & Beta Quadrants', short: 'Starship Handbook 3', year: 2007, date: 'First edition, autumn 2007; version 1.14, 2 June 2009',
  publisher: 'Mark Gill, a free fan ebook (trek.escape-committee.co.uk, as printed)', credits: 'Compiled by Mark Gill',
  form: 'PDF, 44 A5 pages.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A pocket-size fan reference to the ships of the Klingons, Romulans and the other powers of the Alpha and Beta Quadrants. The compiler says he tried to contact the owners of the images he used, and credits a designer or source ship by ship. His bibliography is repeated here in full.',
  attribution: [
   ['Compiler', 'Mark Gill.'],
   ['Books, as listed', 'Decipher Starships sourcebook (Bridges et al). Spacedock Ship Recognition Manual (Stephen S. Long). Star Fleet Technical Manual (Franz Joseph). Starship Recognition Manual Beta (Robert Hamilton III). Starship Spotter (Adam Lebowitz and Rob Bonchune). Star Trek Concordance (Bjo Trimble). Star Trek Encyclopedia (Michael Okuda, Denise Okuda and Debbie Mirek). Star Trek Fact Files and Star Trek: The Magazine. Star Trek: Deep Space Nine Technical Manual (Zimmerman, Drexler and Sternbach). Star Trek: The Next Generation Technical Manual (Sternbach and Okuda).'],
   ['Websites, as listed', 'Daystrom Institute Technical Library. Eavesdropping with Johnny. Ex Astris Scientia. Memory Alpha. Memory Beta. Neutral Zone Starship Database. Starship Schematic Database. STARTREK.com. Star Trek LCARS Blueprints Database. Star Trek Minutiae. ST Starship Tactical Combat Simulator Online Database.'],
   ['Games, as listed', 'Starfleet Command 3 and Star Trek: Armada 2 (Activision).'],
   ['Images, as credited', 'Colour side views from Ex Astris Scientia (the Romulan Mogai by Animaniac). Emblems from Ex Astris Scientia and Star Trek Minutiae; the Tholian and Breen emblems by Kristian Trigwell, the Tholian emblem originally by Geoffrey Mandel. Each ship’s entry names its designer and the source of its schematic.'],
  ],
  notice: 'This ebook has been produced by a fellow fan for reference and fun. All copyrights are acknowledged.',
  pages: 'library/starship-handbook-3/pages/',
  spine: {w: 22, h: .84, bg: '#5a1f1b', fg: '#fffefa', accent: '#e9b4a8', kind: 'paperback', lines: ['STARSHIP HANDBOOK'], foot: 'VOL 3'},
 },
 {
  slug: 'four-years-war-2', shelf: 'fan', title: 'Ships of the Four Years War, Volume Two', short: 'Four Years War II', year: 2008, date: '2006–2008 (file dated August 2008)',
  publisher: 'Neale Davidson, a free fan publication', credits: 'Neale Davidson, based on the works of Dana Knutson and Mitch O’Connell',
  form: 'PDF, 28 landscape letter-size pages. Numbered RS:480375-1.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A landscape fan guide to the ships of the Four Years War, the conflict set out in FASA’s role-playing game. The title page credits it as “based on the works of Dana Knutson and Mitch O’Connell”.',
  attribution: [
   ['Chief editor', 'Neale Davidson (www.pixelsagas.com, as printed).'],
   ['Based on the works of', 'Dana Knutson and Mitch O’Connell.'],
   ['Copyright', '©2006–2008 Neale Davidson.'],
   ['Based on, as printed', 'Star Trek Blueprints, ©1972 Ballantine Books. Star Trek Technical Manual, ©1975 Ballantine Books. Federation Ship Recognition Manual, ©1983 FASA, Inc. Four Years War, 1983 FASA, Inc. General Plans: Dollond Class, ©1991–1993 Patrick Lichty.'],
  ],
  notice: 'This document has been established for informational and entertainment purposes only. No infringement of copyright or trademark is intended.',
  pages: 'library/four-years-war-2/pages/',
  spine: {w: 20, h: .66, bg: '#4a3a5c', fg: '#f4f2e9', accent: '#c9b6e0', kind: 'paperback', lines: ['FOUR YEARS WAR'], foot: 'VOL TWO'},
 },
 {
  slug: 'fighting-starships', shelf: 'fan', title: 'Mandel’s Fighting Starships: Federation Fleet Review, 2290–91', short: 'Fighting Starships', year: 2015, date: '2015 (file dated June 2016)',
  publisher: 'Richard E. Mandel, a free reference work', credits: 'Richard E. Mandel',
  form: 'PDF, 377 landscape pages.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A 377-page fleet review in the manner of a naval annual. Its author calls it “a free scholarly reference work”, says it is “not sponsored, approved, or authorized by CBS Paramount”, and dedicates it to “pioneering Trek tech uber-fan Geoffery Mandel”, as printed. Visual materials are reproduced, it says, with permission or under fair use, and are credited in the book itself.',
  attribution: [
   ['Author', 'Richard E. Mandel.'],
   ['Copyright', 'Manuscript copyright © 2015 by Richard E. Mandel, all rights reserved.'],
   ['Star Trek', 'Stated in the book to be the property of CBS Paramount.'],
   ['Illustrations', 'Credited to their makers in the book’s own pages; reproduced there with permission or under fair use, by the author’s statement.'],
  ],
  notice: 'Manuscript copyright © 2015 by Richard E. Mandel, all rights reserved. “This is a free work for my fellow Trekkers everywhere.”',
  pages: 'library/fighting-starships/pages/',
  spine: {w: 60, h: .68, bg: '#14213a', fg: '#e6edf2', accent: '#d8b25a', kind: 'paperback', lines: ['MANDEL’S', 'FIGHTING STARSHIPS'], foot: 'FLEET REVIEW 2290–91'},
 },
 {
  slug: 'rehak-model-building', shelf: 'fan', title: 'From Model Building to 3D Printing: Star Trek and Build Code Across the Analog/Digital Divide', short: 'Rehak, Model Building', year: 2018, date: '2018',
  publisher: 'Routledge (chapter 12 of The Routledge Companion to Media Fandom, pages 114–122); this copy from Swarthmore College Libraries’ Works', credits: 'Bob Rehak (Swarthmore College)',
  form: 'PDF, a repository cover sheet and nine pages.',
  presenter: 'book', presenterName: 'book',
  blurb: 'A scholarly chapter on fans who build the hardware of Star Trek, from model kits and blueprints to 3D printing. It is the one academic work on the shelf, and the same author’s 2012 essay on Franz Joseph is a source for the lineage page.',
  attribution: [
   ['Author', 'Bob Rehak, Swarthmore College.'],
   ['Citation, as the repository gives it', 'Bob Rehak. (2018). “From Model Building To 3D Printing: Star Trek And Build Code Across The Analog/Digital Divide”. Routledge Companion To Media Fandom. 114–122.'],
   ['Repository', 'Swarthmore College Libraries’ Works, Film & Media Studies Faculty Works: https://works.swarthmore.edu/fac-film-media/61'],
  ],
  link: ['Read it at Swarthmore Works', 'https://works.swarthmore.edu/fac-film-media/61'],
  notice: 'This work is brought to you for free by Swarthmore College Libraries’ Works.',
  pages: 'library/rehak-model-building/pages/',
  spine: {w: 18, h: .8, bg: '#f4f2e9', fg: '#202321', accent: '#686a60', kind: 'zine', lines: ['REHAK · BUILD CODE'], foot: '2018'},
 },
 {
  slug: 'constitution-remastered', shelf: 'fan', title: 'Franz Joseph Remastered: Booklet of General Plans, U.S.S. Constitution Class', short: 'General Plans, remastered', year: 2024, date: 'Second edition, 27 August 2024',
  publisher: 'WillCAD, a digitized edition', credits: 'Franz Joseph Schnaubelt (original plans, 1973); redrawn by WillCAD',
  form: 'PDF: a title sheet, thirteen long sheets and a 21 × 36 inch five-view poster.',
  presenter: 'book', presenterName: 'book',
  blurb: 'The title sheet describes it: all twelve sheets of Franz Joseph’s Booklet of General Plans, “painstakingly redrawn using modern computer-aided drafting software”, with two bonuses, Geoffrey Mandel’s 1978 warp nacelle and a five-view poster in a format by Patrick Cumby. Each long sheet is shown here across an open spread, so the left and right pages are two halves of one drawing.',
  attribution: [
   ['Original plans', 'Franz Joseph Schnaubelt. Each sheet carries “© 1973 Paramount Pictures Corporation”.'],
   ['Digitized edition', '© 2024 WillCAD. Second edition, dated 27 August 2024.'],
   ['Bonus sheet', 'Warp nacelle, © 1978 Geoffrey Mandel.'],
   ['Poster', 'Five-view poster; “Poster format by Patrick Cumby 2021”.'],
  ],
  notice: '© 1973 Paramount Pictures Corporation. Digitized Edition © 2024 WillCAD. © 1978 Geoffrey Mandel. Poster format by Patrick Cumby 2021.',
  pages: 'library/constitution-remastered/pages/',
  spine: {w: 30, h: .9, bg: '#1d3a5c', fg: '#e6edf2', accent: '#8fb2cf', kind: 'pouch', lines: ['GENERAL PLANS'], foot: 'REMASTERED 2024'},
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

// A fan work or paper read from the owner's copy of its file: the first and last pages are its covers.
// Its credits panel is built from the volume's own `attribution` and `notice`.
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
function fanbook(v) {
 return {
  trim: 0.7727, fallbackCount: 0, opensWithoutScan: false, store: `sftm-lib-${v.slug}-v1`,
  folio: `${v.short.toUpperCase()}, ${v.year}`, folioRight: 'OWNER’S COPY OF THE FILE',
  heading: `${v.title}: virtual book`, loading: 'Opening the volume…', name: 'the volume', tocEyebrow: 'Contents',
  editions: [{id: 'copy', label: 'Owner’s file', cover: 'self', needsScan: true, closed: 'First page', closedBack: 'Last page'}],
  toc: [], tocNote: 'Numbers are pages as shown here.',
  about: ({standalone: SA}) => `<section class="bk-notes bk-credits" aria-label="Credits for this document">
 <div><strong>01 / THE DOCUMENT</strong><p>${esc(v.blurb)}</p><p>${esc(v.publisher)}, ${esc(v.date)}. ${esc(v.form)}</p></div>
 <div><strong>02 / CREDITS</strong>${v.attribution.map(([k, t]) => `<p><b>${esc(k)}.</b> ${esc(t)}</p>`).join('')}</div>
 <div><strong>03 / RIGHTS AND THIS COPY</strong><p>The document’s own notice: “${esc(v.notice)}”</p><p>All of it is the work of the people credited here. It is shown from the owner’s copy of the file${SA ? ', which is private to the owner’s account' : '; the pages are not published with this site'}. Nothing in it has been altered. Pages are only resized to fit the book, and a blank page is added where a volume needs an even number.</p>${v.link ? `<p><a href="${v.link[1]}" target="_blank" rel="noopener">${esc(v.link[0])} ›</a></p>` : ''}</div>
</section>`,
  history: null, noScan: '',
 };
}
VOLUMES.forEach(v => { if (v.shelf === 'fan') v.book = fanbook(v); else v.shelf = 'published'; });
export const SHELVES = [
 {id: 'published', name: 'Published volumes', note: '1975–1991'},
 {id: 'fan', name: 'Fan works and scholarship', note: '2005–2024'},
];

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
