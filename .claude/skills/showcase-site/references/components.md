# Component catalogue

Copy-paste HTML for every component in `assets/style.css`. Nothing here needs
a class you have to invent.

## Design tokens

Defined on `:root`. Re-token the three accents per project; leave the rest.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0a0a0f` | Page ground |
| `--surface` | `#12121b` | Cards |
| `--surface-2` | `#171722` | Buttons, chips, table headers |
| `--surface-3` | `#1e1e2c` | Hover states |
| `--line` | `rgba(255,255,255,.08)` | Ordinary borders |
| `--line-strong` | `rgba(255,255,255,.14)` | Button borders |
| `--text` | `#e9e9f2` | Headings, emphasis |
| `--text-dim` | `#a8a8bd` | Body copy |
| `--text-faint` | `#74748c` | File paths, captions |
| `--violet` | `#b8a4f5` | Primary accent, links, eyebrows |
| `--green` | `#6ee7a8` | Proof, success, "this is verified" |
| `--amber` | `#f5c26b` | Caution, trust boundaries, "be careful here" |
| `--mono` | JetBrains Mono stack | Code, figures, file paths, eyebrows |
| `--wide` | `1120px` | Content max-width |
| `--radius` | `14px` | Cards, panels |

**Accent semantics matter.** Violet is neutral emphasis. Green means *proven* —
a measured figure, a passing guard. Amber means *watch out* — a trust boundary,
a silent-failure mode. Do not use them decoratively; the reader learns the code
within one page and a misuse reads as a mistake.

## Layout

```html
<section class="reveal">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Category</p>
      <h2>The claim this section makes</h2>
      <p class="lede">One or two sentences. Max 68ch by design.</p>
    </div>

    <div class="grid grid-2">
      <!-- cards -->
    </div>
  </div>
</section>
```

- `.wrap` — centres at `--wide` with 22px gutters. Every section needs one.
- `.reveal` — opts the section into the fade-in. Safe to omit.
- `.grid-2` — `minmax(320px, 1fr)`, so it collapses to one column on its own.
- `.grid-3` — `minmax(268px, 1fr)`. For chips or short cards, not prose.

## Card

The workhorse. One claim, one paragraph, one file reference.

```html
<article class="card">
  <h3><span class="badge badge-violet">Concurrency</span></h3>
  <p>
    <strong>The one-sentence version.</strong> Then the mechanism, then the
    consequence. One paragraph — a second paragraph restating the fix reads as
    padding when the reader is scanning six of these.
  </p>
  <div class="proof"><b>8.13 s → 0.033 s</b> with identical output.</div>
  <span class="file">src/path/file.py · function_name()</span>
</article>
```

- `.proof` — green left rule. For a measured before/after. Optional.
- `.file` — monospace, top-bordered, at the card foot. **Never omit this.**

## Badges

```html
<span class="badge badge-violet">Concurrency</span>
<span class="badge badge-green">Honest metrics</span>
<span class="badge badge-amber">Trust boundary</span>
```

Uppercase monospace, pill. One per card, inside the `<h3>`.

## Stat strip

Directly under the hero. Three to five items; more and none of them land.

```html
<div class="stat-strip">
  <div class="stat"><b>800</b><span>roles in the corpus</span></div>
  <div class="stat"><b>544</b><span>tests passing</span></div>
  <div class="stat"><b>84.07%</b><span>branch coverage</span></div>
</div>
```

## Chips

For a stack list. Name and version, nothing else.

```html
<div class="chips">
  <span class="chip"><b>FastAPI</b> <code>0.104.1</code></span>
  <span class="chip"><b>Next.js</b> <code>16.3.0</code></span>
</div>
```

Versions must match the lockfile. A chip claiming a version you do not pin is
the cheapest possible thing to catch you out on.

## Table

Always wrapped — it scrolls on narrow screens instead of breaking the layout.

```html
<div class="table-scroll">
  <table>
    <thead><tr><th>Boundary</th><th>Crosses</th><th>Enforced by</th></tr></thead>
    <tbody>
      <tr><td>Browser → API</td><td>Network</td><td><code>CORS_ORIGINS</code></td></tr>
    </tbody>
  </table>
</div>
```

Use `<td class="num">` for figures — right-aligns and switches to monospace.

## Screenshot frame

```html
<figure class="shot">
  <div class="shot-bar">
    <span class="dots"><i></i><i></i><i></i></span>
    <span class="shot-url">localhost:3000/results</span>
  </div>
  <img src="assets/img/screenshots/06-results.webp"
       alt="Results page showing eight ranked matches with score rings"
       width="1440" height="900" loading="lazy">
</figure>
```

- `.shot.is-full` — removes the height cap for a tall page capture.
- `.shot.is-mobile` — narrow frame for a 375px capture.
- **Always set `width`/`height`.** Without them the page reflows as images land.
- The `alt` describes what the screenshot *shows*, not that it is a screenshot.

## Walkthrough step

```html
<div class="stage">
  <div class="step">
    <div class="step-head">
      <span class="step-num">3</span>
      <h3>Scoring against the corpus</h3>
    </div>
    <p>What happens, and what to look at in the image below.</p>
    <figure class="shot"><!-- ... --></figure>
  </div>
</div>
```

## Note

An aside that must not be missed. Sparingly — two per page at most.

```html
<div class="note is-green">
  <p><strong>Deliberately absent.</strong> No microservices, no queue, no
  vector database. Each was considered and rejected for a stated reason.</p>
</div>
```

`.is-green` for a positive claim, `.is-violet` for neutral, bare for caution.

## Buttons

```html
<a class="btn btn-primary" href="...">Read the architecture</a>
<a class="btn" href="...">View the repository</a>
<a class="btn btn-sm" href="...">Smaller</a>
```

Inline SVG icons only, 16px, as a child of the anchor.

## Inline SVG diagram

```html
<div class="diagram">
  <svg viewBox="0 0 900 420" role="img" aria-label="Plain-language description">
    <!-- use var(--violet) etc. directly in fill/stroke -->
  </svg>
</div>
```

Inline, never an `<img>` — the SVG reads the CSS custom properties, so it
re-tokens with the palette instead of becoming a stale asset. Give it a real
`aria-label`; a diagram is content.
