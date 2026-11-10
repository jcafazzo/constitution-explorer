#!/usr/bin/env python3
"""Assemble the owner's private reading copy of the book as a standalone page.

  python3 model-source/book/build-private.py OUT_DIR

Prerequisite: render-pages.py has filled dist/book/pages/.

Writes these to OUT_DIR (keep it outside the repo, because it contains the
page images):
  index.html      the page body (no doctype; the private host wraps it)
  preview.html    the same page with a doctype, for a local check
  book.js         dist/book.js, loading three.js r180 from the jsDelivr CDN
  library/volumes.js  dist/library/volumes.js, the volume settings book.js reads
  book.css        dist/book.css
  book/pages/     manifest.json, sm/, lg/

The copy is meant for a private, signed-in host that only the owner can open,
such as a private claude.ai artifact. It is a copyrighted book: never make it
public.
"""
import hashlib, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THREE = 'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js'

PAGE = """<title>Star Fleet Technical Manual</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Michroma&family=Space+Mono:wght@400;700&display=swap">
<link rel="stylesheet" href="book.css?v=__V__">
<style>
/* One visual world: a dark desk under a lamp, paper-coloured reference panels. */
:root{
 --desk:#17120d; --lamp:#efe7d6; --brass:#c9a34e;
 --paper:#f4f2e9; --ink:#202321; --muted:#686a60; --rule:#b8b9ae; --red:#a72c25;
 --mono:'Space Mono',ui-monospace,Menlo,monospace; --display:'Michroma','Arial Black',Arial,sans-serif;
 color-scheme:dark
}
html,body{background:var(--desk);color:var(--lamp)}
body{font:14px/1.6 Arial,Helvetica,sans-serif}
.eyebrow{font:10px var(--mono);letter-spacing:1.5px;text-transform:uppercase;color:var(--red);display:block;margin-bottom:14px}
.folio{display:flex;justify-content:space-between;gap:20px;font:9px var(--mono);letter-spacing:1px;color:#a99a80;padding:12px max(16px,env(safe-area-inset-right,0px)) 10px max(16px,env(safe-area-inset-left,0px))}
main.book-route{padding:0;max-width:none}
main.book-route>.folio{margin:0;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.bk{border:0}
.bk-stage{height:calc(100svh - 120px)}
.bk-bar{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.bk-notes{background:var(--paper);color:var(--ink);max-width:none;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.bk-notes p{max-width:62ch}
@media (max-width:700px){.bk-stage{height:calc(100svh - 196px);min-height:340px}}
</style>
<main id="main"></main>
<script type="module">
import {renderBook} from './book.js?v=__V__';
const start = location.hash.match(/^#p(\\d+)$/);
renderBook(document.getElementById('main'), '/book', {standalone: true, initial: start ? start[1] : ''});
</script>
"""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    if out == ROOT or ROOT in out.parents:
        sys.exit('Choose an output folder outside the repository: it will hold the page images.')
    pages = ROOT / 'dist' / 'book' / 'pages'
    if not (pages / 'manifest.json').exists():
        sys.exit('No rendered pages. Run render-pages.py first.')
    out.mkdir(parents=True, exist_ok=True)
    js = (ROOT / 'dist' / 'book.js').read_text()
    old = "from './vendor/three.module.js';"
    assert old in js, 'book.js import changed'
    (out / 'book.js').write_text(js.replace(old, f"from '{THREE}';"))
    shutil.copy(ROOT / 'dist' / 'book.css', out / 'book.css')
    # book.js reads the manual's settings from library/volumes.js, so that goes along too.
    assert "from './library/volumes.js" in js, 'book.js no longer imports library/volumes.js'
    (out / 'library').mkdir(exist_ok=True)
    shutil.copy(ROOT / 'dist' / 'library' / 'volumes.js', out / 'library' / 'volumes.js')
    # Version stamp from the content, so a republished copy never runs a cached old script.
    v = hashlib.sha1((out / 'book.js').read_bytes() + (out / 'book.css').read_bytes() + (out / 'library' / 'volumes.js').read_bytes()).hexdigest()[:10]
    page = PAGE.replace('__V__', v)
    (out / 'index.html').write_text(page)
    (out / 'preview.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + page + '</body></html>')
    dst = out / 'book' / 'pages'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(pages, dst)
    print('wrote', out)


if __name__ == '__main__':
    main()
