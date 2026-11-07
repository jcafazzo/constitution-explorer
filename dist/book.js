// #/book: a virtual copy of the 1975 Star Fleet Technical Manual.
//
// Each leaf is a thin slab bent along a curve: rooted at the spine, it rises
// through the glued gutter, and its bend is integrated by arc length so the
// paper never stretches. A turn blends the leaf's resting curve on the right
// stack into its resting curve on the left, and adds a curl that leads early
// and relaxes late (or follows the reader's finger, with a twist toward the
// corner they grabbed). Pages under the turning leaf are real geometry, so the
// leaf's shadow falls across them. Page images are generated locally from the
// owner's scan by model-source/book/render-pages.py. They are never published,
// and without them the book still opens on blank, numbered sheets.
import * as THREE from './vendor/three.module.js';

const BASE = 'book/pages/';
const W = 0.7712, H = 1;                 // trim, height = 1 unit
const T = {paper: 0.00042, card: 0.0013, board: 0.0085};
const G = {paper: 0.17, card: 0.12, board: 0.03};
const SU = 40, SV = 10;                  // grid segments across and down a leaf
const STORE = 'sftm-book-v1';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

// Contents, by PDF page of the owner's scan (page headings, abbreviated).
const TOC = [
 ['Front matter', [[2, 'Title sheet'], [3, 'Title page'], [4, 'Authorisation'], [5, 'Foreword I'], [7, 'Foreword II'], [8, 'Contents']]],
 ['General section', [[10, 'Section divider'], [13, 'Articles of Federation'], [33, 'Treaty of Peace'], [35, 'United Federation: banner and seal'], [37, 'United Nations'], [39, 'Planetary Confederation'], [41, 'United Planets'], [43, 'Star Empire'], [45, 'Alpha Centauri'], [47, 'Official type style'], [49, 'Uniform colour code']]],
 ['Command section', [[50, 'Section divider'], [53, 'Star Fleet Armed Forces'], [57, 'Star Fleet Academy'], [58, 'Fleet Headquarters'], [65, 'Insignia and rank'], [66, 'Duty uniforms and patterns'], [74, 'Fleet ship classifications'], [75, 'Heavy cruiser class'], [77, 'Destroyer class'], [79, 'Scout class'], [81, 'Transport/tug class'], [83, 'Transport containers'], [86, 'Mk IV starliner'], [88, 'Dreadnought class'], [90, 'Shuttlecraft'], [92, 'Staterooms'], [94, 'Main bridge'], [96, 'Command module and stations'], [102, 'Security section'], [103, 'Hand phasers'], [106, 'Ray gun']]],
 ['Sciences section', [[107, 'Section divider'], [110, 'Command intelligence'], [112, 'Sciences tricorder'], [115, 'Galactic coordinate system'], [119, 'Standard orbits'], [120, 'Milky Way galaxy'], [122, 'United Federation chart'], [123, 'Medical section'], [124, 'Medical instruments']]],
 ['Support services', [[133, 'Section divider'], [135, 'Communications'], [137, 'Communicator'], [139, 'Universal translator'], [140, 'Engineering'], [143, 'Impulse power unit'], [144, 'Main propulsion'], [145, 'Transporter'], [149, 'Hangar deck']]],
 ['Miscellaneous section', [[151, 'Vulcan lyrette'], [152, 'Tri-dimensional chess'], [154, 'Section divider'], [155, 'Star Fleet Command'], [156, 'Record forms']]],
];
const FLAT = TOC.flatMap(([s, e]) => e.map(([n, t]) => ({n, t, s}))).sort((a, b) => a.n - b.n);
const titleFor = n => { let r = null; for (const e of FLAT) if (e.n <= n) r = e; return r; };

const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
const ease = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

export function renderBook(main, path) {
 let alive = true;
 const initial = parseInt(path.split('/')[2], 10);
 main.classList.add('book-route');
 main.innerHTML = `<div class="folio"><span><a href="#/">COMMAND SECTION</a> / THE MANUAL, 1975</span><span>TM: 379260 · STARDATE 7511.01</span></div>
<section class="bk" aria-labelledby="bk-title">
 <h1 id="bk-title" class="sr-only">Star Fleet Technical Manual: virtual book</h1>
 <div class="bk-stage" id="bk-stage" tabindex="0" role="region" aria-roledescription="book" aria-label="The book. Left and right arrows turn the page; drag a page corner to curl it. Scroll, pinch, double-click or plus and minus zoom in place; drag to pan while zoomed; zero or Escape resets.">
  <div class="bk-zhint" id="bk-zhint" hidden><span id="bk-zhint-t">Drag to pan · double-${matchMedia('(pointer: coarse)').matches ? 'tap' : 'click'} to return</span><button class="bk-btn" id="bk-zreset">Whole book</button></div>
  <span class="bk-loading" role="status">Opening the manual…</span>
 </div>
 <div class="bk-bar" role="toolbar" aria-label="Book controls">
  <button class="bk-btn" id="bk-prev" aria-label="Previous page">‹</button>
  <div class="bk-scrub"><input id="bk-range" type="range" min="0" max="1" value="0" aria-label="Position in the book"><output id="bk-where" for="bk-range">Closed</output></div>
  <button class="bk-btn" id="bk-next" aria-label="Next page">›</button>
  <div class="bk-tools">
   <button class="bk-btn" id="bk-toc-btn" aria-expanded="false" aria-controls="bk-toc">Contents</button>
   <div class="bk-zoom" role="group" aria-label="Zoom"><button class="bk-btn" id="bk-zout" aria-label="Zoom out">−</button><output id="bk-zval" aria-live="off">100%</output><button class="bk-btn" id="bk-zin" aria-label="Zoom in">+</button></div>
   <button class="bk-btn" id="bk-zoom-btn" title="Open the page flat, on its own">Page view</button>
   <div class="bk-seg" role="group" aria-label="Edition"><button id="bk-ed-binder" aria-pressed="true">1975 binder</button><button id="bk-ed-copy" aria-pressed="false">Owner’s copy</button></div>
   <button class="bk-btn" id="bk-age" aria-pressed="false" title="Tone the paper as fifty years of shelf life would">Aged paper</button>
   <button class="bk-btn" id="bk-sound" aria-pressed="true">Sound</button>
   <button class="bk-btn" id="bk-full" aria-label="Full screen">⛶</button>
  </div>
 </div>
 <aside class="bk-toc" id="bk-toc" hidden aria-label="Contents"><div class="bk-toc-head"><span class="eyebrow">Technical orders</span><button class="bk-btn" id="bk-toc-close" aria-label="Close contents">×</button></div>
  ${TOC.map(([s, e]) => `<h3>${esc(s)}</h3><ol>${e.map(([n, t]) => `<li><button data-page="${n}"><span>${esc(t)}</span><b>${n}</b></button></li>`).join('')}</ol>`).join('')}
  <p class="bk-small">Numbers are pages of the scanned copy; the manual itself is not paginated.</p></aside>
 <div class="bk-loupe" id="bk-loupe" hidden role="dialog" aria-modal="true" aria-label="Magnified page">
  <div class="bk-loupe-view" id="bk-loupe-view"><img id="bk-loupe-img" alt="" draggable="false"></div>
  <div class="bk-loupe-bar"><button class="bk-btn" id="bk-l-prev" aria-label="Previous page">‹</button><span id="bk-l-label"></span><button class="bk-btn" id="bk-l-next" aria-label="Next page">›</button><button class="bk-btn" id="bk-l-out" aria-label="Zoom out">−</button><button class="bk-btn" id="bk-l-in" aria-label="Zoom in">+</button><button class="bk-btn" id="bk-l-fit">Fit</button><button class="bk-btn" id="bk-l-close" aria-label="Close magnifier">Close</button></div>
 </div>
 <p class="sr-only" aria-live="polite" id="bk-live"></p>
</section>
<section class="bk-notes" aria-label="About this edition">
 <div><strong>01 / THE OBJECT</strong><p>Ballantine Books published Franz Joseph’s manual in November 1975, stardate 7511.01 on the copyright page. Booksellers describe the first printing as a red softcover inside a removable black vinyl binder stamped in gold, like a real service manual. Later printings were paperbacks with printed covers.</p></div>
 <div><strong>02 / THIS COPY</strong><p>The pages are the owner’s own copy, a later paperback printing, scanned at 150 dpi. They are cleaned and sharpened on the owner’s computer and are not published with this site. Choose <em>Owner’s copy</em> to read it in its own printed cover.</p></div>
 <div><strong>03 / THE RECONSTRUCTION</strong><p>The binder is drawn from booksellers’ descriptions, not from a photograph, so its lettering layout is an approximation. Leaves bend by arc length from a glued spine. Paper grain, gutter shading and stack edges are rendered live.</p></div>
</section>`;

 const $ = s => main.querySelector(s);
 const stage = $('#bk-stage'), live = $('#bk-live'), range = $('#bk-range'), where = $('#bk-where');
 let prefs = {edition: 'binder', sound: true, aged: false};
 try { Object.assign(prefs, JSON.parse(localStorage.getItem(STORE) || '{}')); } catch {}
 const savePrefs = () => { try { localStorage.setItem(STORE, JSON.stringify(prefs)); } catch {} };

 // ---------- renderer and scene ----------
 let renderer;
 try { renderer = new THREE.WebGLRenderer({antialias: true, powerPreference: 'high-performance'}); }
 catch (e) { stage.innerHTML = '<p class="bk-fallback">This book needs WebGL, which this browser has turned off.</p>'; return () => { main.classList.remove('book-route'); }; }
 const phone = matchMedia('(max-width: 700px)').matches;
 renderer.setPixelRatio(Math.min(devicePixelRatio, phone ? 2 : 2));
 renderer.outputColorSpace = THREE.SRGBColorSpace;
 renderer.toneMapping = THREE.NeutralToneMapping;
 renderer.toneMappingExposure = 1.0;
 renderer.shadowMap.enabled = true;
 renderer.shadowMap.type = THREE.PCFSoftShadowMap;
 stage.appendChild(renderer.domElement);
 renderer.domElement.setAttribute('aria-hidden', 'true');
 const maxAniso = renderer.capabilities.getMaxAnisotropy();

 const scene = new THREE.Scene();
 scene.background = new THREE.Color('#17120d');
 const camera = new THREE.PerspectiveCamera(26, 1, 0.05, 20);
 const book = new THREE.Group();
 scene.add(book);

 // Environment for the gold foil and vinyl sheen: a dim room with one softbox.
 {
  const env = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.SphereGeometry(5, 24, 12), new THREE.MeshBasicMaterial({color: '#2a2018', side: THREE.BackSide}));
  env.add(room);
  const box = (c, x, y, z, w, h) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({color: c, side: THREE.DoubleSide})); m.position.set(x, y, z); m.lookAt(0, 0, 0); env.add(m); };
  box('#fff1d8', -2.2, 2.4, 3.2, 2.6, 1.6);
  box('#6d5a44', 3, -1, 2, 3, 2);
  box('#ffffff', 0, 0, 4.6, 1, 1);
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(env, 0.04).texture;
  scene.environmentIntensity = 0.35;
  pm.dispose();
 }
 scene.add(new THREE.HemisphereLight('#fff8ee', '#3b2a1b', 0.7));
 const key = new THREE.DirectionalLight('#fff0dc', 2.4);
 key.position.set(-1.1, 1.25, 2.4);
 key.castShadow = true;
 key.shadow.mapSize.set(phone ? 1024 : 2048, phone ? 1024 : 2048);
 Object.assign(key.shadow.camera, {left: -1.1, right: 1.1, top: 0.8, bottom: -0.8, near: 0.5, far: 6});
 key.shadow.bias = -0.0004;
 key.shadow.normalBias = 0.012;
 key.shadow.radius = 4;
 scene.add(key);
 const fill = new THREE.DirectionalLight('#cfe0ff', 0.35);
 fill.position.set(1.4, -0.6, 1.8);
 scene.add(fill);

 // ---------- procedural textures ----------
 const canvasTex = (w, h, draw, srgb = true) => {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = maxAniso;
  return t;
 };
 const noise = (g, w, h, amt, base, scale = 1) => {
  const img = g.getImageData(0, 0, w, h), d = img.data;
  for (let i = 0; i < d.length; i += 4) { const n = (Math.random() - .5) * amt * scale; d[i] = clamp(d[i] + n, 0, 255); d[i + 1] = clamp(d[i + 1] + n, 0, 255); d[i + 2] = clamp(d[i + 2] + n, 0, 255); }
  g.putImageData(img, 0, 0);
 };
 // Paper tooth: fibres and fine mottling, used as a bump map on every page.
 const fibre = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#808080'; g.fillRect(0, 0, w, h); noise(g, w, h, 46);
  g.globalAlpha = .08;
  for (let i = 0; i < 900; i++) { g.strokeStyle = Math.random() < .5 ? '#000' : '#fff'; g.lineWidth = Math.random() * 1.2 + .3; g.beginPath(); const x = Math.random() * w, y = Math.random() * h, a = Math.random() * Math.PI, l = 4 + Math.random() * 18; g.moveTo(x, y); g.quadraticCurveTo(x + Math.cos(a + .6) * l / 2, y + Math.sin(a + .6) * l / 2, x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
 }, false);
 fibre.wrapS = fibre.wrapT = THREE.RepeatWrapping; fibre.repeat.set(3, 4);
 // Stacked leaf edges seen on the fore-edge, head and tail of the page blocks.
 const edgeTex = canvasTex(16, 256, (g, w, h) => {
  for (let y = 0; y < h; y++) { const v = 222 + Math.random() * 20 - (y % 4 === 0 ? 26 : 0); g.fillStyle = `rgb(${v},${v - 5},${v - 16})`; g.fillRect(0, y, w, 1); }
 });
 edgeTex.wrapS = edgeTex.wrapT = THREE.RepeatWrapping;
 // Black vinyl: pebbled grain.
 const vinylBump = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#808080'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 9000; i++) { const x = Math.random() * w, y = Math.random() * h, r = Math.random() * 2.4 + .6; const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, 'rgba(255,255,255,.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); }
  noise(g, w, h, 20);
 }, false);
 vinylBump.wrapS = vinylBump.wrapT = THREE.RepeatWrapping; vinylBump.repeat.set(4, 5);

 const TW = 1024, TH = Math.round(TW / W);
 const seam = (g, w, h, inset, col = 'rgba(255,255,255,.07)') => { g.strokeStyle = col; g.lineWidth = 3; g.setLineDash([]); g.strokeRect(inset, inset, w - inset * 2, h - inset * 2); g.strokeStyle = 'rgba(0,0,0,.6)'; g.lineWidth = 2; g.strokeRect(inset + 3, inset + 3, w - inset * 2 - 6, h - inset * 2 - 6); };
 const drawTitle = (g, w, h, fill) => {
  g.fillStyle = fill; g.textAlign = 'center'; g.textBaseline = 'alphabetic';
  g.font = `${Math.round(w * .052)}px Michroma, Arial, sans-serif`;
  g.fillText('STAR FLEET', w / 2, h * .215);
  g.font = `${Math.round(w * .074)}px Michroma, Arial, sans-serif`;
  g.fillText('TECHNICAL', w / 2, h * .305);
  g.fillText('MANUAL', w / 2, h * .39);
  g.fillRect(w * .3, h * .43, w * .4, Math.max(2, w * .003));
 };
 let faceCache = new Map();
 const procFace = (k) => {
  if (faceCache.has(k)) return faceCache.get(k);
  let f;
  if (k === 'vinylFront') {
   const map = canvasTex(TW, TH, (g, w, h) => { g.fillStyle = '#0b0b0c'; g.fillRect(0, 0, w, h); noise(g, w, h, 10); seam(g, w, h, w * .035); drawTitle(g, w, h, '#c9a34e'); });
   const rough = canvasTex(TW, TH, (g, w, h) => { g.fillStyle = '#9a9a9a'; g.fillRect(0, 0, w, h); drawTitle(g, w, h, '#4a4a4a'); }, false);
   const metal = canvasTex(TW, TH, (g, w, h) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); drawTitle(g, w, h, '#fff'); }, false);
   f = {map, rough, metal, vinyl: true};
  } else if (k === 'vinylInside' || k === 'vinylBack') {
   const map = canvasTex(512, Math.round(512 / W), (g, w, h) => { g.fillStyle = '#0c0c0d'; g.fillRect(0, 0, w, h); noise(g, w, h, 8); seam(g, w, h, w * .035); if (k === 'vinylInside') { g.strokeStyle = 'rgba(255,255,255,.08)'; g.lineWidth = 2; g.beginPath(); g.moveTo(w * .8, h * .035); g.lineTo(w * .8, h * .965); g.stroke(); } });
   f = {map, vinyl: true};
  } else if (k === 'cardInside') {
   f = {map: canvasTex(256, Math.round(256 / W), (g, w, h) => { g.fillStyle = '#f3efe4'; g.fillRect(0, 0, w, h); noise(g, w, h, 6); })};
  } else if (k.startsWith('blank')) {
   const n = +k.slice(5);
   f = {map: canvasTex(512, Math.round(512 / W), (g, w, h) => {
    g.fillStyle = n === 2 || n === 158 ? '#c8261f' : '#fbfaf6'; g.fillRect(0, 0, w, h);
    noise(g, w, h, 5);
    g.fillStyle = n === 2 || n === 158 ? 'rgba(0,0,0,.4)' : 'rgba(40,36,30,.42)';
    g.font = '11px "Space Mono", monospace'; g.textAlign = 'center';
    g.fillText(String(n), w / 2, h * .955);
   })};
  }
  faceCache.set(k, f);
  return f;
 };

 // ---------- page images, lazily loaded ----------
 let manifest = null;
 const pageCache = new Map();            // n -> {tex, used}
 const blankWhite = new THREE.DataTexture(new Uint8Array([250, 249, 244, 255]), 1, 1); blankWhite.colorSpace = THREE.SRGBColorSpace; blankWhite.needsUpdate = true;
 const pageTex = (n) => {
  let e = pageCache.get(n);
  if (!e) {
   const tex = new THREE.Texture(); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = maxAniso;
   e = {tex, ready: false}; pageCache.set(n, e);
   const img = new Image(); img.decoding = 'async';
   img.onload = () => { if (!alive || pageCache.get(n) !== e) return; tex.image = img; tex.needsUpdate = true; e.ready = true; dirty = true; };
   img.onerror = () => { e.failed = true; };
   img.src = `${BASE}sm/p${String(n).padStart(3, '0')}.webp`;
  }
  e.used = performance.now();
  return e;
 };
 // The settled spread is re-textured from the 2048 px images when the page is shown large.
 const hiRes = new Map();
 const wantHi = () => zoom > 1.15 || stage.clientHeight * Math.min(devicePixelRatio, 2) > 1150;
 const refreshHi = () => {
  const want = new Set(manifest && wantHi() ? (single ? currentPages() : spreadPages(cur).filter(Boolean)) : []);
  for (const [n, e] of hiRes) if (!want.has(n)) { e.tex.dispose(); hiRes.delete(n); }
  for (const n of want) if (!hiRes.has(n)) {
   const tex = new THREE.Texture(); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = maxAniso;
   const e = {tex, ready: false}; hiRes.set(n, e);
   const img = new Image(); img.decoding = 'async';
   img.onload = () => { if (!alive || hiRes.get(n) !== e) return; tex.image = img; tex.needsUpdate = true; e.ready = true; dirty = true; };
   img.src = `${BASE}lg/p${String(n).padStart(3, '0')}.webp`;
  }
 };
 const prune = () => {
  const keep = new Set(); for (const i of [0, N - 1, ...Array.from({length: 9}, (_, k) => cur - 4 + k)]) { const l = leaves[i]; if (!l) continue; if (l.front.p) keep.add(l.front.p); if (l.back.p) keep.add(l.back.p); }
  for (const [k, f] of faceCache) if (k.startsWith('blank') && !keep.has(+k.slice(5))) { f.map.dispose(); faceCache.delete(k); }
  if (pageCache.size < 28) return;
  for (const [n, e] of pageCache) if (!keep.has(n)) { e.tex.dispose(); pageCache.delete(n); }
 };

 // ---------- materials ----------
 const ageU = {value: prefs.aged ? 1 : 0};
 const pageMaterial = (face, flip) => {
  let map = blankWhite, proc = null, ready = true;
  if (face.p) {
   if (manifest) { const e = pageTex(face.p); map = e.tex.image ? e.tex : blankWhite; ready = e.ready; }
   else proc = procFace('blank' + face.p);
  } else proc = procFace(face.c);
  if (proc) map = proc.map;
  const vinyl = proc?.vinyl;
  const m = new THREE.MeshStandardMaterial({
   map, color: vinyl ? '#ffffff' : '#fffdf8', roughness: vinyl ? 0.62 : 0.9, metalness: 0,
   bumpMap: vinyl ? vinylBump : fibre, bumpScale: vinyl ? 0.6 : 0.35,
  });
  if (proc?.rough) { m.roughnessMap = proc.rough; m.metalnessMap = proc.metal; m.metalness = 1; m.roughness = 1; }
  m.userData = {face, ready};
  if (!vinyl) {
   m.onBeforeCompile = (sh) => {
    sh.uniforms.uFlip = {value: flip ? 1 : 0};
    sh.uniforms.uAge = ageU;
    sh.fragmentShader = sh.fragmentShader
     .replace('#include <common>', '#include <common>\nuniform float uFlip; uniform float uAge;')
     .replace('#include <map_fragment>', `#include <map_fragment>
      { float gu = mix(vMapUv.x, 1.0 - vMapUv.x, uFlip);
        float edge = min(min(gu, 1.0 - gu) * 1.3, min(vMapUv.y, 1.0 - vMapUv.y));
        diffuseColor.rgb = max(diffuseColor.rgb, vec3(0.085, 0.074, 0.062));
        diffuseColor.rgb *= mix(0.8, 1.0, smoothstep(0.0, 0.16, gu));
        vec3 aged = diffuseColor.rgb * vec3(1.0, 0.955, 0.86);
        aged *= mix(0.86, 1.0, smoothstep(0.0, 0.06, edge));
        diffuseColor.rgb = mix(diffuseColor.rgb, aged, uAge); }`);
   };
   m.customProgramCacheKey = () => 'page' + (flip ? 1 : 0);
  }
  return m;
 };
 const edgeMat = {
  paper: new THREE.MeshStandardMaterial({color: '#ece5d4', roughness: .95}),
  card: new THREE.MeshStandardMaterial({color: '#e6dfcf', roughness: .9}),
  board: new THREE.MeshStandardMaterial({color: '#111112', roughness: .55, bumpMap: vinylBump, bumpScale: .4}),
 };
 const blockMat = new THREE.MeshStandardMaterial({map: edgeTex, color: '#fffaf0', roughness: .95});
 const blockTop = new THREE.MeshStandardMaterial({color: '#f4efe2', roughness: .95});

 // ---------- the book ----------
 let leaves = [], N = 0, hL = [], hR = [], cur = 0;  // cur: leaves turned to the left
 const restCache = new Map();
 const solveA = (h, g) => {                         // angle amplitude that rises h over arc g
  let lo = 0, hi = Math.PI / 2;
  const rise = A => { let z = 0; const n = 24; for (let i = 0; i < n; i++) z += Math.sin(A * Math.sin(Math.PI * (i + .5) / n)) * g / n; return z; };
  if (rise(hi) <= h) return hi;
  for (let k = 0; k < 30; k++) { const m = (lo + hi) / 2; if (rise(m) < h) lo = m; else hi = m; }
  return (lo + hi) / 2;
 };
 const rest = (i, side) => {
  const k = i + side; if (restCache.has(k)) return restCache.get(k);
  const l = leaves[i], h = (side === 'R' ? hR[i] : hL[i]) + l.t / 2;
  const g = Math.max(G[l.kind], h * 1.75), A = solveA(h, g);
  const r = {A, g}; restCache.set(k, r); return r;
 };
 const buildLeaves = () => {
  const count = manifest?.count || 160, last = count;
  const L = [];
  const copy = prefs.edition === 'copy';
  L.push(copy ? {kind: 'card', front: {p: 1}, back: {c: 'cardInside'}} : {kind: 'board', front: {c: 'vinylFront'}, back: {c: 'vinylInside'}});
  for (let n = 2; n + 1 < last; n += 2) L.push({kind: !copy && n === 2 ? 'card' : 'paper', front: {p: n}, back: {p: n + 1}});
  L.push(copy ? {kind: 'card', front: {c: 'cardInside'}, back: {p: last}} : {kind: 'board', front: {c: 'vinylInside'}, back: {c: 'vinylBack'}});
  L.forEach(l => { l.t = T[l.kind]; l.pos = 0; l.anim = null; l.bend = 0; l.twist = 0; l.vg = .5; l.peek = 0; l.peekTo = 0; });
  leaves = L; N = L.length;
  hL = []; hR = [];
  let s = 0; for (let i = 0; i < N; i++) { hL[i] = s; s += L[i].t; }
  s = 0; for (let i = N - 1; i >= 0; i--) { hR[i] = s; s += L[i].t; }
  restCache.clear();
  range.max = N;
 };
 // Which pages are showing for a state.
 const spreadPages = (s) => {
  const l = s > 0 ? leaves[s - 1].back : null, r = s < N ? leaves[s].front : null;
  return [l?.p || null, r?.p || null];
 };
 const stateForPage = (n) => {
  for (let i = 0; i < N; i++) { if (leaves[i].front.p === n) return i; if (leaves[i].back.p === n) return i + 1; }
  return n <= 1 ? 0 : n >= (manifest?.count || 160) ? N : clamp(Math.floor(n / 2), 0, N);
 };

 // Centreline of leaf i at turn position t (0 right .. 1 left).
 const curve = (i, t, bend, twist, vg, out) => {
  const l = leaves[i], R = rest(i, 'R'), Lf = rest(i, 'L'), du = W / SU, s = Math.sin(Math.PI * t);
  const rigid = l.kind === 'board' ? 0 : l.kind === 'card' ? .45 : 1;
  for (let r = 0; r <= SV; r++) {
   const v = r / SV; let x = 0, z = 0;
   for (let c = 0; c <= SU; c++) {
    const o = (r * (SU + 1) + c) * 3;
    out[o] = x; out[o + 1] = (v - .5) * H; out[o + 2] = z;
    if (c === SU) break;
    const u = (c + .5) * du;
    const aR = u < R.g ? R.A * Math.sin(Math.PI * u / R.g) : 0;
    const aL = Math.PI - (u < Lf.g ? Lf.A * Math.sin(Math.PI * u / Lf.g) : 0);
    const f = Math.pow(u / W, 1.6) * rigid;
    const a = clamp(aR + (aL - aR) * t + (bend + twist * (v - vg)) * s * f, 0, Math.PI);
    x += Math.cos(a) * du; z += Math.sin(a) * du;
   }
  }
 };

 // A leaf as a slab: front, back and edges, rebuilt from its centreline.
 const NV = (SU + 1) * (SV + 1);
 const centre = new Float32Array(NV * 3), nrm = new Float32Array(NV * 3);
 const makeLeafGeometry = () => {
  const edgeVerts = 2 * (2 * (SU + 1) + 2 * (SV + 1));
  const g = new THREE.BufferGeometry();
  const total = NV * 2 + edgeVerts;
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(total * 3), 3));
  g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(total * 3), 3));
  const uv = new Float32Array(total * 2);
  for (let r = 0; r <= SV; r++) for (let c = 0; c <= SU; c++) { const k = r * (SU + 1) + c; uv[k * 2] = c / SU; uv[k * 2 + 1] = r / SV; uv[(NV + k) * 2] = 1 - c / SU; uv[(NV + k) * 2 + 1] = r / SV; }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  const idx = [], at = (r, c) => r * (SU + 1) + c;
  for (let r = 0; r < SV; r++) for (let c = 0; c < SU; c++) { const a = at(r, c), b = at(r, c + 1), d = at(r + 1, c), e = at(r + 1, c + 1); idx.push(a, b, d, b, e, d); }
  const nf = idx.length;
  for (let r = 0; r < SV; r++) for (let c = 0; c < SU; c++) { const a = NV + at(r, c), b = NV + at(r, c + 1), d = NV + at(r + 1, c), e = NV + at(r + 1, c + 1); idx.push(a, d, b, b, d, e); }
  const nb = idx.length - nf;
  // edges: strips of (front, back) vertex pairs
  let base = NV * 2; const strips = [];
  const strip = (list, flip) => { const s0 = base; strips.push({s0, list}); for (let k = 0; k < list.length - 1; k++) { const a = s0 + k * 2, b = a + 1, c2 = a + 2, d = a + 3; if (flip) idx.push(a, c2, b, b, c2, d); else idx.push(a, b, c2, b, d, c2); } base += list.length * 2; };
  strip([...Array(SV + 1)].map((_, r) => at(r, SU)), false);           // fore-edge
  strip([...Array(SV + 1)].map((_, r) => at(r, 0)), true);             // spine edge
  strip([...Array(SU + 1)].map((_, c) => at(SV, c)), false);           // head
  strip([...Array(SU + 1)].map((_, c) => at(0, c)), true);             // tail
  g.setIndex(idx);
  g.addGroup(0, nf, 0); g.addGroup(nf, nb, 1); g.addGroup(nf + nb, idx.length - nf - nb, 2);
  g.userData.strips = strips;
  return g;
 };
 const shapeLeaf = (g, i, t, bend, twist, vg) => {
  curve(i, t, bend, twist, vg, centre);
  const P = centre, at = (r, c) => (r * (SU + 1) + c) * 3;
  for (let r = 0; r <= SV; r++) for (let c = 0; c <= SU; c++) {
   const o = at(r, c), c0 = at(r, Math.max(0, c - 1)), c1 = at(r, Math.min(SU, c + 1)), r0 = at(Math.max(0, r - 1), c), r1 = at(Math.min(SV, r + 1), c);
   const ux = P[c1] - P[c0], uy = P[c1 + 1] - P[c0 + 1], uz = P[c1 + 2] - P[c0 + 2];
   const vx = P[r1] - P[r0], vy = P[r1 + 1] - P[r0 + 1], vz = P[r1 + 2] - P[r0 + 2];
   let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; const L = Math.hypot(nx, ny, nz) || 1;
   nrm[o] = nx / L; nrm[o + 1] = ny / L; nrm[o + 2] = nz / L;
  }
  const pos = g.attributes.position.array, nor = g.attributes.normal.array, h = leaves[i].t / 2;
  for (let k = 0; k < NV; k++) {
   const o = k * 3, b = (NV + k) * 3;
   pos[o] = P[o] + nrm[o] * h; pos[o + 1] = P[o + 1] + nrm[o + 1] * h; pos[o + 2] = P[o + 2] + nrm[o + 2] * h;
   pos[b] = P[o] - nrm[o] * h; pos[b + 1] = P[o + 1] - nrm[o + 1] * h; pos[b + 2] = P[o + 2] - nrm[o + 2] * h;
   nor[o] = nrm[o]; nor[o + 1] = nrm[o + 1]; nor[o + 2] = nrm[o + 2];
   nor[b] = -nrm[o]; nor[b + 1] = -nrm[o + 1]; nor[b + 2] = -nrm[o + 2];
  }
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  g.userData.strips.forEach(({s0, list}, si) => list.forEach((k, j) => {
   const a = (s0 + j * 2) * 3, b = a + 3;
   for (let q = 0; q < 3; q++) { pos[a + q] = pos[k * 3 + q]; pos[b + q] = pos[(NV + k) * 3 + q]; }
   // edge normal: along the page surface, away from the leaf
   const k2 = si < 2 ? k + (si === 0 ? -1 : 1) : k + (si === 2 ? -(SU + 1) : (SU + 1));
   let ex = P[k * 3] - P[k2 * 3], ey = P[k * 3 + 1] - P[k2 * 3 + 1], ez = P[k * 3 + 2] - P[k2 * 3 + 2]; const L = Math.hypot(ex, ey, ez) || 1;
   nor[a] = nor[b] = ex / L; nor[a + 1] = nor[b + 1] = ey / L; nor[a + 2] = nor[b + 2] = ez / L;
  }));
  g.attributes.position.needsUpdate = true; g.attributes.normal.needsUpdate = true;
  g.computeBoundingSphere();
 };

 const meshes = new Map();   // leaf index -> mesh
 const leafMesh = (i) => {
  let m = meshes.get(i);
  if (m) return m;
  const l = leaves[i];
  m = new THREE.Mesh(makeLeafGeometry(), [pageMaterial(l.front, false), pageMaterial(l.back, true), edgeMat[l.kind]]);
  m.castShadow = m.receiveShadow = true;
  m.userData.key = '';
  if (l.kind === 'board') m.scale.set((W + .014) / W, (H + .02) / H, 1);   // boards overhang the leaves
  book.add(m); meshes.set(i, m);
  return m;
 };
 const dropMesh = (i) => { const m = meshes.get(i); if (!m) return; book.remove(m); m.geometry.dispose(); m.material[0].dispose(); m.material[1].dispose(); meshes.delete(i); };

 // Page blocks: every leaf not drawn individually, as one solid per side.
 const blocks = {L: null, R: null};
 const setBlock = (side, from, to) => {
  const old = blocks[side];
  const sig = from + ':' + to;
  if (old && old.userData.sig === sig) return;
  if (old) { book.remove(old); old.geometry.dispose(); blocks[side] = null; }
  if (to < from) return;
  const top = side === 'R' ? from : to, bot = side === 'R' ? to : from;
  const prof = (i, off) => { curve(i, side === 'R' ? 0 : 1, 0, 0, .5, centre); const xs = [], zs = []; for (let c = 0; c <= SU; c++) { xs.push(centre[c * 3]); zs.push(centre[c * 3 + 2] + off); } return {xs, zs}; };
  const pt = prof(top, leaves[top].t / 2), pb = prof(bot, -leaves[bot].t / 2);
  const pos = [], uv = [], idx = [], groups = [];
  const quad = (a, b, c, d, ua, ub, uc, ud) => { const n = pos.length / 3; pos.push(...a, ...b, ...c, ...d); uv.push(...ua, ...ub, ...uc, ...ud); idx.push(n, n + 1, n + 2, n + 1, n + 3, n + 2); };
  const sv = z => z / T.paper / 64;          // one stripe per leaf
  const y0 = -H / 2, y1 = H / 2, e = SU;
  // fore-edge
  quad([pb.xs[e], y0, pb.zs[e]], [pt.xs[e], y0, pt.zs[e]], [pb.xs[e], y1, pb.zs[e]], [pt.xs[e], y1, pt.zs[e]], [0, sv(pb.zs[e])], [0, sv(pt.zs[e])], [1, sv(pb.zs[e])], [1, sv(pt.zs[e])]);
  // head and tail
  for (let c = 0; c < SU; c++) {
   for (const [y, flip] of [[y1, side === 'R'], [y0, side !== 'R']]) {
    const a = [pb.xs[c], y, pb.zs[c]], b = [pb.xs[c + 1], y, pb.zs[c + 1]], cc = [pt.xs[c], y, pt.zs[c]], d = [pt.xs[c + 1], y, pt.zs[c + 1]];
    if (flip) quad(a, b, cc, d, [c / SU, sv(pb.zs[c])], [(c + 1) / SU, sv(pb.zs[c + 1])], [c / SU, sv(pt.zs[c])], [(c + 1) / SU, sv(pt.zs[c + 1])]);
    else quad(b, a, d, cc, [(c + 1) / SU, sv(pb.zs[c + 1])], [c / SU, sv(pb.zs[c])], [(c + 1) / SU, sv(pt.zs[c + 1])], [c / SU, sv(pt.zs[c])]);
   }
  }
  groups.push(idx.length);
  // top surface (mostly hidden; it shows in the gutter during a turn)
  for (let c = 0; c < SU; c++) {
   const a = [pt.xs[c], y0, pt.zs[c]], b = [pt.xs[c + 1], y0, pt.zs[c + 1]], cc = [pt.xs[c], y1, pt.zs[c]], d = [pt.xs[c + 1], y1, pt.zs[c + 1]];
   if (side === 'R') quad(a, b, cc, d, [0, 0], [0, 0], [0, 0], [0, 0]); else quad(b, a, d, cc, [0, 0], [0, 0], [0, 0], [0, 0]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  g.addGroup(0, groups[0], 0); g.addGroup(groups[0], idx.length - groups[0], 1);
  const m = new THREE.Mesh(g, [blockMat, blockTop]);
  m.castShadow = m.receiveShadow = true; m.userData.sig = sig;
  book.add(m); blocks[side] = m;
 };

 // The desk: dark walnut under a warm lamp.
 const desk = new THREE.Mesh(new THREE.PlaneGeometry(9, 6), new THREE.MeshStandardMaterial({
  map: canvasTex(1024, 1024, (g, w, h) => {
   g.fillStyle = '#3a2416'; g.fillRect(0, 0, w, h);
   for (let y = 0; y < h; y++) { const k = Math.sin(y * .045 + Math.sin(y * .011) * 3) * .5 + .5; const v = 16 + k * 22 + Math.random() * 6; g.fillStyle = `rgba(${v + 30},${v + 12},${v},.55)`; g.fillRect(0, y, w, 1); }
   g.globalAlpha = .18; for (let i = 0; i < 160; i++) { g.strokeStyle = Math.random() < .5 ? '#140b06' : '#5a3a24'; g.lineWidth = Math.random() * 2; g.beginPath(); const y = Math.random() * h; g.moveTo(0, y); for (let x = 0; x <= w; x += 32) g.lineTo(x, y + Math.sin(x * .01 + i) * 6); g.stroke(); }
  }), roughness: .55, metalness: 0,
 }));
 desk.material.map.wrapS = desk.material.map.wrapT = THREE.RepeatWrapping; desk.material.map.repeat.set(2, 1);
 desk.material.map.rotation = Math.PI / 2;
 desk.position.z = -0.0006; desk.receiveShadow = true;
 scene.add(desk);

 // ---------- state and animation ----------
 let dirty = true, raf = 0, drag = null, single = false, focus = 'right', camX = 0;
 const sound = (() => {
  let ctx = null, buf = null;
  const play = (kind) => {
   if (!prefs.sound || reduceMQ.matches || !ctx) return;
   try {
    if (kind === 'settle') {
     const src = ctx.createBufferSource(); src.buffer = buf; const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 900;
     const g = ctx.createGain(), t0 = ctx.currentTime; g.gain.setValueAtTime(.09, t0); g.gain.exponentialRampToValueAtTime(.001, t0 + .09);
     src.connect(lp).connect(g).connect(ctx.destination); src.start(t0, .2); src.stop(t0 + .1); return;
    }
    const src = ctx.createBufferSource(); src.buffer = buf;
    const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = .7;
    const g = ctx.createGain(), t0 = ctx.currentTime, len = kind === 'board' ? .22 : .42;
    bp.frequency.setValueAtTime(kind === 'board' ? 500 : 2600, t0); bp.frequency.exponentialRampToValueAtTime(kind === 'board' ? 180 : 900, t0 + len);
    g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(kind === 'board' ? .5 : .16, t0 + .03); g.gain.exponentialRampToValueAtTime(.001, t0 + len);
    src.connect(bp).connect(g).connect(ctx.destination); src.start(t0, Math.random() * .1); src.stop(t0 + len + .05);
   } catch {}
  };
  play.unlock = () => {
   if (!prefs.sound) return;
   try {
    ctx ??= new AudioContext();
    if (ctx.state === 'suspended') ctx.resume();
    if (!buf) { buf = ctx.createBuffer(1, ctx.sampleRate * .6, ctx.sampleRate); const d = buf.getChannelData(0); let b = 0; for (let i = 0; i < d.length; i++) { b = .82 * b + .18 * (Math.random() * 2 - 1); d[i] = b; } }
   } catch {}
  };
  play.close = () => { try { ctx?.close(); } catch {} };
  return play;
 })();
 const bendProfile = p => .65 * Math.sin(Math.PI * p) * (1 - p) - .15 * Math.sin(Math.PI * p) * p;
 const animate = (i, to, dur, delay = 0) => {
  const l = leaves[i];
  if (reduceMQ.matches || dur <= 0) { l.pos = to; l.anim = null; l.bend = l.twist = 0; dirty = true; return; }
  l.anim = {from: l.pos, to, start: performance.now() + delay, dur, dir: to > l.pos ? 1 : -1, twist0: l.twist, bend0: l.bend, played: false};
  dirty = true;
 };
 const busyLeaf = () => leaves.some(l => l.anim);
 const settledState = () => { let s = 0; while (s < N && leaves[s].pos >= 1 && !leaves[s].anim) s++; return s; };
 // Target state, which the controls show at once even while leaves are still moving.
 let target = 0;

 const goTo = (s, opts = {}) => {
  s = clamp(s, 0, N);
  if (drag) return;
  clearPeek(); unzoom();
  const from = target; target = s;
  if (s === from) { syncUI(); return; }
  const fwd = s > from, span = Math.abs(s - from);
  const animN = Math.min(span, opts.instant ? 0 : span > 1 ? 7 : 1);
  const list = fwd ? [...Array(span)].map((_, k) => from + k) : [...Array(span)].map((_, k) => from - 1 - k);
  // the far leaves snap; the last few nearest the destination turn visibly
  const snap = list.slice(0, span - animN), anim = list.slice(span - animN);
  snap.forEach(i => { leaves[i].pos = fwd ? 1 : 0; leaves[i].anim = null; });
  const dur = span > 1 ? 620 : 980, gap = span > 1 ? 85 : 0;
  anim.forEach((i, k) => animate(i, fwd ? 1 : 0, dur, k * gap));
  if (single) focus = fwd ? (s >= N ? 'left' : s === 0 ? 'right' : 'left') : (s === 0 ? 'right' : 'right');
  syncUI(true);
 };
 const next = () => {
  unzoom();
  if (single && focus === 'left' && target < N && target > 0) { focus = 'right'; dirty = true; syncUI(true); return; }
  goTo(target + 1);
 };
 const prev = () => {
  unzoom();
  if (single && focus === 'right' && target > 0 && target < N) { focus = 'left'; dirty = true; syncUI(true); return; }
  if (target === 0) return;
  goTo(target - 1);
  if (single) focus = target === 0 ? 'right' : 'right';
 };
 // Fetch the destination pages first, so a long jump lands on printed pages.
 let jumpSeq = 0;
 const whenReady = (s, fn0) => {
  const seq = ++jumpSeq, fn = () => { if (seq === jumpSeq) fn0(); };
  if (!manifest || Math.abs(s - target) < 2) return fn();
  const need = [s - 1, s].filter(i => i >= 0 && i < N).flatMap(i => [leaves[i].front.p, leaves[i].back.p]).filter(Boolean).map(pageTex);
  const t0 = performance.now();
  const wait = () => { if (!alive) return; if (need.every(e => e.ready || e.failed) || performance.now() - t0 > 700) fn(); else setTimeout(wait, 40); };
  wait();
 };
 const jumpToPage = (n) => {
  const s = stateForPage(n);
  whenReady(s, () => jumpTo(n, s));
 };
 const jumpTo = (n, s) => {
  goTo(s);
  if (single) { const [l, r] = spreadPages(s); focus = r === n || !l ? 'right' : 'left'; if (s === N) focus = 'left'; }
  syncUI(true);
 };

 // ---------- camera ----------
 const fit = () => {
  const w = stage.clientWidth, h = stage.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  single = w / h < 0.95;
  camera.updateProjectionMatrix();
  dirty = true;
 };
 const camTarget = () => {
  const p0 = leaves[0] ? leaves[0].pos : 0, pN = leaves[N - 1] ? leaves[N - 1].pos : 0;
  const off = -W / 2 * (1 - p0) + W / 2 * pN;
  book.position.x = off;
  if (!single) return {x: 0, w: (p0 < 1 || pN > 0) ? W * 1.32 + .1 : 2 * W + .14, h: H + .14};
  const fx = target === 0 ? 0 : target === N ? 0 : focus === 'right' ? off + W / 2 : off - W / 2;
  return {x: fx, w: W + .05, h: H + .06};
 };
 // In-place zoom: the camera moves in toward a point on the page; it tilts flatter as it nears.
 const ZMAX = 4.5;
 let zoom = 1, zCur = 1, zx = 0, zy = 0, camY = 0;
 const placeCamera = (snap) => {
  const t = camTarget();
  const fov = THREE.MathUtils.degToRad(camera.fov), tan = Math.tan(fov / 2);
  const dist = Math.max(t.h / 2 / tan, t.w / 2 / (tan * camera.aspect)) * 1.02;
  const now = snap || reduceMQ.matches;
  if (zoom <= 1.001) { zx = t.x; zy = 0; }
  else { const off = book.position.x; zx = clamp(zx, off - W - .03, off + W + .03); zy = clamp(zy, -H / 2, H / 2); }
  const k = now ? 1 : .16;
  zCur += (zoom - zCur) * k; camX += (zx - camX) * k; camY += (zy - camY) * k;
  if (Math.abs(zCur - zoom) > 1e-4 || Math.abs(camX - zx) > 1e-5 || Math.abs(camY - zy) > 1e-5) dirty = true;
  const prevD = camera.userData.d ?? dist;
  const d = now ? dist : prevD + (dist - prevD) * .14;
  if (Math.abs(d - dist) > 1e-4) dirty = true;
  camera.userData.d = d;
  const tilt = THREE.MathUtils.degToRad(single ? 6 : 16) / zCur, dd = d / zCur;
  camera.position.set(camX, camY - Math.sin(tilt) * dd, Math.cos(tilt) * dd + .02);
  camera.up.set(0, 1, 0);
  camera.lookAt(camX, camY, .02);
 };
 const worldAt = (x, y) => {
  const r = renderer.domElement.getBoundingClientRect();
  ndc.set((x - r.left) / r.width * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  return ray.ray.intersectPlane(plane, hit) ? {x: hit.x, y: hit.y} : null;
 };
 const syncZoomUI = () => {
  $('#bk-zval').textContent = `${Math.round(zoom * 100)}%`;
  $('#bk-zin').disabled = zoom >= ZMAX - .01; $('#bk-zout').disabled = zoom <= 1;
  const z = zoom > 1.02;
  stage.classList.toggle('zoomed', z); $('#bk-zhint').hidden = !z;
  stage.style.touchAction = z ? 'none' : '';
 };
 const setZoomTo = (z, P) => {
  z = clamp(z, 1, ZMAX); if (z < 1.02) z = 1;
  const C = zoom > 1.001 ? {x: zx, y: zy} : {x: camTarget().x, y: 0};
  if (P && z > 1) { const k = zoom / z; zx = P.x + (C.x - P.x) * k; zy = P.y + (C.y - P.y) * k; } else { zx = C.x; zy = C.y; }
  const was = wantHi(); zoom = z;
  if (wantHi() !== was) refreshHi();
  clearPeek(); syncZoomUI(); dirty = true;
 };
 const zoomAt = (f, x, y) => setZoomTo(zoom * f, x == null ? null : worldAt(x, y));
 const panBy = (x0, y0, x1, y1) => { const a = worldAt(x0, y0), b = worldAt(x1, y1); if (!a || !b) return; zx -= b.x - a.x; zy -= b.y - a.y; dirty = true; };
 const unzoom = () => { if (zoom > 1) setZoomTo(1); };

 // ---------- per-frame update ----------
 const update = (now) => {
  for (let i = 0; i < N; i++) {
   const l = leaves[i], a = l.anim;
   if (a) {
    if (now < a.start) continue;
    const p = clamp((now - a.start) / a.dur, 0, 1);
    if (!a.played && p > 0) { a.played = true; sound(l.kind === 'board' ? 'board' : 'leaf'); }
    l.pos = a.from + (a.to - a.from) * ease(p);
    l.bend = a.dir * bendProfile(p) + a.bend0 * (1 - p);
    l.twist = a.twist0 * (1 - ease(p));
    if (p >= 1) { l.pos = a.to; l.anim = null; l.bend = l.twist = 0; if (l.kind !== 'board') sound('settle'); }
    dirty = true;
   }
   if (Math.abs(l.peek - l.peekTo) > 1e-4) { l.peek += (l.peekTo - l.peek) * .2; dirty = true; } else l.peek = l.peekTo;
  }
  // visible leaves
  let rightTop = N, leftTop = -1;
  for (let i = 0; i < N; i++) if (leaves[i].pos <= 0 && !leaves[i].anim) { rightTop = i; break; }
  for (let i = N - 1; i >= 0; i--) if (leaves[i].pos >= 1 && !leaves[i].anim) { leftTop = i; break; }
  const vis = new Set([0, N - 1]);
  for (let i = 0; i < N; i++) { const l = leaves[i]; if ((l.pos > 0 && l.pos < 1) || l.anim) vis.add(i); }
  [rightTop, rightTop + 1, leftTop, leftTop - 1].forEach(i => { if (i >= 0 && i < N) vis.add(i); });
  for (const i of [...meshes.keys()]) if (!vis.has(i)) dropMesh(i);
  for (const i of vis) {
   const l = leaves[i], m = leafMesh(i);
   const p = clamp(l.pos + (l.pos >= 1 ? -l.peek : l.peek), 0, 1);
   const k = `${p.toFixed(5)}|${l.bend.toFixed(4)}|${l.twist.toFixed(4)}|${l.vg.toFixed(3)}`;
   if (m.userData.key !== k) { shapeLeaf(m.geometry, i, p, l.bend + (l.peek ? .5 * (l.pos >= 1 ? -1 : 1) : 0), l.twist, l.vg); m.userData.key = k; }
   // swap in a page image once it arrives
   m.material.forEach((mat, j) => {
    const n = j < 2 && manifest && mat.userData.face?.p; if (!n) return;
    const hi = hiRes.get(n), lo = pageTex(n);
    const want = hi?.ready ? hi.tex : lo.ready ? lo.tex : null;
    if (want && mat.map !== want) { mat.map = want; mat.userData.ready = true; dirty = true; }
   });
  }
  setBlock('R', Math.max(rightTop + 2, 1), N - 2);
  setBlock('L', 1, Math.min(leftTop - 2, N - 2));
  placeCamera(false);
 };
 const loop = (now) => {
  if (!alive) return;
  raf = requestAnimationFrame(loop);
  update(now);
  if (dirty) { dirty = false; renderer.render(scene, camera); }
  if (!busyLeaf() && !drag && cur !== settledState()) { cur = settledState(); prune(); preload(); refreshHi(); }
 };
 const preload = () => {
  if (!manifest) return;
  for (let i = Math.max(0, target - 3); i <= Math.min(N - 1, target + 3); i++) { const l = leaves[i]; if (l.front.p) pageTex(l.front.p); if (l.back.p) pageTex(l.back.p); }
 };

 // ---------- UI sync ----------
 const label = (s) => {
  const [l, r] = spreadPages(s);
  if (s === 0) return prefs.edition === 'copy' ? 'Front cover' : 'Binder, closed';
  if (s === N) return prefs.edition === 'copy' ? 'Back cover' : 'Binder, closed (back)';
  const shown = single ? (focus === 'right' ? r : l) : null;
  const pages = single ? (shown ? `Page ${shown}` : 'Inside cover') : [l, r].filter(Boolean).length ? `Pages ${[l, r].filter(Boolean).join('–')}` : 'Inside cover';
  const e = titleFor(shown || r || l || 0);
  return `${pages}${e ? ' · ' + e.t : ''}`;
 };
 let lastAnnounce = '';
 const syncUI = (announce) => {
  range.value = target;
  const txt = label(target);
  where.textContent = txt;
  range.setAttribute('aria-valuetext', txt);
  $('#bk-prev').disabled = target === 0 && !(single && focus === 'right' && false);
  $('#bk-next').disabled = target === N;
  $('#bk-zoom-btn').disabled = !manifest || !currentPages().length;
  const here = new Set(spreadPages(target).filter(Boolean).map(n => titleFor(n)?.n));
  main.querySelectorAll('.bk-toc button[data-page]').forEach(b => { const on = here.has(+b.dataset.page); b.classList.toggle('here', on); if (on) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current'); });
  if (announce && txt !== lastAnnounce) { live.textContent = txt; lastAnnounce = txt; }
  const n = (single ? (focus === 'right' ? spreadPages(target)[1] : spreadPages(target)[0]) : null) || spreadPages(target)[0] || spreadPages(target)[1];
  const h = n ? `#/book/${n}` : '#/book';
  if (location.hash !== h) history.replaceState(null, '', h);
  dirty = true;
 };
 const currentPages = () => { const [l, r] = spreadPages(target); return single ? [focus === 'right' ? r : l].filter(Boolean) : [l, r].filter(Boolean); };

 // ---------- pointer: tap, drag to curl, hover peek ----------
 const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), -0.03), hit = new THREE.Vector3();
 const toBook = (e) => {
  const r = renderer.domElement.getBoundingClientRect();
  ndc.set((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  if (!ray.ray.intersectPlane(plane, hit)) return null;
  return {x: hit.x - book.position.x, y: hit.y};
 };
 const clearPeek = () => leaves.forEach(l => { l.peekTo = 0; });
 const el = renderer.domElement;
 const touches = new Map(); let tpinch = null;
 const pinchState = () => { const [a, b] = [...touches.values()]; return {d: Math.hypot(a.x - b.x, a.y - b.y) || 1, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2}; };
 el.addEventListener('pointerdown', (e) => {
  touches.set(e.pointerId, {x: e.clientX, y: e.clientY});
  if (touches.size === 2) { if (drag && !drag.active) drag = null; if (!drag) { tpinch = pinchState(); clearTimeout(tapT); } return; }
  if (e.button !== 0 || drag || tpinch) return;
  sound.unlock();
  const p = toBook(e); if (!p) return;
  drag = {id: e.pointerId, x0: e.clientX, y0: e.clientY, lx: e.clientX, ly: e.clientY, p0: p, t0: performance.now(), active: false, leaf: -1, last: [], side: p.x >= 0 ? 'R' : 'L', spread: spreadPages(target), focus, zoomPan: zoom > 1.02};
  try { el.setPointerCapture(e.pointerId); } catch {}
 });
 el.addEventListener('pointermove', (e) => {
  if (touches.has(e.pointerId)) touches.set(e.pointerId, {x: e.clientX, y: e.clientY});
  if (tpinch && touches.size >= 2) {
   const q = pinchState();
   zoomAt(q.d / tpinch.d, q.mx, q.my); panBy(tpinch.mx, tpinch.my, q.mx, q.my);
   tpinch = q; return;
  }
  const p = toBook(e);
  if (!drag) {
   if (zoom > 1.02) { el.style.cursor = 'grab'; return; }
   if (e.pointerType !== 'mouse' || reduceMQ.matches || busyLeaf() || !p) return;
   clearPeek();
   const v = p.y / H + .5;
   if (Math.abs(p.y) < H / 2 && v >= 0 && v <= 1) {
    if (p.x > W - .13 && p.x < W + .02 && target < N) { leaves[target].peekTo = .045; leaves[target].vg = v; leaves[target].twist = (v - .5) * .5; }
    else if (p.x < -W + .13 && p.x > -W - .02 && target > 0) { leaves[target - 1].peekTo = .045; leaves[target - 1].vg = v; leaves[target - 1].twist = -(v - .5) * .5; }
   }
   el.style.cursor = p && Math.abs(p.x) < W && Math.abs(p.y) < H / 2 ? 'pointer' : '';
   return;
  }
  if (e.pointerId !== drag.id) return;
  const moved = Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0);
  if (drag.zoomPan) { panBy(drag.lx, drag.ly, e.clientX, e.clientY); drag.lx = e.clientX; drag.ly = e.clientY; if (moved > 5) drag.moved = true; el.style.cursor = 'grabbing'; return; }
  if (!drag.active && !drag.pan && moved > 8 && p) {
   if (busyLeaf()) return;
   if (single) {
    // On one-page view the swipe direction decides; a swipe toward the facing page just pans.
    const fwdSwipe = e.clientX < drag.x0;
    if ((fwdSwipe && focus === 'left' && target > 0 && target < N) || (!fwdSwipe && focus === 'right' && target > 0 && target < N)) { drag.pan = fwdSwipe ? 'next' : 'prev'; return; }
    drag.side = fwdSwipe ? 'R' : 'L';
   }
   const fwd = drag.side === 'R';
   const i = fwd ? target : target - 1;
   if (i < 0 || i >= N) { drag = null; return; }
   clearPeek(); leaves.forEach(l => { l.peek = 0; });
   drag.active = true; drag.leaf = i; drag.fwd = fwd;
   drag.u = clamp(Math.abs(drag.p0.x), W * .35, W);
   drag.vg = clamp(drag.p0.y / H + .5, 0, 1);
   sound(leaves[i].kind === 'board' ? 'board' : 'leaf');
  }
  if (drag.active && p) {
   const l = leaves[drag.leaf];
   const th = Math.acos(clamp(p.x / drag.u, -1, 1));       // free edge follows the finger
   l.pos = clamp(th / Math.PI, 0.002, 0.998);
   l.vg = drag.vg;
   l.bend = (drag.fwd ? 1 : -1) * .42;
   l.twist = (drag.fwd ? 1 : -1) * clamp((p.y / H + .5 - drag.vg) * 2.2 + (drag.vg - .5) * .9, -1.1, 1.1);
   drag.last.push([performance.now(), p.x]); if (drag.last.length > 6) drag.last.shift();
   dirty = true;
  }
 });
 let tapPrev = {t: 0, x: 0, y: 0};
 // A second tap or click on the same spot zooms in place there (or back out).
 const isDoubleTap = (e) => {
  const now = performance.now(), dbl = now - tapPrev.t < 320 && Math.hypot(e.clientX - tapPrev.x, e.clientY - tapPrev.y) < 32;
  tapPrev = dbl ? {t: 0, x: 0, y: 0} : {t: now, x: e.clientX, y: e.clientY};
  if (dbl) { clearTimeout(tapT); if (zoom > 1.05) setZoomTo(1); else zoomAt(2.5, e.clientX, e.clientY); }
  return dbl;
 };
 const endDrag = (e) => {
  if (touches.delete(e.pointerId) && touches.size < 2) tpinch = null;
  if (!drag || e.pointerId !== drag.id) return;
  const d = drag; drag = null;
  if (d.zoomPan) { el.style.cursor = 'grab'; if (!d.moved && e.type !== 'pointercancel') isDoubleTap(e); return; }
  if (d.pan) { if (e.type !== 'pointercancel') (d.pan === 'next' ? next : prev)(); return; }
  if (!d.active) {
   if (e.type === 'pointercancel') return;
   const p = toBook(e); if (!p) return;
   clearPeek();
   if (isDoubleTap(e)) return;
   const act = single ? ((e.clientX - el.getBoundingClientRect().left > el.clientWidth / 2) ? next : prev)
    : target === 0 ? next : target === N ? prev : (p.x >= 0 ? next : prev);
   // Turns wait a moment, so a double-click or double-tap can zoom instead.
   clearTimeout(tapT); tapT = setTimeout(act, 240);
   return;
  }
  const l = leaves[d.leaf];
  const [t0, x0] = d.last[0] || [0, 0], [t1, x1] = d.last[d.last.length - 1] || [1, 0];
  const vx = (x1 - x0) / Math.max(1, t1 - t0) * 1000;   // book units per second
  let done = d.fwd ? (l.pos > .5 || vx < -1.2) : (l.pos < .5 || vx > 1.2);
  if (d.fwd && vx > 1.2 && l.pos < .85) done = false;
  if (!d.fwd && vx < -1.2 && l.pos > .15) done = false;
  const to = done ? (d.fwd ? 1 : 0) : (d.fwd ? 0 : 1);
  l.anim = null;
  const rem = Math.abs(to - l.pos);
  l.anim = {from: l.pos, to, start: performance.now(), dur: reduceMQ.matches ? 1 : 260 + 520 * rem, dir: to > l.pos ? 1 : -1, twist0: l.twist, bend0: l.bend * .6, played: true};
  if (done) { target = d.fwd ? d.leaf + 1 : d.leaf; if (single) focus = target >= N ? 'left' : d.fwd ? 'left' : 'right'; }
  syncUI(true);
 };
 el.addEventListener('pointerup', endDrag);
 el.addEventListener('pointercancel', endDrag);
 el.addEventListener('pointerleave', () => { if (!drag) { clearPeek(); dirty = true; } });
 let tapT = 0;
 el.addEventListener('wheel', (e) => {
  e.preventDefault();
  const dy = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1);
  zoomAt(Math.exp(-dy * (e.ctrlKey ? .01 : .0017)), e.clientX, e.clientY);
 }, {passive: false});
 $('#bk-zin').onclick = () => zoomAt(1.5);
 $('#bk-zout').onclick = () => zoomAt(1 / 1.5);
 $('#bk-zreset').onclick = () => { setZoomTo(1); stage.focus({preventScroll: true}); };

 const onKey = (e) => {
  if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
  if (!loupe.hidden) return loupeKey(e);
  if (e.target.closest?.('input, select, textarea, .bk-toc') || (e.target.closest?.('button') && (e.key === ' ' || e.key === 'Enter'))) return;
  const k = e.key;
  // Outside the book only the arrows turn pages; Space, Page and Home/End keep scrolling the document.
  if (!e.target.closest?.('.bk') && !['ArrowLeft', 'ArrowRight'].includes(k)) return;
  sound.unlock();
  if (k === 'ArrowRight' || k === 'PageDown' || k === ' ') { e.preventDefault(); next(); }
  else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); prev(); }
  else if (k === 'Home') { e.preventDefault(); whenReady(0, () => goTo(0)); }
  else if (k === 'End') { e.preventDefault(); whenReady(N, () => goTo(N)); }
  else if (k === '+' || k === '=') { e.preventDefault(); zoomAt(1.4); }
  else if (k === '-' || k === '_') { e.preventDefault(); zoomAt(1 / 1.4); }
  else if (k === '0' || (k === 'Escape' && zoom > 1)) { e.preventDefault(); setZoomTo(1); }
  else if (zoom > 1.02 && (k === 'ArrowUp' || k === 'ArrowDown')) { e.preventDefault(); zy += (k === 'ArrowUp' ? .08 : -.08) / zoom; dirty = true; }
  else if (k === 'Enter' && manifest && e.target.closest?.('.bk-stage')) { e.preventDefault(); const n = currentPages().at(-1); if (n) openLoupe(n); }
 };
 document.addEventListener('keydown', onKey);

 // ---------- toolbar ----------
 $('#bk-prev').onclick = prev;
 $('#bk-next').onclick = next;
 let scrubT = 0;
 range.addEventListener('input', () => { clearTimeout(scrubT); const s = +range.value; where.textContent = label(s); scrubT = setTimeout(() => whenReady(s, () => goTo(s)), 120); });
 const toc = $('#bk-toc'), tocBtn = $('#bk-toc-btn');
 const setToc = (open) => { toc.hidden = !open; tocBtn.setAttribute('aria-expanded', String(open)); if (open) (toc.querySelector('button.here') || toc.querySelector('button[data-page]')).focus(); };
 tocBtn.onclick = () => setToc(toc.hidden);
 $('#bk-toc-close').onclick = () => { setToc(false); tocBtn.focus(); };
 toc.addEventListener('click', (e) => { const b = e.target.closest('button[data-page]'); if (!b) return; jumpToPage(+b.dataset.page); if (matchMedia('(max-width: 900px)').matches) setToc(false); stage.focus({preventScroll: true}); });
 toc.addEventListener('keydown', (e) => { if (e.key === 'Escape') { setToc(false); tocBtn.focus(); } });
 $('#bk-zoom-btn').onclick = () => { const n = currentPages().at(-1); if (n) openLoupe(n); };
 const setEdition = (ed) => {
  if (ed === prefs.edition) return;
  if (ed === 'copy' && !manifest) return;
  const keep = currentPages()[0] || spreadPages(target).find(Boolean);
  prefs.edition = ed; savePrefs();
  $('#bk-ed-binder').setAttribute('aria-pressed', String(ed === 'binder'));
  $('#bk-ed-copy').setAttribute('aria-pressed', String(ed === 'copy'));
  keepPage = keep; rebuild(keep ? stateForPageIn(keep) : target === 0 ? 0 : null); keepPage = null;
 };
 const stateForPageIn = (n) => { buildLeaves(); return stateForPage(n); };
 $('#bk-ed-binder').onclick = () => setEdition('binder');
 $('#bk-ed-copy').onclick = () => setEdition('copy');
 const ageBtn = $('#bk-age');
 const setAge = () => { ageBtn.setAttribute('aria-pressed', String(prefs.aged)); ageU.value = prefs.aged ? 1 : 0; dirty = true; };
 ageBtn.onclick = () => { prefs.aged = !prefs.aged; savePrefs(); setAge(); };
 const soundBtn = $('#bk-sound');
 soundBtn.onclick = () => { prefs.sound = !prefs.sound; savePrefs(); soundBtn.setAttribute('aria-pressed', String(prefs.sound)); };
 soundBtn.setAttribute('aria-pressed', String(prefs.sound));
 setAge();
 const full = $('#bk-full');
 full.onclick = () => { const s = main.querySelector('.bk'); if (document.fullscreenElement) document.exitFullscreen(); else s.requestFullscreen?.().catch(() => {}); };
 if (!document.fullscreenEnabled) full.hidden = true;

 // ---------- loupe ----------
 const loupe = $('#bk-loupe'), lview = $('#bk-loupe-view'), limg = $('#bk-loupe-img');
 let lz = {n: 0, s: 1, x: 0, y: 0, fit: 1}, lastFocus = null;
 const lApply = () => { limg.style.transform = `translate(${lz.x}px,${lz.y}px) scale(${lz.s})`; };
 const lFit = () => {
  const vw = lview.clientWidth, vh = lview.clientHeight, iw = manifest.lg[0], ih = manifest.lg[1];
  lz.fit = Math.min(vw / iw, vh / ih) * .96; lz.s = lz.fit; lz.x = (vw - iw * lz.s) / 2; lz.y = (vh - ih * lz.s) / 2; lApply();
 };
 const lZoom = (f, cx, cy) => {
  const r = lview.getBoundingClientRect(); cx ??= r.width / 2; cy ??= r.height / 2;
  const s = clamp(lz.s * f, lz.fit, lz.fit * 6); const k = s / lz.s;
  lz.x = cx - (cx - lz.x) * k; lz.y = cy - (cy - lz.y) * k; lz.s = s; lApply();
 };
 const lShow = (n) => {
  n = clamp(n, 1, manifest.count); lz.n = n;
  limg.src = `${BASE}lg/p${String(n).padStart(3, '0')}.webp`;
  limg.alt = `Scanned page ${n} of the manual${titleFor(n) ? ', ' + titleFor(n).t : ''}`;
  limg.width = manifest.lg[0]; limg.height = manifest.lg[1];
  $('#bk-l-label').textContent = `Page ${n}${titleFor(n) ? ' · ' + titleFor(n).t : ''}`;
  $('#bk-l-prev').disabled = n <= 1; $('#bk-l-next').disabled = n >= manifest.count;
  lFit();
 };
 function openLoupe(n) { lastFocus = document.activeElement; loupe.hidden = false; lShow(n); $('#bk-l-close').focus(); }
 const closeLoupe = () => { loupe.hidden = true; jumpToPage(lz.n); (lastFocus || stage).focus({preventScroll: true}); };
 $('#bk-l-close').onclick = closeLoupe;
 $('#bk-l-prev').onclick = () => lShow(lz.n - 1);
 $('#bk-l-next').onclick = () => lShow(lz.n + 1);
 $('#bk-l-in').onclick = () => lZoom(1.5);
 $('#bk-l-out').onclick = () => lZoom(1 / 1.5);
 $('#bk-l-fit').onclick = lFit;
 const lPan = (dx, dy) => { lz.x += dx; lz.y += dy; lApply(); };
 function loupeKey(e) {
  if (e.key === 'ArrowUp') { e.preventDefault(); lPan(0, 60); }
  else if (e.key === 'ArrowDown') { e.preventDefault(); lPan(0, -60); }
  else if (lz.s > lz.fit * 1.05 && (e.key === 'ArrowLeft' || e.key === 'ArrowRight') && e.shiftKey) { e.preventDefault(); lPan(e.key === 'ArrowLeft' ? 60 : -60, 0); }
  else if (e.key === 'Escape') { e.preventDefault(); closeLoupe(); }
  else if (e.key === 'ArrowRight') lShow(lz.n + 1);
  else if (e.key === 'ArrowLeft') lShow(lz.n - 1);
  else if (e.key === '+' || e.key === '=') lZoom(1.5);
  else if (e.key === '-') lZoom(1 / 1.5);
  else if (e.key === '0') lFit();
  else if (e.key === 'Tab') { const f = [...loupe.querySelectorAll('button:not([disabled])')]; const i = f.indexOf(document.activeElement); if (e.shiftKey && i <= 0) { e.preventDefault(); f.at(-1).focus(); } else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); } }
 }
 const onWinResize = () => { if (!loupe.hidden) lFit(); };
 window.addEventListener('resize', onWinResize);
 lview.addEventListener('wheel', (e) => { e.preventDefault(); const r = lview.getBoundingClientRect(); lZoom(Math.exp(-e.deltaY * .0022), e.clientX - r.left, e.clientY - r.top); }, {passive: false});
 const pts = new Map(); let pinch = null, lastTap = 0;
 lview.addEventListener('pointerdown', (e) => {
  lview.setPointerCapture(e.pointerId); pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
  if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch = {d: Math.hypot(a.x - b.x, a.y - b.y)}; }
  const now = performance.now(); if (pts.size === 1 && now - lastTap < 300) { const r = lview.getBoundingClientRect(); lz.s > lz.fit * 1.2 ? lFit() : lZoom(2.6, e.clientX - r.left, e.clientY - r.top); } lastTap = now;
 });
 lview.addEventListener('pointermove', (e) => {
  const p = pts.get(e.pointerId); if (!p) return;
  if (pts.size === 2 && pinch) {
   p.x = e.clientX; p.y = e.clientY; const [a, b] = [...pts.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y); const r = lview.getBoundingClientRect();
   lZoom(d / pinch.d, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top); pinch.d = d; return;
  }
  lz.x += e.clientX - p.x; lz.y += e.clientY - p.y; p.x = e.clientX; p.y = e.clientY; lApply();
 });
 const lUp = (e) => { pts.delete(e.pointerId); if (pts.size < 2) pinch = null; };
 lview.addEventListener('pointerup', lUp); lview.addEventListener('pointercancel', lUp);

 // ---------- boot ----------
 const ro = new ResizeObserver(() => { fit(); placeCamera(true); if (leaves.length) refreshHi(); });
 ro.observe(stage);
 const onMotion = () => { dirty = true; };
 reduceMQ.addEventListener('change', onMotion);
 let keepPage = null;
 const rebuild = (s) => {
  for (const i of [...meshes.keys()]) dropMesh(i);
  ['L', 'R'].forEach(k => { if (blocks[k]) { book.remove(blocks[k]); blocks[k].geometry.dispose(); blocks[k] = null; } });
  buildLeaves();
  s = s ?? 0;
  for (let i = 0; i < s; i++) leaves[i].pos = 1;
  target = s; cur = s;
  focus = s >= N ? 'left' : 'right';
  if (single && s > 0 && s < N && keepPage) { focus = spreadPages(s)[0] === keepPage ? 'left' : 'right'; }
  zoom = 1; syncZoomUI(); preload(); syncUI(false); fit(); placeCamera(true); refreshHi(); dirty = true;
 };
 let initialFocusLeft = false;
 Promise.all([
  fetch(BASE + 'manifest.json', {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).catch(() => null),
  document.fonts?.load('40px Michroma').catch(() => {}),
 ]).then(([m]) => {
  if (!alive) return;
  manifest = m && m.count ? m : null;
  if (!manifest) {
   prefs.edition = 'binder';
   $('#bk-ed-copy').disabled = true;
   $('#bk-ed-copy').title = 'Needs the owner’s scan on this computer';
   $('#bk-age').hidden = false;
   stage.insertAdjacentHTML('beforeend', `<div class="bk-note" role="note"><strong>The pages are not published here.</strong> The manual is a copyrighted book, so this public site shows the binder and blank, numbered sheets. On the owner’s computer the pages come from their own scan: run <code>python3 model-source/book/render-pages.py &lt;scan.pdf&gt;</code> and serve <code>dist/</code> locally.<button class="bk-btn" aria-label="Dismiss note">×</button></div>`);
   stage.querySelector('.bk-note button').onclick = (e) => e.target.parentElement.remove();
  }
  $('#bk-ed-binder').setAttribute('aria-pressed', String(prefs.edition === 'binder'));
  $('#bk-ed-copy').setAttribute('aria-pressed', String(prefs.edition === 'copy'));
  stage.querySelector('.bk-loading')?.remove();
  buildLeaves();
  let s = 0;
  if (Number.isFinite(initial) && initial > 0) { s = stateForPage(initial); initialFocusLeft = spreadPages(s)[0] === initial; }
  fit();
  keepPage = initialFocusLeft ? spreadPages(s)[0] : null; rebuild(s); keepPage = null;
  if (Number.isFinite(initial) && initial > 0 && single) focus = initialFocusLeft ? 'left' : 'right';
  initialFocusLeft = false;
  syncUI(false);
  raf = requestAnimationFrame(loop);
  if (phone) setTimeout(() => { if (alive && scrollY < 40) main.querySelector('.bk')?.scrollIntoView({block: 'start'}); }, 80);
 });

 return () => {
  alive = false; cancelAnimationFrame(raf); sound.close(); clearTimeout(tapT); window.removeEventListener('resize', onWinResize); document.removeEventListener('keydown', onKey); ro.disconnect(); clearTimeout(scrubT);
  reduceMQ.removeEventListener('change', onMotion);
  for (const i of [...meshes.keys()]) dropMesh(i);
  ['L', 'R'].forEach(k => blocks[k]?.geometry.dispose());
  pageCache.forEach(e => e.tex.dispose()); pageCache.clear(); hiRes.forEach(e => e.tex.dispose()); hiRes.clear();
  faceCache.forEach(f => { f.map?.dispose(); f.rough?.dispose(); f.metal?.dispose(); });
  [fibre, edgeTex, vinylBump, blankWhite, desk.material.map].forEach(t => t.dispose());
  desk.geometry.dispose(); desk.material.dispose();
  scene.environment?.dispose();
  renderer.dispose(); renderer.forceContextLoss?.();
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  main.classList.remove('book-route');
 };
}
