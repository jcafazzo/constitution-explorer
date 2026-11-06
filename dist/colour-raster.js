// Raster colour studies painted from the manual's own drawings (no vector redraw).
// Each *-map.png is produced by model-source/colour/segment.py from the scanned plate:
//   R = linework / edge weight, G = region class × 20, B/A = halftone flag (uniforms) or emblem alpha (flags).
// Painting happens on a <canvas>; colours come from the SF code palette passed in.
const V = 'r3';
const CLASS = ['paper', 'tunic', 'black', 'hose', 'badge', 'field', 'metal', 'device', 'braid'];
const cache = new Map();
function loadImage(src) {
  if (!cache.has(src)) cache.set(src, new Promise((ok, fail) => { const i = new Image(); i.onload = () => ok(i); i.onerror = fail; i.src = src; }));
  return cache.get(src);
}
async function loadMap(id) {
  const key = 'map:' + id;
  if (!cache.has(key)) cache.set(key, (async () => {
    const img = await loadImage(`assets/colours/${id}-map.png?v=${V}`);
    const c = new OffscreenCanvasOr(img.width, img.height), x = c.getContext('2d', {willReadFrequently: true});
    x.drawImage(img, 0, 0); return {w: img.width, h: img.height, data: x.getImageData(0, 0, img.width, img.height).data};
  })());
  return cache.get(key);
}
async function loadMeta(id) {
  const key = 'meta:' + id;
  if (!cache.has(key)) cache.set(key, fetch(`assets/colours/${id}-meta.json?v=${V}`).then(r => r.ok ? r.json() : null).catch(() => null));
  return cache.get(key);
}
function OffscreenCanvasOr(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const PAPER = [251, 250, 245], INK = [29, 28, 26], SHEEN = [143, 145, 148];

// Paint one map into an RGBA buffer. colours: {classname: '#rrggbb'}; flags use alpha, uniforms are opaque.
function paintMap(map, colours, {flag = false, metalShade = true} = {}) {
  const {w, h, data} = map, out = new ImageData(w, h), o = out.data;
  const col = CLASS.map(n => colours[n] ? hex(colours[n]) : null);
  for (let y = 0; y < h; y++) {
    const shade = metalShade ? 1.05 - .1 * (y / h) : 1;
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4, r = data[i] / 255, k = Math.round(data[i + 1] / 20);
      let c;
      if (flag) {
        const a = data[i + 2];
        if (!a) { o[i + 3] = 0; continue; }
        const field = col[5] || col[4] || PAPER, metal = col[6] || col[7] || INK;
        const fieldK = k === 5 || k === 4;
        c = fieldK ? mix(field, metal, r) : mix(field, metal, Math.max(r, .85));
        if (!fieldK && (k === 6)) c = c.map(v => v * shade);
        o[i] = c[0]; o[i + 1] = c[1]; o[i + 2] = c[2]; o[i + 3] = a; continue;
      }
      const base = (k === 4 && colours.tunic ? hex(colours.tunic) : col[k]) || PAPER;
      c = k === 2 ? mix(base, SHEEN, r * .8) : mix(base, INK, r);
      o[i] = c[0]; o[i + 1] = c[1]; o[i + 2] = c[2]; o[i + 3] = 255;
    }
  }
  if (flag) {                                   // darken metal at the emblem's outer edge so silver reads on light cards
    for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
      const i = (y * w + x) * 4; if (!o[i + 3]) continue;
      if (!o[i + 3 - 4] || !o[i + 3 + 4] || !o[i + 3 - 4 * w] || !o[i + 3 + 4 * w]) { o[i] *= .62; o[i + 1] *= .62; o[i + 2] *= .62; }
    }
  }
  return out;
}
function toCanvas(imgData) { const c = OffscreenCanvasOr(imgData.width, imgData.height); c.getContext('2d').putImageData(imgData, 0, 0); return c; }

// Braid stamp, coloured gold with the drawing's own rope linework.
async function braidCanvas(gold) {
  const m = await loadMapRGBA('braid-map'), {w, h, data} = m, out = new ImageData(w, h), o = out.data, g = hex(gold), dark = mix(g, INK, .78);
  for (let i = 0; i < data.length; i += 4) {
    const a = data[i + 3]; if (!a) continue; const c = mix(g, dark, data[i] / 255);
    o[i] = c[0]; o[i + 1] = c[1]; o[i + 2] = c[2]; o[i + 3] = a;
  }
  return toCanvas(out);
}
async function loadMapRGBA(id) {
  const key = 'rgba:' + id;
  if (!cache.has(key)) cache.set(key, (async () => {
    const img = await loadImage(`assets/colours/${id}.png?v=${V}`); const c = OffscreenCanvasOr(img.width, img.height), x = c.getContext('2d', {willReadFrequently: true});
    x.drawImage(img, 0, 0); return {w: img.width, h: img.height, data: x.getImageData(0, 0, img.width, img.height).data};
  })());
  return cache.get(key);
}

// Rank patterns: 1 = full stripe, 0 = broken stripe (PDF 65).
export const RANKS = {ensign: [], lieutenant: [1], 'lieutenant-commander': [1, 0], commander: [1, 1], captain: [1, 0, 1], commodore: [1, 1, 1], admiral: [1, 1, 1, 1]};

/** Paint a plate study into a canvas.
 *  spec: {id, kind: 'uniform'|'flag'|'badge', colours: {...}, division?: 'command'|'sciences'|'engineering', rank?: string} */
export async function paintStudy(canvas, spec) {
  const map = await loadMap(spec.id);
  canvas.width = map.w; canvas.height = map.h;
  const ctx = canvas.getContext('2d');
  ctx.putImageData(paintMap(map, spec.colours, {flag: spec.kind !== 'uniform'}), 0, 0);
  if (spec.kind !== 'uniform') return canvas;
  const meta = await loadMeta(spec.id);
  if (!meta) return canvas;
  // Division insignia from PDF 65, fitted into the drawn D.I. box (whose outline was absorbed into the badge region).
  if (meta.badge && spec.division) {
    const bm = await loadMap(`${spec.division}-badge`);
    const b = toCanvas(paintMap(bm, {badge: spec.colours.gold, device: spec.colours.black}, {flag: true, metalShade: false}));
    const [x0, y0, x1, y1] = meta.badge, bw0 = x1 - x0, bh0 = y1 - y0, k = Math.min(bw0 / b.width, bh0 / b.height) * 1.04;
    ctx.drawImage(b, (x0 + x1) / 2 - b.width * k / 2, (y0 + y1) / 2 - b.height * k / 2, b.width * k, b.height * k);
  }
  // Rank braid above the cuff of each sleeve.
  const pattern = RANKS[spec.rank || 'ensign'] || [];
  if (pattern.length) {
    const braid = await braidCanvas(spec.colours.gold), g = hex(spec.colours.gold), edge = mix(g, INK, .72);
    for (const cf of meta.cuffs) {
      const [ax, ay] = cf.a, [bx, by] = cf.b, [ux, uy] = cf.up, len = Math.hypot(bx - ax, by - ay), ang = Math.atan2(by - ay, bx - ax);
      const H = len * .24, gap = H * .32, start = H * .35;          // PDF 65: broad braid, about a quarter of the sleeve width
      pattern.forEach((full, i) => {
        const off = start + i * (H + gap);
        ctx.save(); ctx.translate(ax + ux * (off + H / 2), ay + uy * (off + H / 2)); ctx.rotate(ang);
        ctx.beginPath(); ctx.rect(0, -H / 2, len, H); ctx.clip();
        if (full) ctx.drawImage(braid, 0, -H / 2 - H * .25, len, H * 1.5);   // stamp's rope fills ~2/3 of its height
        else {                                                               // broken stripe: a row of separate diamonds (PDF 65)
          const step = H * 1.35, n = Math.ceil(len / step) + 1;
          for (let k = -1; k < n; k++) {
            const cx = k * step + step / 2 + (len % step) / 2;
            ctx.beginPath(); ctx.moveTo(cx - step * .42, 0); ctx.lineTo(cx, -H * .46); ctx.lineTo(cx + step * .42, 0); ctx.lineTo(cx, H * .46); ctx.closePath();
            ctx.fillStyle = `rgb(${g.join(',')})`; ctx.fill(); ctx.lineWidth = Math.max(1, H * .08); ctx.strokeStyle = `rgb(${edge.join(',')})`; ctx.stroke();
          }
        }
        ctx.restore();
      });
    }
  }
  // Optional single view (front / side / back) for small screens.
  if (spec.view && spec.view !== 'all' && meta.views?.[spec.view]) {
    const [a, b] = meta.views[spec.view], tmp = OffscreenCanvasOr(b - a, canvas.height);
    tmp.getContext('2d').drawImage(canvas, a, 0, b - a, canvas.height, 0, 0, b - a, canvas.height);
    canvas.width = b - a; ctx.drawImage(tmp, 0, 0);
  }
  return canvas;
}
