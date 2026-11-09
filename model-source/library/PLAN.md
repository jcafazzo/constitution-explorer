# Plan: the Technical Library (the 1975 manual's companions and successors)

Goal: grow the site from one book into a shelf of the 1975 manual's companions and successors. Each volume gets the same two layers as the manual:

1. A **faithful virtual copy** made from the owner's own scan. It lives only in the private, password-gated Netlify build, never in the public repo.
2. An **explorer layer**: original 3D studies, measured data, cross-links and history. It can be public, as the current site is.

## The shelf

The first four titles are the ones you named. The DS9 manual is optional.

| # | Title | Year, credits | Physical form | Presenter | Explorer layer |
|---|---|---|---|---|---|
| 1 | *Star Trek Blueprints* (FJ's "Booklet of General Plans") | Ballantine, spring 1975 (24 May per Rehak); Franz Joseph | 12 large sheets in a plastic pouch, not a bound book | New **plan chest**: pull a sheet out, unfold it flat, deep-zoom on tiles | Deck-by-deck index; overlay the existing Constitution model's sections on each sheet; links to manual pp. 92–101 and 143–150 |
| 2 | *Star Trek Maps* | Bantam, August 1980. Jeffrey Maynard: design and coordination. Geoffrey Mandel: astronomical art | Box with four 4-colour wall maps and an instruction booklet | **Map table**: unfold each map on a desk, zoom and pan; the booklet uses the book engine | Interactive UFP chart tied to the manual's galactic coordinate system (p. 115), standard orbits (p. 119) and Federation chart (p. 122) |
| 3 | *Mr. Scott's Guide to the Enterprise* | Pocket Books, 1987; Shane Johnson | Trade paperback | Book engine | Refit Enterprise (films I–IV) as a new 3D study, shown alongside the TOS Constitution |
| 4 | *Star Trek: The Next Generation Technical Manual* | Pocket Books, 1991; Rick Sternbach and Michael Okuda | Trade paperback | Book engine | Optional: Galaxy class. It's a different era, so last |
| (5) | *DS9 Technical Manual* | 1998 | Paperback | Book engine | Only if wanted |

Also: a **Lineage** page, a timeline from the 1974 Equicon Blueprints to the 1991 TNG manual. It would reuse the sourced findings in `model-source/book/origins.md`, which already covers the Blueprints' dates, the Paramount and Roddenberry rift, and the official and fan successors.

## Corrections to the brief

- The author of *Mr. Scott's Guide* is **Shane Johnson**. "Lora Johnson" is a search-panel error.
- The Blueprints came out about six months *before* the manual, not "just before". They were drawn in late 1973, sold as a 500-copy private edition at Equicon in April 1974, and published by Ballantine in spring 1975. See origins.md.
- *Star Trek Maps* is not Mandel's alone. Wikipedia and catalogue records credit Jeffrey Maynard with design and coordination, and Mandel with the astronomical art. Calling it the manual's "truest spiritual sequel" is a fan opinion and should be presented as one.
- "Franz Joseph owned the rights to his designs" is consistent with origins.md: Paramount agreed not to contest FJ's copyright. That is the reason later official books started from fresh designs. Present it with the source.

## Engineering steps

1. **Generalise the book engine** (`dist/book.js`). Move everything specific to this book into a per-volume config:
   - the trim ratio, leaf structure, cover treatment, editions, contents and the folio text;
   - the manifest path, so pages live in `dist/library/<slug>/pages/`.
   Add the routes `#/library`, `#/library/<slug>` and `#/library/<slug>/<page>`, and keep `#/book` as an alias for the manual.
2. **Generalise the page renderer** (`model-source/book/render-pages.py`). Give it the slug, colour pages and dark pages as arguments, plus an option for very large sheets that writes deep-zoom tiles (needed for the Blueprints and the maps).
3. **The library shelf page** (`#/library`): the volumes standing on a shelf, spines out, each pulled out to open. Volumes without a scan stay on the shelf with a note. That's how the public site behaves today.
4. **Plan chest** (Blueprints) and **map table** (Maps): new presenters, built on the same three.js desk, lamp and paper as the book. A sheet is a thin slab with fold creases that unfolds panel by panel, and tiles stream in while zoomed.
5. **Explorer layers** for each volume, in the order of the table above. Every new 3D study follows the equipment-locker method: profiles measured off the scan at its scale bar, an IoU score against the drawing, and honest interpretation notes.
6. **Private build**. Add each volume's `dist/library/<slug>/` folder to the private Netlify repo (`star-fleet-technical-manual`) and keep it out of the public repo with `.gitignore`. The manual itself stays where it is.

## Order

1. **Blueprints first.** They're the same author, the same visual language and the most direct link to the existing Constitution model, and the plan chest is the most distinctive new presenter.
2. *Star Trek Maps* second. It ties straight into the manual's sciences section.
3. *Mr. Scott's Guide*.
4. The TNG manual.

## What only you can supply

- **Which titles you own.** Only owned copies get scanned.
- **Scans.** Use PDFs like the manual's. For the Blueprints and the maps, flatbed sheets in pieces at 300 dpi or more, which I can stitch together. Sheets around 2 ft wide won't fit a normal scanner.
- **Photos.** Pictures of the physical objects (the pouch, the map box, the covers) let the presenters match them, as the binder could have.
