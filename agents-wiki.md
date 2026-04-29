# nuBlog Comprehensive Developer Wiki (v4.0)

Technical reference for human and agent contributors to **nuBlog**. Validated against the live tree on 2026-04-29 after v2.1 second-pass audit.

---

## 1. Core Identity & Philosophy
nuBlog is an "Anti-Modern" static site designed for longevity and minimalism.
- **Zero Frameworks.** No React, Vue, Tailwind, or build tools. Vanilla HTML/CSS/JS only.
- **Static-only hosting.** Anything dynamic is client-side fetch + DOM injection.
- **Bot Resistance.** Aggressive blocking of AI crawlers (see §2.3).
- **One Python build step.** `scripts/build-sitemap.py` regenerates all derived files; never hand-edit them.

---

## 2. Architectural Deep Dive

### 2.1 The Partial Inclusion Engine (`js/include.js`)
Every page that wants the shared header/footer ends with:
```html
<div id="site-header"></div>
...
<div id="site-footer"></div>
<script src="<path>/js/include.js" data-base="<base>"></script>
```

What it does, in order:
1. Reads `data-base` from its own `<script>` tag (default `.`), trims trailing slashes, exposes it as `window.nublogBase`.
2. **Validates** that `data-base` matches the page's actual depth — logs `console.warn` if mismatch.
3. **Immediately** appends `js/bot-blocker.js` to `<head>` (fires before partials so scrapers get blanked early).
4. Fetches `partials/header.html` and `partials/footer.html`, replaces every `%BASE%` token with `data-base`, injects them into `#site-header` / `#site-footer`.
5. After both partials resolve, appends `js/counter.js` (hit counter writes into footer).
6. In parallel, appends `js/oneko.js` (cursor cat) and `js/blog-nav.js` (prev/next links — self-gates to `/blog/*.html` URLs only).

**The `%BASE%` Token.** Always use `%BASE%` for absolute-from-root paths inside `partials/header.html` and `partials/footer.html`. Never hardcode.

### 2.2 Global Styling & Layout (`styles/style.css`)
- **Container:** `.content` (85% width, max 1000px, `padding: 16px 20px` balanced top/bottom).
- **Typography:** Web-safe sans-serif stacks (Lucida Grande, Verdana).
- **Gallery grid:** `.gallery-grid` uses `grid-template-columns: repeat(auto-fill, minmax(300px, 1fr))` — handles mixed orientations. Collapses to single column at 600px.
- **Mobile grids:** `.builds-grid` collapses to single column at 550px (via in-page media query in `blog/builds/index.html`). Gallery index grids collapse to single column at 500px (via in-page media query in `galleries.html`).
- **Single stylesheet.** Don't add new `.css` files; extend `style.css`.

### 2.3 Bot Defense (`js/bot-blocker.js` + `robots.txt`)
Three layers:
1. **Passive (`robots.txt`).** 200-line categorized blocklist of 142 unique AI crawler agents (sourced from Known Agents), organized by category (AI Data Scrapers, AI Search, AI Assistants, AI Agents, AI Coding Agents, AI Data Providers, Automated Browsers, Traditional Search, SEO/Marketing, Misc, Catch-all).
2. **Static meta-tag.** Every HTML file carries `<meta name="robots" content="noai, noimageai">` in `<head>`. The `build-sitemap.py` template does the same for `all-images.html`. This is **in addition to** the runtime injection below — providing defense for crawlers that don't execute JS.
3. **Runtime meta-tag injection.** On every page load `bot-blocker.js` injects additional per-crawler opt-out tags and the `ai-training: unauthorized` property.
4. **Active blanking.** If `userAgent` matches the bot regex *or* `navigator.webdriver === true`, the script wipes the document root so scrapers receive an empty page.

### 2.4 Build Script (`scripts/build-sitemap.py`)
The only build step. Run before deploying:
```bash
python3 scripts/build-sitemap.py
```
Generates / rewrites these derived files (do **not** hand-edit any of them):
- `js/sitemap-data.js` — filesystem tree consumed by `sitemap.html`. Excludes agent/audit `.md` files.
- `all-images.html` — flat grid of every image under `images/` (~825 images).
- `js/blog-nav.js` — the `blogPosts` array between `AUTOGEN-START/END blogPosts` markers, sorted newest-first.
- `blog.html` — post list between `<!-- AUTOGEN-START/END blog-list -->` markers, with titles extracted from `<title>` tags.
- `galleries/monthly/*.html` — gallery grids between `<!-- AUTOGEN-START/END gallery-grid -->` markers, auto-generated from `images/monthly/` with PIL orientation detection (horizontal first, separator, then vertical).
- **Image size check** — warns about files >1 MB at the end of the build.

### 2.5 Scaffold Script (`scripts/new-page.py`)
Generate boilerplate pages with correct conventions:
```bash
python3 scripts/new-page.py -t blog|builds-project|builds-machine|monthly-gallery -T "Title" [-d "Month Year"] [-f filename.html]
```

---

## 3. Interactive Systems

### 3.1 Hit Counter (`js/counter.js`)
- API: `api.counterapi.dev` (namespace + key).
- Fetched count is offset by **+6500** to reflect legacy traffic.
- Injects total into `#hit-counter` (lives in `partials/footer.html`).

### 3.2 Oneko (`js/oneko.js`)
- Pixel-art cat following the cursor via `setInterval(100ms)`.
- Resolves sprite path through `window.nublogBase` → `${base}/images/oneko.gif`.

### 3.3 Blog Nav (`js/blog-nav.js`)
- Self-gates: only runs when `pathname` matches `/blog/*.html`.
- Finds back-link by `a.back-link` selector.
- Reads the `blogPosts` array (chronological, newest first) and injects prev/next links.
- Sets `innerHTML` to `← back to blog` and `href` to `base + '/blog.html'`.
- The array between `AUTOGEN-START/END blogPosts` is **regenerated by `scripts/build-sitemap.py`**.

---

## 4. Content Subsystems

### 4.1 Galleries
- **Index:** `galleries.html` (root, linked from `partials/header.html` as "photos").
- **Data file:** `js/gallery-data.js` (source of truth for gallery grid cards). All `href` and `previewImage` paths are **relative to site root**.
- **Renderer:** `js/gallery.js` clones `<template>` tags.
- **Sub-pages:**
  - `galleries/animals.html` — animal photo collection (depth 1)
  - `galleries/videos.html` — YouTube embeds with `loading="lazy"` (depth 1)
  - `galleries/cameras/` — per-camera collections (canon-2022 through canon-2026, canon-sd400 hub, disposable, vivitar-pz3090 hub, vivitar-san-diego, vivitar-utah)
  - `galleries/monthly/` — monthly archive pages (auto-generated, see §2.4)

### 4.2 Plants
- Top-level index: `plants.html` (depth 0).
- Detail pages: `plants/collection.html` (depth 1) and monthly progress under `plants/progress/2026-MM.html` (depth 2).
- Back-links: `plants/collection.html` uses `href="../plants.html"`. Progress pages use `href="../../plants.html"`.

### 4.3 Blog
- Top-level index: `blog.html` (depth 0). Post list is auto-generated.
- Posts: `blog/YYYY-MM-DD-title.html` (depth 1). Strict naming — `blog-nav.js` parses by sort order.
- **Back-link convention:** `<a href="../blog.html" class="back-link">&larr; back to blog</a>`. Never `javascript:history.back()`.
- **Content format:** Clean HTML only. No Medium export markup (`graf` classes, `section` wrappers, UUID `name`/`id` attributes, `markup--` classes).
- Posts have boot sequence check: redirects to `../index.html` if `sessionStorage.nuBlogBootFinished !== 'true'`.

### 4.4 Builds+
- **Index:** `blog/builds/index.html` (depth 2, `data-base="../.."`), linked from header nav and `js/gallery-data.js`.
- **Project pages:** `blog/builds/<slug>.html` — one per project/machine (17 total including index). All depth 2.
- **Images:** `images/builds/` — project thumbnail images. Match slug naming convention.
- **Grid pattern:** `.builds-grid` with `.big-link-box` cards using `background-image: url(...)` inline.
- **Sections:** machines (6) / llm + ai (3) / projects + services + other (7).
- **Templates:** Machine pages have inlined spec-box CSS. Project pages use `.blog-post-content`. Use `scripts/new-page.py` to scaffold.

### 4.5 Image Directories
- `images/badges/` — retro Neocities web badges (about.html)
- `images/blog/` — images embedded in blog posts
- `images/builds/` — builds+ card thumbnails
- `images/cameras/` — camera gallery source images
- `images/galleries/` — gallery index card preview images
- `images/monthly/YYYY/MM-mmm/` — monthly gallery photos
- `images/plants/<month>/` — plant progress photos
- `images/benchmarking/` — LLM benchmark chart PNGs
- `images/animals/` — animal photos (some used as builds card placeholders)
- `images/water.gif` — site-wide animated background (signature element)

### 4.6 All-Images & Sitemap
- `all-images.html` and `js/sitemap-data.js` are **auto-generated** — see §2.4.
- `sitemap.html` has a hand-maintained nav bar synced with `partials/header.html`.

---

## 5. Directory Map

```
/
├── index.html, about.html, blog.html, galleries.html, plants.html, guestbook.html, sitemap.html
├── all-images.html              ← AUTO-GENERATED (do not hand-edit)
├── CLAUDE.md, README.md, agents-wiki.md, robots.txt, .nojekyll, favicon.ico
├── blog/
│   ├── 19 posts, YYYY-MM-DD-title.html (depth 1)
│   └── builds/                  project/machine pages + index.html (depth 2, 17 pages)
├── galleries/
│   ├── animals.html             animal photo collection (depth 1)
│   ├── videos.html              YouTube embeds (depth 1)
│   ├── cameras/                 per-camera pages (depth 2)
│   └── monthly/                 YYYY-MM-monthname.html (depth 2, auto-generated grids)
├── plants/
│   ├── collection.html          current plants gallery (depth 1)
│   └── progress/                2026-MM.html monthly progress pages (depth 2)
├── images/
│   ├── badges/                  retro Neocities web badges (about.html)
│   ├── blog/                    images embedded in blog posts
│   ├── builds/                  project thumbnails
│   ├── cameras/                 camera gallery source images
│   ├── galleries/               gallery index card preview images
│   ├── monthly/YYYY/MM-monthname/
│   ├── plants/jan/, feb/, mar/, apr/
│   ├── animals/
│   ├── benchmarking/            LLM benchmark chart PNGs
│   └── water.gif                site-wide animated background
├── js/
│   ├── include.js               partial loader + data-base validation + chain bootstrapper
│   ├── bot-blocker.js, counter.js, oneko.js, blog-nav.js
│   ├── gallery.js, gallery-data.js
│   └── sitemap-data.js          ← AUTO-GENERATED
├── partials/                    header.html, footer.html (use %BASE% only)
├── scripts/
│   ├── build-sitemap.py         §2.4
│   └── new-page.py              scaffold generator §2.5
└── styles/
    └── style.css                single source of styling
```

---

## 6. The "Agent Manifesto"

1. **Path calculation by depth.** `data-base` is the relative path from the file *to the site root*:
   - Root (`index.html`, `plants.html`): `data-base="."`
   - Depth 1 (`blog/foo.html`, `plants/collection.html`, `galleries/animals.html`): `data-base=".."`
   - Depth 2 (`galleries/monthly/2025-05-may.html`, `blog/builds/mycelium.html`, `plants/progress/2026-04.html`): `data-base="../.."`
   - `include.js` validates `data-base` at runtime and warns on mismatch.
2. **Never hand-edit auto-generated files.** That means `js/sitemap-data.js`, `all-images.html`, and the `blogPosts` block in `js/blog-nav.js`, the `blog-list` block in `blog.html`, and the `gallery-grid` blocks in `galleries/monthly/*.html`. All between `AUTOGEN-START` / `AUTOGEN-END` markers. Run `python3 scripts/build-sitemap.py` instead.
3. **Lazy load images and iframes.** Every `<img>` and `<iframe>` needs `loading="lazy"`.
4. **In-page `<style>` blocks are acceptable** for single-page-specific CSS (boot sequence, builds-grid, spec-box, blog-pinned). Global styles go in `styles/style.css`.
5. **Partials.** Never hardcode paths in `partials/header.html` or `partials/footer.html` — always `%BASE%`.
6. **Back-links.** Blog posts: `<a href="../blog.html" class="back-link">`. Builds pages: `<a href="index.html" class="back-link">`. Plants progress (depth 2): `<a href="../../plants.html" class="back-link">`. Gallery pages: `<a href="../../galleries.html" class="back-link">`. Never `javascript:history.back()`.
7. **Boot check.** Blog posts include the `sessionStorage` boot guard and redirect to `../index.html` if the user hasn't booted.
8. **Git awareness.** Don't commit unless asked. Respect `.gitignore`.
9. **Builds+ cards.** `.big-link-box` cards set their thumbnail via `background-image` inline on the `<a>` tag. Do not use `<img>` inside `.big-link-box`.
10. **Use the scaffold script** (`scripts/new-page.py`) for new pages. It generates correct boilerplate with proper depth, data-base, and back-links.

---

## 7. QA Checklist (run mentally before claiming done)

- [ ] **Path check:** No leading `/` in asset paths. `data-base` matches file depth (§6.1).
- [ ] **Build script:** Ran `python3 scripts/build-sitemap.py` if any HTML, image, or blog post was added/moved/removed.
- [ ] **Include check:** `<script src="…/js/include.js" …>` present at end of `<body>`; `#site-header` and `#site-footer` divs both exist.
- [ ] **Back-link check:** Blog posts use `../blog.html`. Plants progress uses `../../plants.html`. Gallery pages use `../../galleries.html`. No `history.back()` anywhere.
- [ ] **Boot check:** Blog post redirects to `../index.html` when `sessionStorage.nuBlogBootFinished !== 'true'`.
- [ ] **Alt text:** All images have meaningful `alt` attributes (no `alt="x"`).
- [ ] **Lazy loading:** All `<img>` and `<iframe>` have `loading="lazy"`.
- [ ] **Bot defense intact:** Did not remove or weaken `js/bot-blocker.js` or `robots.txt`.
- [ ] **Link check:** No broken relative paths to CSS, JS, images, or other pages.
