# nuBlog — Project CLAUDE.md

See `agents-wiki.md` for the full technical reference (architecture, directory map, agent manifesto, QA checklist).

## Quick Rules

- Static site, zero frameworks. Vanilla HTML/CSS/JS only.
- Never hand-edit auto-generated files: `js/sitemap-data.js`, `all-images.html`, `js/blog-nav.js` (the `AUTOGEN` block). Run `python3 scripts/build-sitemap.py` instead.
- All HTML files carry `<meta name="robots" content="noai, noimageai">` in `<head>`. The `build-sitemap.py` template also includes it for auto-generated pages.
- Use `%BASE%` (never hardcoded paths) inside `partials/header.html` and `partials/footer.html`.
- `data-base` must match file depth: root = `.`, depth-1 = `..`, depth-2 = `../..`.
- All `<img>` tags and `<iframe>` tags need `loading="lazy"`.
- Blog posts use `<a href="../blog.html" class="back-link">` — never `javascript:history.back()`.
- Plants progress pages (depth 2) use `<a href="../../plants.html" class="back-link">`.
- Do not commit unless explicitly asked.
- `corbin-style-guide.md`, `corbin-style-guide-builds.md`, `nublogv2.1 full changes.md`, and all audit `.md` files are gitignored — do not commit or reference them publicly.

## Key Directories

| Path | Purpose |
|------|---------|
| `blog/builds/` | Builds+ project pages (depth 2, 17 pages) |
| `images/builds/` | Thumbnails for builds+ cards |
| `images/badges/` | Retro Neocities web badges (about.html) |
| `images/blog/` | Images embedded in blog posts |
| `images/galleries/` | Gallery index card preview images |
| `images/benchmarking/` | LLM benchmark chart PNGs |
| `partials/` | Shared header/footer (use `%BASE%` only) |
| `js/gallery-data.js` | Source of truth for gallery grid cards |
| `scripts/build-sitemap.py` | Only build step — run after adding pages/images |
| `scripts/new-page.py` | Scaffold generator for new pages |

## Builds+ Section (`blog/builds/`)

### Structure
- **Index page:** `blog/builds/index.html` — grid of `.big-link-box` cards grouped into three sections:
  1. **machines** — hardware builds (macbook pro 2026, macbook pro 2021, mac pro 2013, macbook air 2014, linux box 2014, raspi3)
  2. **llm + ai** — AI/ML projects (mycelium, nuLLM, lumen + acre)
  3. **projects + services + other** — everything else (navidrome, calibre, ipod, apple music toolkit, misc+, tvwishes, this site)
- **Project pages:** `blog/builds/<slug>.html` — one per project/machine (17 total including index)
- All builds pages are depth-2: `data-base="../.."`, CSS/JS paths use `../../`

### Page Templates (use these patterns when adding new builds pages)
Use `python3 scripts/new-page.py -t builds-machine -T "Title"` or `-t builds-project` to scaffold.

**Machine page** (has spec-box): macbook-pro-2026, macbook-pro-2021, mac-pro-2013, macbook-air-2014, linux-box-2014, raspi3
- Hero image + `.spec-box` table (hostname/model, cpu, ram, storage, os, services/role)
- Spec-box CSS is inlined in `<style>` block (same 7-rule block on every machine page — do not extract to style.css, keep it per-page for independence)

**Project page** (text-only or image + text): mycelium, nullm, misc-plus, this-site, neocities-tcwishes, apple-music-toolkit, navidrome, calibre, lumen-acre
- Hero image (optional) + `.blog-post-content` div with paragraphs
- Some use `<br><hr><br>` separators between sub-projects (misc-plus, lumen-acre)

**Gallery page** (image grid + text): ipod
- Uses `.gallery-grid` + `.gallery-grid-item` for photo grids
- Multiple gallery grids can appear in one page (ipod has two)

### Adding a New Build Page
1. Scaffold: `python3 scripts/new-page.py -t builds-project -T "Title"`
2. Add a thumbnail to `images/builds/` (compress if >1 MB — see Image Compression Policy)
3. Add a `.big-link-box` card to `blog/builds/index.html` in the correct section
4. Card format: `<a class="big-link-box" href="<slug>.html" style="background-image: url('../../images/builds/<thumb>')"><span>label</span></a>`
5. Run `python3 scripts/build-sitemap.py`

### Image Naming
- Thumbnail images in `images/builds/` should match the page slug (e.g., `macbook-pro-2026.jpg` for `macbook-pro-2026.html`)
- **Verify image filenames match their content.** If a file is named `navidrome.jpg` it should actually be a navidrome screenshot, not a calibre screenshot. If filenames and content are mismatched, rename the files — do not swap the HTML references to accommodate wrong filenames.
- Some pages use images from other directories (e.g., `images/animals/`) as placeholders — this is acceptable but prefer `images/builds/` when a proper thumbnail exists

### Content Style
- First person, casual, lowercase when it feels right
- No code blocks, no technical documentation — these are personal build notes, not manuals
- Date format in `.blog-post-date`: `Month Year — status` (e.g., "April 2026 — active", "January 2025 — running", "August 2022 — traded in")
- Status values: active, running, wip, deprecated, proof of concept, planning, intermittent, present
- Back link on every project page: `<a href="index.html" class="back-link">&larr; back to builds+</a>`

## Gallery Pages

### Monthly Galleries
- Grid content is **auto-generated** by `build-sitemap.py` from `images/monthly/YYYY/MM-mmm/`
- Drop photos in the directory, run the build script — the gallery HTML updates automatically
- Orientation is auto-detected: horizontal photos first, separator `<div>`, then vertical photos
- Empty months show "no photos this month" placeholder
- Page headers (title, description, back-link) remain hand-editable — only grid content between `AUTOGEN-START/END gallery-grid` markers is auto-generated

### Camera Galleries
- Hub pages (canon-sd400.html, vivitar-pz3090.html) link to year/location sub-pages
- Sub-pages contain hand-authored image grids with captions

## Blog Posts
- Blog posts use **clean HTML** — no Medium export markup (`graf` classes, `section` wrappers, UUID attributes)
- Back-link: `<a href="../blog.html" class="back-link">&larr; back to blog</a>`
- All blog posts have the boot sequence check (`sessionStorage.nuBlogBootFinished`) — redirects to `../index.html` on first visit
- Post list on `blog.html` is **auto-generated** by `build-sitemap.py` from `blog/` directory

## Sitemap
- `sitemap.html` has a hand-maintained nav bar at the top — add new top-level sections there
- Current nav links: home, photos, blog, builds+, plants, about (must match `partials/header.html`)
- The tree itself is auto-generated from `js/sitemap-data.js` (run `build-sitemap.py` to update)

## Header Navigation
- `partials/header.html` nav order: home → photos → blog → builds → plants → about
- Always use `%BASE%` prefix for nav links

## Build Script Features
`python3 scripts/build-sitemap.py` now handles:
- Sitemap data generation (`js/sitemap-data.js`)
- All-images flat page (`all-images.html`)
- Blog navigation array (`js/blog-nav.js`)
- Blog listing page (`blog.html` — auto-generates from filesystem)
- Monthly gallery grids (`galleries/monthly/*.html` — auto-generates from `images/monthly/`)
- Image size warnings (flags files >1 MB during build)
- Agent doc exclusion (11 audit/agent `.md` files excluded from sitemap)

## Scaffold Script
`python3 scripts/new-page.py --type blog|builds-project|builds-machine|monthly-gallery --title "Title" [--date "Month Year"] [--filename filename.html]`

## Image Compression Policy

Before committing new images, compress any file over **1 MB**. Target: max 2400px on the long edge, JPEG quality 78.

Quick one-liner to check and compress all over-threshold images:

```python
python3 << 'EOF'
from PIL import Image
import os

THRESHOLD = 1 * 1024 * 1024
MAX_DIM = 2400
QUALITY = 78

for root, _, files in os.walk("images"):
    for fname in files:
        if not fname.lower().endswith(('.jpeg', '.jpg')):
            continue
        path = os.path.join(root, fname)
        if os.path.getsize(path) < THRESHOLD:
            continue
        with Image.open(path) as img:
            exif = img.info.get('exif', b'')
            rgb = img.convert('RGB') # handles RGBA safely
            w, h = rgb.size
            if max(w, h) > MAX_DIM:
                r = MAX_DIM / max(w, h)
                rgb = rgb.resize((int(w*r), int(h*r)), Image.LANCZOS)
            kw = dict(quality=QUALITY, optimize=True)
            if exif:
                kw['exif'] = exif
            rgb.save(path, 'JPEG', **kw)
            print(f"compressed {path}")
EOF
```

- Run from the repo root.
- Always use `img.convert('RGB')` before saving as JPEG — PIL will error on RGBA files otherwise and may corrupt the file on disk.
- Images under 1 MB are already web-appropriate; don't touch them.

## Content Date

Current date context: 2026-04-29.
