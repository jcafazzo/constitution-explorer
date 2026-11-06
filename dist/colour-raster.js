// Raster colour studies painted from the manual's own drawings (no vector redraw).
// Each *-map.png is produced by model-source/colour/segment.py from the scanned plate:
//   R = linework / edge weight, G = region class × 20, B/A = halftone flag (uniforms) or emblem alpha (flags).
// Painting happens on a <canvas>; colours come from the SF code palette passed in.
const V = 'r1';
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
    const shade = metalShade ? 1.1 - .2 * (y / h) : 1;
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
      const base = col[k] || PAPER;
      c = k === 2 ? mix(base, SHEEN, r * .8) : mix(base, INK, r);
      o[i] = c[0]; o[i + 1] = c[1]; o[i + 2] = c[2]; o[i + 3] = 255;
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
  // Division insignia from PDF 65, scaled into the drawn D.I. position.
  if (meta.badge && spec.division) {
    const bm = await loadMap(`${spec.division}-badge`);
    const b = toCanvas(paintMap(bm, {badge: spec.colours.gold, device: spec.colours.black}, {flag: true, metalShade: false}));
    const [x0, y0, x1, y1] = meta.badge, bh = (y1 - y0) * 1.08, bw = bh * b.width / b.height, cx = (x0 + x1) / 2;
    ctx.drawImage(b, cx - bw / 2, y0 - (bh - (y1 - y0)) / 2, bw, bh);
  }
  // Rank braid above the cuff of each sleeve.
  const pattern = RANKS[spec.rank || 'ensign'] || [];
  if (pattern.length) {
    const braid = await braidCanvas(spec.colours.gold), ppc = meta.pxPerCm || 8.3, H = 1.25 * ppc, gap = .45 * ppc, start = .7 * ppc;
    for (const cf of meta.cuffs) {
      const [ax, ay] = cf.a, [bx, by] = cf.b, [ux, uy] = cf.up, len = Math.hypot(bx - ax, by - ay), ang = Math.atan2(by - ay, bx - ax);
      pattern.forEach((full, i) => {
        const off = start + i * (H + gap), h = full ? H : H * .6;
        ctx.save(); ctx.translate(ax + ux * (off + h / 2), ay + uy * (off + h / 2)); ctx.rotate(ang);
        if (full) ctx.drawImage(braid, 0, -h / 2, len, h);
        else for (let s = 0; s < 3; s++) ctx.drawImage(braid, 0, 0, braid.width * .3, braid.height, len * (s / 3 + .04), -h / 2, len * .25, h);
        ctx.restore();
      });
    }
  }
  return canvas;
}
