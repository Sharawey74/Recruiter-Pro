---
name: showcase-site
description: Build a static showcase site for a software project — a dark, evidence-led multi-page site on GitHub Pages with no build step. Use when asked for a project landing page, portfolio site, docs microsite, GitHub Pages site, architecture page, or a walkthrough of a running app. Also use when adding a page to an existing site built this way.
---

# Showcase site

A dark, technical, evidence-led static site. Three-ish pages, one stylesheet,
one small script, no build step and no framework — it ships to GitHub Pages by
copying a folder.

## When this fits, and when it does not

**Fits:** a project that wants to be *read* — a portfolio piece, an internal
tool people must be persuaded to adopt, apost-mortem, an architecture write-up.
The whole design assumes the reader is technical and skeptical.

**Does not fit:** a marketing page that needs A/B tests and analytics, a docs
site with fifty pages and search (use a generator), or anything needing a CMS.

## The one rule that makes this design work

**Every claim carries the file that proves it.** That is what the `.file` and
`.proof` components are for, and it is why the layout has room for them under
every card. A page of adjectives looks like every other project page; a page
where each assertion names `src/api.py · read_upload()` reads as true because
it can be checked.

Write the evidence first, then the sentence around it. If a card has no file to
name and no measured figure, it is decoration — cut it.

## Build order

1. **Copy `assets/` into `site/assets/`.** `style.css`, `main.js`, `favicon.svg`
   are complete and need no edits for a new project except the palette block at
   the top of the CSS.
2. **Re-token the palette** — `--violet`, `--green`, `--amber` and their `-dim`
   partners. Take them from the application's own tokens if it has any, so
   screenshots sit *inside* the page rather than on top of it.
3. **Write the pages.** Start from `references/page-skeleton.html`. Keep the
   header and footer byte-identical across pages; the nav highlight is done in
   JS so a renamed page cannot end up highlighted on the wrong one.
4. **Wire GitHub Pages** — see `references/deploy.md`.

Read `references/components.md` before writing markup. It is the full catalogue
with copy-paste HTML.

## Page shapes that work

| Page | Job | Backbone |
|---|---|---|
| `index.html` | What it is, why it is credible | hero → stat strip → cards of found problems → stack chips |
| `architecture.html` | How it fits together | inline SVG diagram → boundary table → decision cards |
| `walkthrough.html` | Proof it runs | numbered `.step` blocks, each with a real screenshot |

Three pages is usually right. A fourth is usually a section.

## Non-negotiables

- **Screenshots must be captured, not mocked.** The `.shot` frame styles a real
  screenshot; a mockup inside a browser chrome is a lie with extra steps.
- **Content must never depend on an animation having run.** `main.js` reveals
  everything immediately when `IntersectionObserver` is missing or
  `prefers-reduced-motion` is set. Do not add an effect without the same guard.
- **No external requests.** No CDN, no web font, no analytics. The page must
  render with JS blocked and offline.
- **Numbers carry their conditions.** "0.7 s" is not a measurement; "0.7 s,
  800 roles, 10-skill CV, model off" is. A figure without its input will be
  wrong the first time someone checks it.
- **Every page validates.** Balanced tags, one `<h1>`, `alt` on every image,
  `<title>` and `<meta name="description">` per page.

## Enhancements worth adding

These are not in the base stylesheet. Add them when the content asks for it —
see `references/enhancements.md` for the code.

| Enhancement | When |
|---|---|
| Copy-to-clipboard on code blocks | Any page showing a command a reader will run |
| Anchored headings with a `#` on hover | Pages people will link into |
| A skip-to-content link | Always, honestly — it is four lines |
| `prefers-contrast` overrides | The palette is low-contrast by design; this restores it |
| Open Graph and Twitter card tags | Anything that will be shared in a chat |
| A print stylesheet | Architecture pages get printed more than you expect |
| Lazy-loaded screenshots | More than about six images on one page |

## Checking the work

```bash
# balanced tags, on every page
python - <<'PY'
from html.parser import HTMLParser
import pathlib, sys
VOID={"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
class P(HTMLParser):
    def __init__(s): super().__init__(); s.stack=[]; s.err=[]
    def handle_starttag(s,t,a):
        if t not in VOID: s.stack.append((t,s.getpos()[0]))
    def handle_endtag(s,t):
        if not s.stack: s.err.append(f"stray </{t}> line {s.getpos()[0]}"); return
        top,ln=s.stack.pop()
        if top!=t: s.err.append(f"</{t}> line {s.getpos()[0]} closes <{top}> from line {ln}")
for f in pathlib.Path("site").glob("*.html"):
    p=P(); p.feed(f.read_text(encoding="utf-8"))
    print(f.name, "OK" if not p.err and not p.stack else (p.err or p.stack))
PY
```

Then serve it and look at it — at 1440px, at 375px, and with JS disabled:

```bash
python -m http.server 8080 --directory site
```
