# Publishing to GitHub Pages

The site is static files in `site/`. Nothing is built, so the workflow uploads
the folder as-is.

`.github/workflows/pages.yml`:

```yaml
name: Pages

on:
  push:
    branches: [main]
    paths: ["site/**", ".github/workflows/pages.yml"]
  workflow_dispatch:

# Pages needs these; the defaults are not enough.
permissions:
  contents: read
  pages: write
  id-token: write

# One deploy at a time. Do not cancel in progress — a half-finished
# deployment is worse than a slightly stale one.
concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - id: deployment
        uses: actions/deploy-pages@v4
```

Then: **Settings → Pages → Source → GitHub Actions.** Without that the workflow
succeeds and publishes nothing, which is the failure that wastes the most time.

## Things that bite

**Paths are relative, so the site works at a sub-path.** GitHub Pages serves a
project site at `/REPO/`, not `/`. `assets/css/style.css` resolves; `/assets/css/style.css`
404s in production while working perfectly on `python -m http.server`.

**`.nojekyll` if any path starts with an underscore.** Jekyll silently drops
those. Not needed otherwise, but harmless.

**Open Graph images must be absolute URLs.** A relative `og:image` does not
resolve when Slack or LinkedIn fetches it.

**Check the deployed site, not the local one.** The two differ in exactly the
ways above, and only in production.
