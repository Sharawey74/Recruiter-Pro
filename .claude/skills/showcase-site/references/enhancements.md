# Enhancements

Not in the base stylesheet. Add what the content asks for; adding all of them
to a three-card page is worse than adding none.

## Skip link — always

Four lines, and the first thing a keyboard user needs. The skeleton already has
the anchor; this styles it.

```css
.skip {
  position: absolute;
  left: 12px;
  top: -60px;
  z-index: 10;
  padding: 10px 16px;
  border-radius: 10px;
  background: var(--surface-3);
  border: 1px solid var(--line-strong);
  color: var(--text);
  text-decoration: none;
  transition: top 0.15s;
}
.skip:focus { top: 12px; }
```

## Visible focus ring

The base sheet relies on the browser default, which disappears against a dark
ground in some engines. Do not remove outlines; replace them.

```css
:where(a, button, .btn, summary, [tabindex]):focus-visible {
  outline: 2px solid var(--violet);
  outline-offset: 3px;
  border-radius: 6px;
}
```

## Copy button on code blocks

For any page showing a command someone will run.

```css
.codeblock { position: relative; }
.codeblock .copy {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 10px;
  font: 600 0.74rem var(--mono);
  color: var(--text-dim);
  background: var(--surface-3);
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.codeblock:hover .copy,
.codeblock .copy:focus-visible { opacity: 1; }
.codeblock .copy[data-done="1"] { color: var(--green); border-color: var(--green); }
```

```js
/* Progressive: the button is created by JS, so with JS blocked there is no
   button promising something that cannot happen. */
document.querySelectorAll("pre.codeblock > code").forEach(function (code) {
  var pre = code.parentNode;
  var btn = document.createElement("button");
  btn.className = "copy";
  btn.type = "button";
  btn.textContent = "Copy";
  btn.addEventListener("click", function () {
    navigator.clipboard.writeText(code.innerText).then(function () {
      btn.textContent = "Copied";
      btn.dataset.done = "1";
      setTimeout(function () {
        btn.textContent = "Copy";
        delete btn.dataset.done;
      }, 1600);
    });
  });
  pre.appendChild(btn);
});
```

Requires `navigator.clipboard`, which needs HTTPS or localhost. On GitHub Pages
that is satisfied.

## Anchored headings

For pages people will link into — architecture pages especially.

```css
.anchor {
  margin-left: 8px;
  color: var(--text-faint);
  text-decoration: none;
  opacity: 0;
  transition: opacity 0.14s;
}
h2:hover .anchor, h3:hover .anchor, .anchor:focus-visible { opacity: 1; }
```

```js
document.querySelectorAll("main h2[id], main h3[id]").forEach(function (h) {
  var a = document.createElement("a");
  a.className = "anchor";
  a.href = "#" + h.id;
  a.textContent = "#";
  a.setAttribute("aria-label", "Link to this section");
  h.appendChild(a);
});
```

`scroll-padding-top: 90px` is already set on `html`, so an anchored heading
lands below the sticky header rather than under it.

## High-contrast override

The palette is deliberately low-contrast. `--text-dim` on `--bg` is around
7:1 — fine for AA, but some readers ask the OS for more. Honour it.

```css
@media (prefers-contrast: more) {
  :root {
    --text-dim: #d4d4e4;
    --text-faint: #a6a6bd;
    --line: rgba(255, 255, 255, 0.18);
    --line-strong: rgba(255, 255, 255, 0.3);
  }
}
```

## Print stylesheet

Architecture pages get printed and PDF'd more than you expect.

```css
@media print {
  body { background: #fff; color: #000; }
  body::before,
  .site-header,
  .site-footer,
  .hero-actions,
  .skip { display: none !important; }
  .card, .table-scroll, .shot { border-color: #bbb; break-inside: avoid; }
  .card { background: #fff; }
  p, .lede { color: #222; }
  section { padding: 24px 0; border-top: 1px solid #ddd; }
  /* A printed link that says "here" is useless. */
  main a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.8em; color: #555; }
  .reveal { opacity: 1 !important; transform: none !important; }
}
```

That last line matters: without it, any section that had not been scrolled into
view prints blank.

## Lazy screenshots

Past about six images on a page. `loading="lazy"` plus explicit dimensions —
the dimensions are what stop the page reflowing as each one lands.

```html
<img src="..." alt="..." width="1440" height="900" loading="lazy" decoding="async">
```

Never lazy-load an image above the fold; it delays the thing the reader came
for.

## Reduced motion

`main.js` already guards the reveal. If any further animation is added, extend
this rather than writing a second guard.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
```
