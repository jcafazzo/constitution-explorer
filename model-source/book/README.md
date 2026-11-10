# The virtual book (`#/book`): build journal

A tribute to Franz Joseph's *Star Fleet Technical Manual* (Ballantine, November 1975), shown as a physical book you can open and page through. Files:

- `dist/book.js`: the three.js book engine, its controls, the contents and the magnifier.
- `dist/book.css`: styles scoped to `.book-route` and `.bk*`.
- `model-source/book/render-pages.py`: renders and cleans the owner's scan into `dist/book/pages/`.
- Minimal hooks: one import and one route branch in `dist/app.js`, plus a nav link and a stylesheet link in `dist/index.html`.

## The Technical Library (`#/library`)

The book is now one volume on a shelf of five (plan: `model-source/library/PLAN.md`). Files:

- `dist/library/volumes.js`: one config object per volume, in shelf order. Everything that was specific to the 1975 manual in `book.js` lives here under the volume's `book` key: trim ratio, editions (cover treatment, card leaves, closed-book labels), cover title lines, tinted blank sides, contents, folio text, the notes and history under the stage, and the saved-settings key. The header comment lists every field. `loadManifest(vol)` fetches `<pages>manifest.json`; a volume has a scan when that loads with a page count.
- `dist/book.js`: the same engine, now reading a volume. `renderBook(main, path, {volume, base, crumb, manifest})`; with no options it shows the manual at `#/book`, as before.
- `dist/library.js`, `dist/library.css`: the shelf, the volume card and the lineage page. The shelf is plain HTML buttons (no WebGL), so it works by keyboard and without a graphics context. The spines are original typographic designs; they do not copy any cover.

Routes:

- `#/library`: the shelf.
- `#/library/<slug>`: a volume. If it is a book and can open (it has a scan, or it is the manual, which opens on blank sheets without one), the book engine shows it; `#/library/<slug>/<page>` is a deep link. Otherwise the shelf shows with that volume pulled out and its card: what it is, how it will be shown, and that no scan has been added.
- `#/library/lineage`: the timeline from the 1973 drawings to the 1991 manual. Every entry comes from `origins.md` or the plan's table and carries its source.
- `#/book`, `#/book/<page>`: unchanged; an alias for the manual.

Slugs: `blueprints`, `manual`, `maps`, `mr-scotts-guide`, `tng-technical-manual`. The manual's pages stay in `dist/book/pages/`. Every other volume's pages go in `dist/library/<slug>/pages/`, which is gitignored (`dist/library/*/pages/`).

To add a scan of another volume:

```
python3 model-source/book/render-pages.py scan.pdf --slug mr-scotts-guide --colour 1,2,128 --dark 1,128 --title "Mr. Scott's Guide to the Enterprise"
```

Renderer options: `--slug` (default `manual`), `--out DIR`, `--colour LIST`, `--dark LIST` (colour pages whose paper is not white), `--aspect X` (default: the median of the PDF's page boxes), `--title TEXT`. Lists take `1,2,49` or ranges `1-4,128`. With no options the output paths, names and manifest are the manual's, as before.

Not built yet:

- **Deep-zoom tiles** (TODO). The Blueprints sheets and the wall maps need a tile pyramid. The plan chest and map table that would read the tiles do not exist, so there is no tile layout to write to; `render-pages.py` carries the TODO.
- The plan chest and map table presenters, and every explorer layer. Blueprints and Maps show a card even if a scan is present.
- The two paperbacks have a minimal book config (one edition, the scan's own cover, no contents list). Check trim, colour pages and contents against the scan when one arrives.

## Copyright and publication

The manual is a copyrighted work, and this repository and its GitHub Pages site are public. The owner owns a physical copy and wants it preserved digitally. So:

- Page images are **generated locally** from the owner's PDF into `dist/book/pages/`, which is in `.gitignore`. They are not committed and are not published.
- Without the images, as on the public site, the book still works: the binder opens onto blank sheets numbered by scan page, and a note explains that the pages render from the owner's copy. The *Owner's copy* edition is disabled there, because its cover is a scan.
- The binder cover is an original rendering: plain gold title type on black vinyl. It does not trace the paperback's cover art, the STAR TREK logo or the seal; those appear only in the owner's local scan.
- Whether to publish the page images is the owner's decision. Nothing in this branch does so.

## Running it locally

```
python3 model-source/book/render-pages.py "/path/to/Star Trek Star Fleet Technical Manual.pdf"   # about 2-3 minutes; about 50 MB
python3 -m http.server 4174 -d dist
# open http://localhost:4174/#/book   (deep links: #/book/75)
```

Requirements: poppler (`pdftoppm`, `pdfinfo`), `cwebp`, Python 3 with Pillow and numpy.

## Owner's private copy

`model-source/book/build-private.py OUT_DIR` assembles a standalone copy outside the repo: a wrapper page, `book.js` (loading three.js r180 from jsDelivr), `library/volumes.js` (the manual's config), the CSS and the rendered pages. It is published as a **private** claude.ai artifact that only the owner's account can open. Don't share it or make it public. Deep links there use `#p75`.

## Research: the physical book

- Ballantine published the first edition in November 1975. The copyright page carries the stardate 7511.01 edition marker and the SBN 345-24730-2-695. ([Wikipedia](https://en.wikipedia.org/wiki/Star_Trek_Star_Fleet_Technical_Manual), [Memory Alpha](https://memory-alpha.fandom.com/wiki/Star_Trek_Star_Fleet_Technical_Manual), [Authorwars](https://authorwars.com/publications/star-fleet-technical-manual-253748.html))
- The first printing came as a **red softcover in a removable black vinyl binder** with the title printed in gold, styled like a real service manual. Later printings were paperbacks with printed covers that name *Star Trek*. ([Memory Alpha](https://memory-alpha.fandom.com/wiki/Star_Trek_Star_Fleet_Technical_Manual), and bookseller listings such as [AbeBooks](https://www.abebooks.com/first-edition/Star-Trek-Fleet-Technical-Manual-Franz/31449211421/bd) and [Biblio](https://www.biblio.com/book/star-trek-star-fleet-technical-manual/d/1175971620))
- "The 1975 version with the black cover" is therefore read as the **black binder**, which is the default presentation. The owner's scanned copy is a later printing with a printed black paperback cover ($10.95, barcode), offered as the *Owner's copy* edition.
- I found no photograph of the binder to work from. The gold lettering layout (three centred lines and a rule) is an approximation from the descriptions, and the heat-sealed seam and the inner pocket edge are plausible details, not verified ones. If the owner has the binder, a photo would let this be corrected.
- The trim comes from the scan: median page box 0.7712 (width:height). Booksellers' sizes vary (10×8 in, 4to, 29 cm), so the scan was taken as the most reliable source.
- Leaf structure follows the scan. In the binder edition the leaves are: board, then leaves (2,3), (4,5) … (158,159), with the red title leaf on heavier card, then the back board. In the owner's-copy edition: card cover (p1 / blank inside), the same leaves, then the card back cover (blank inside / p160). The inside covers were not scanned, so they render as plain card.

## Research: flipbook techniques

- **StPageFlip** (`page-flip`, [Nodlik/StPageFlip](https://github.com/Nodlik/StPageFlip)): the best-known modern 2D flipbook, with canvas or HTML pages, soft and hard pages, and drawn shadows. It's convincing for a flat page, but the book has no thickness, stack or lighting.
- **turn.js**: the classic jQuery flipbook. Its licence is non-commercial, and it's dated and 2D.
- **three.js 3D books**: a [three.js forum thread](https://discourse.threejs.org/t/animating-pages-of-a-book/28883) on animating book pages, SkinnedMesh page books in React Three Fiber (for example the [Zyora 3D book](https://zeeljasani.vercel.app/project/3d-book)), and bend modifiers in [quick_flipbook](https://awesome.ecosyste.ms/projects/github.com%2Fbandinopla%2Fquick_flipbook). These give real depth and light, but most bend each page with a single rotation, so pages either stay flat or bend with a constant curvature.

**Choice:** a custom three.js book, since three.js is already vendored and adds no dependency. Its improvements over those references:

1. Each leaf is integrated **by arc length** from a tangent-angle profile, so paper never stretches, whatever the bend.
2. The resting shape comes from a **perfect-bound gutter**: every leaf rises from the spine to its height in the stack. The angle amplitude is solved by bisection, so leaves land exactly on top of the stack. Boards use the same model with a short hinge.
3. A turn **blends the left and right resting curves** and adds a curl that leads early and relaxes late. While you drag, the free edge follows your finger, `acos(x/u)`, and twists toward the grabbed corner.
4. Leaves are **slabs** with real thickness and edge strips. The stacks under them are solid blocks with a striped leaf-edge texture, and the stack heights change as you read.
5. Shadows are real: the turning leaf casts onto the page beneath. The gutter shading and paper tooth (a bump map) are done in the shader, and there's an optional *Aged paper* toning.

## Page cleanup (render-pages.py)

The scan is 150 ppi for almost every page; p2 is at 300. Pages render at their native resolution and are normalised to one trim (cover-fit and centred, losing at most about 2% at the margins). Monochrome pages get a histogram-based levels pass (paper to white, ink to near-black, a slight gamma to firm up hairlines, near-white specks removed), then an unsharp mask. Colour pages (1, 2, 49, 158, 160) get a white balance from the paper or border where there is one, plus gentle contrast. The output is WebP at two sizes: `sm` is 1024 px tall, used for the 3D textures; `lg` is 2048 px tall, used for the magnifier and for sharp text when the book is shown large. The page tone and fibre come from the renderer, not from the image.

## Interaction

- Click or tap a page to turn it. Drag a page to curl it, and release past halfway (or flick) to complete the turn. Mouse hover lifts the corner as a hint.
- Keys: ← → / PageUp / PageDown / Space to turn, Home and End to close, Enter or + to magnify.
- Contents panel (section and technical-order titles, numbered by scan page), a position slider, and deep links `#/book/<page>`.
- In-place zoom, on the book itself:
  - Zooming in: scroll, pinch, double-click/double-tap, or the − / + buttons and keys zoom toward the point under the cursor or fingers, up to 450%. The camera flattens its tilt as it closes in.
  - Moving around: drag (or ↑ ↓) pans while zoomed.
  - Returning: double-click, *Whole book*, 0 or Esc returns to the whole book, as does turning a page.
  - While zoomed, the visible pages switch to the 2048 px images.
- *Page view* (the earlier magnifier) opens one page flat with its own zoom, and ← → move through pages there.
- Phones and narrow windows show one page at a time with a slight tilt, and taps go page by page.
- With `prefers-reduced-motion`, turns and camera moves are instant, and there's no hover lift and no sound.
- Sound: a synthesised paper rustle and a board thump (Web Audio). It can be switched off, and the setting is remembered along with the edition and paper tone.
- Performance: rendering happens only when something changes. Textures load lazily for ±3 leaves and are pruned beyond ±4. A long jump waits up to 0.7 s for the destination pages, then turns the last 7 leaves visibly and snaps the rest. Shadow maps are 1024 px on phones.

## Independent review (applied)

A separate reviewer read the code and screenshots cold. Fixed after its report:

- Double-click magnifies the page that was clicked. Before, the first click turned the page and the next page was magnified.
- On the public site, the placeholder sheets' textures are now pruned, so they no longer accumulate on phones.
- Rapid jumps can't land out of order (a jump sequence token).
- A second finger no longer orphans a half-turned leaf.
- The magnifier keeps keyboard control after you drag the image; ↑ ↓ and Shift+← → pan.
- Space, PageUp, PageDown, Home and End only turn pages when focus is in the book, so the page still scrolls normally.
- Taps aren't dropped while a leaf is moving. On one-page view, a swipe toward the facing page pans to it.
- The hover lift clears when the page turns. An edition switch keeps the page you were reading.
- The `AudioContext` is created inside a user gesture and closed on leave. There's now a soft settle tick when a leaf lands.
- The cover textures are kept rather than re-uploaded. The 2048 px swap loads only the page shown on phones. A drag release honours reduced motion. The magnifier refits on resize.
- The contents highlights the current section. The stage has `role="region"`, and disabled controls have higher contrast.
- Authenticity changes:
  - The gutter is wider and softer (the hard dark band is gone).
  - The binder boards overhang the leaves.
  - Ink is a warm near-black.
  - The camera is lower.
  - Public placeholder sheets carry only a small folio number.
  - Ink-heavy pages fall back to a higher paper percentile. In this scan only the colour pages fall below the threshold, and they use the colour path anyway.

## Not done / known limits

- Show-through of the reverse page (cheap 1975 stock) is not simulated.
- The binder has square corners, and its lettering uses the site's Michroma face, not the lettering of the manual's own title sheet.
- In the binder edition, a deep link to page 160 (the paperback's back cover) opens the closed binder at `#/book`.

- The binder's exact lettering, spine and inner pockets are unverified (see above).
- No deskewing. Pages are levelled and sharpened but not straightened.
- The contents labels are short paraphrases of page headings, mapped to scan page numbers, because the manual has no page numbers. A few groupings (for example "Medical instruments" for 124–132) are summaries.
- The inside covers aren't in the scan, so they are plain card or vinyl.
- On the public site the console shows one expected 404 for the missing `book/pages/manifest.json`.
