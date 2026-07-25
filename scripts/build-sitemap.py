#!/usr/bin/env python3
"""Build generated site data and monthly gallery markup from the filesystem.

Run from repo root:  python3 scripts/build-sitemap.py
"""
import json
import re
from datetime import datetime, timedelta
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlparse

from PIL import ExifTags, Image

ROOT = Path(__file__).parent.parent.resolve()
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.remember', '.DS_Store', 'node_modules',
    'scripts', 'tests', 'docs', 'partials', 'archive',
}
EXCLUDE_FILES = {
    'AGENTS.md', 'CLAUDE.md', 'agents-wiki.md',
    'HANDOFF.md',
}
BLOG_FEED_EXCLUDE = {'2025-09-04-review-books-i-have-read-2023-2024-2025.html'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
PHOTO_EXTS = {'.jpg', '.jpeg', '.png'}
MB = 1024 * 1024
IMAGE_SIZE_WARNING_EXCLUDE = {Path('images/water.gif')}
THUMB_DIR_NAME = '.thumbs'  # under images/, mirrors layout; consumed by the canvas page
THUMB_LONG_EDGE = 400
THUMB_QUALITY = 70
# Card backgrounds are a second, larger tier. The canvas shows a thumb at ~150px
# so 400/q70 is plenty there, but a .big-link-box renders at ~230px and the
# blog.html strip spans the full 958px column — at 400px those were visibly soft
# on any retina display, and there is no hi-res swap behind them.
CARD_DIR_NAME = '.cards'
CARD_LONG_EDGE = 800
CARD_QUALITY = 82
# WebP, not JPEG: measured across all card images at the size they actually
# render, WebP q82 is both ~26% smaller AND higher fidelity than JPEG q82.
# It is strictly the better trade, so the tier does not use JPEG at all.
CARD_FORMAT = 'WEBP'
CARD_EXT = '.webp'
# Filenames may contain spaces ("plants/mar/canon - 1.webp"), so stop at the
# quote or paren that closes the url()/attribute rather than at whitespace.
CARD_REF_RE = re.compile(r'images/\.cards/([^\'"()\n]+)\.webp')
EXIF_TAGS = {value: key for key, value in ExifTags.TAGS.items()}
CAPTURE_DATE_TAGS = ('DateTimeOriginal', 'DateTimeDigitized', 'DateTime')
IDG_NAME_RE = re.compile(r'^IDG_(\d{8})_(\d{6})(?:_\d+)?', re.IGNORECASE)
IMG_NAME_RE = re.compile(r'^IMG_(\d+)', re.IGNORECASE)
MONTH_DAY_NAME_RE = re.compile(r'^[a-z]{3}-([0-9]{2})$', re.IGNORECASE)
MONTHLY_SECTION_ORDER = {
    'pre-trip': 0,
    'chicago': 1,
    'great-lakes-ohio': 2,
    'appalachia': 3,
    'east-coast': 4,
}
MONTHLY_SECTION_LABELS = {
    'pre-trip': 'pre-trip',
    'chicago': 'chicago',
    'great-lakes-ohio': 'great lakes, indiana, michigan, ohio',
    'appalachia': 'appalachia',
    'east-coast': 'east coast',
}


def parse_exif_datetime(value):
    """Parse EXIF datetime strings such as YYYY:MM:DD HH:MM:SS."""
    if not value:
        return None
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='ignore')
    text = str(value).strip()
    if len(text) < 19:
        return None
    try:
        return datetime.strptime(text[:19], '%Y:%m:%d %H:%M:%S')
    except ValueError:
        return None


def image_capture_datetime(path: Path):
    """Return the best capture datetime embedded in an image, if present."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
        for tag_name in CAPTURE_DATE_TAGS:
            dt = parse_exif_datetime(exif.get(EXIF_TAGS.get(tag_name)))
            if dt:
                return dt
    except Exception:
        return None
    return None


def duplicate_capture_datetime(path: Path, year: str):
    """Find capture time from a same-named camera original when a gallery copy lost EXIF."""
    cameras_dir = ROOT / 'images' / 'cameras'
    if not cameras_dir.is_dir():
        return None
    for candidate in sorted(cameras_dir.glob(f'*/{year}/{path.name}')):
        if candidate == path:
            continue
        dt = image_capture_datetime(candidate)
        if dt:
            return dt
    return None


def filename_capture_datetime(path: Path, year: str, month_num: str):
    """Infer month-gallery ordering from timestamped names or stable IMG sequences."""
    match = IDG_NAME_RE.match(path.stem)
    if match:
        try:
            return datetime.strptime(''.join(match.groups()), '%Y%m%d%H%M%S')
        except ValueError:
            return None

    match = MONTH_DAY_NAME_RE.match(path.stem)
    if match:
        try:
            return datetime(int(year), int(month_num), int(match.group(1)), 12, 0, 0)
        except ValueError:
            return None

    match = IMG_NAME_RE.match(path.stem)
    if match:
        try:
            return datetime(int(year), int(month_num), 1) + timedelta(seconds=int(match.group(1)))
        except ValueError:
            return None

    return None


def monthly_sort_key(path: Path, year: str, month_num: str):
    dt = (
        image_capture_datetime(path)
        or duplicate_capture_datetime(path, year)
        or filename_capture_datetime(path, year, month_num)
    )
    if dt:
        return (0, dt, path.name.lower())
    return (1, path.name.lower())


def monthly_section_sort_key(path: Path):
    return (MONTHLY_SECTION_ORDER.get(path.name, 100), path.name.lower())


def monthly_section_label(path: Path):
    if path.name in MONTHLY_SECTION_LABELS:
        return MONTHLY_SECTION_LABELS[path.name]
    return path.name.replace('-', ' ')


def monthly_gallery_item(img_file: Path, alt_text: str):
    try:
        with Image.open(img_file) as img:
            width, height = img.size
            orient = img.getexif().get(EXIF_TAGS.get('Orientation'), 1)
        if orient in (5, 6, 7, 8):
            width, height = height, width
        rel_path = img_file.relative_to(ROOT)
        return (
            f'            <div class="gallery-grid-item">'
            f'<img src="../../{rel_path}" alt="{escape(alt_text, quote=True)}"'
            f' width="{width}" height="{height}"'
            f' class="styled-image" loading="lazy"></div>'
        )
    except Exception:
        return None


def monthly_gallery_grid(items):
    if items:
        body = '\n'.join(items)
    else:
        body = (
            '            <p style="grid-column: 1 / -1; color: #666;">'
            'no photos this month</p>'
        )
    return (
        '        <div class="gallery-grid">\n'
        f'{body}\n'
        '        </div>'
    )


def build_tree(path: Path):
    """Recursively build a tree of files and folders."""
    result = {"files": [], "folders": {}}

    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return result

    for entry in entries:
        if entry.name.startswith('.') and entry.name != '.nojekyll':
            continue

        if entry.is_dir():
            if entry.name in EXCLUDE_DIRS:
                continue
            in_images = (
                'images' in [p.name for p in entry.parents] or entry.name == 'images'
            )
            if in_images:
                loose_files = [
                    e.name
                    for e in sorted(entry.iterdir())
                    if e.is_file() and not e.name.startswith('.')
                ]
                subdirs = [
                    d.name + '/'
                    for d in sorted(entry.iterdir())
                    if d.is_dir() and not d.name.startswith('.')
                ]
                files = loose_files + subdirs
                result["folders"][entry.name] = {
                    "files": files if files else ["(image files)"],
                    "note": "(image directory)",
                }
            else:
                subtree = build_tree(entry)
                result["folders"][entry.name] = subtree
        else:
            if entry.name in EXCLUDE_FILES:
                continue
            result["files"].append(entry.name)

    return result


def render_derivative(src_path: Path, out_dir_name: str, long_edge: int, quality: int,
                      fmt: str = 'JPEG', ext: str = '.jpg'):
    """Resize src_path into images/<out_dir_name>/, mirroring its path.

    Returns the repo-rel path of the derivative, or None to signal 'use the
    source'. Skips regeneration when the derivative is newer than the source.
    """
    if src_path.suffix.lower() == '.svg':
        return None  # PIL can't rasterize SVG; let the caller use the original
    rel = src_path.relative_to(ROOT / 'images')
    out = ROOT / 'images' / out_dir_name / rel.with_suffix(ext)
    if out.is_file() and out.stat().st_mtime >= src_path.stat().st_mtime:
        return str(out.relative_to(ROOT)).replace('\\', '/')
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(src_path) as im:
            im = im.convert('RGB')
            w, h = im.size
            if max(w, h) > long_edge:
                ratio = long_edge / max(w, h)
                im = im.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.LANCZOS)
            opts = {'method': 6} if fmt == 'WEBP' else {'optimize': True}
            im.save(out, fmt, quality=quality, **opts)
        return str(out.relative_to(ROOT)).replace('\\', '/')
    except Exception as e:
        print(f"  {out_dir_name} render failed for {src_path.name}: {e}")
        return None


def ensure_thumb(src_path: Path):
    """Canvas-sized thumbnail mirror of src_path under images/.thumbs/."""
    return render_derivative(src_path, THUMB_DIR_NAME, THUMB_LONG_EDGE, THUMB_QUALITY)


def ensure_card(src_path: Path):
    """Card-sized derivative of src_path under images/.cards/."""
    return render_derivative(src_path, CARD_DIR_NAME, CARD_LONG_EDGE, CARD_QUALITY,
                             CARD_FORMAT, CARD_EXT)


def find_image_source(stem_rel: str):
    """Resolve 'builds/navidrome' to the real images/builds/navidrome.<ext>."""
    for ext in sorted(IMAGE_EXTS):
        for candidate in (ext, ext.upper()):
            path = ROOT / 'images' / (stem_rel + candidate)
            if path.is_file():
                return path
    return None


def build_card_thumbs():
    """Build images/.cards/ from the paths the markup actually asks for.

    The markup is the source of truth here: whatever `images/.cards/<path>.jpg`
    a page references, this renders from the matching original under images/.
    That keeps the big tier scoped to the few dozen images used as card
    backgrounds instead of mirroring all ~1500 images at 800px.
    """
    wanted = {}
    for path in sorted(ROOT.rglob('*')):
        if path.suffix.lower() not in {'.html', '.js'} or not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS or part.startswith('.') for part in path.relative_to(ROOT).parts[:-1]):
            continue
        for stem in CARD_REF_RE.findall(path.read_text()):
            wanted.setdefault(stem, []).append(str(path.relative_to(ROOT)))

    missing = []
    built = 0
    for stem, referrers in sorted(wanted.items()):
        src = find_image_source(stem)
        if src is None:
            missing.append(f'{stem} (referenced by {referrers[0]})')
            continue
        out = ROOT / 'images' / CARD_DIR_NAME / (stem + CARD_EXT)
        existed = out.is_file() and out.stat().st_mtime >= src.stat().st_mtime
        if ensure_card(src) and not existed:
            built += 1

    if missing:
        raise RuntimeError(
            f'{len(missing)} card background(s) have no source image: ' + ', '.join(missing)
        )

    # Compare the full filename, not the stem: a tier that changes format leaves
    # same-stem files from the old one behind, and those must go too.
    expected = {stem + CARD_EXT for stem in wanted}
    pruned = 0
    cards_dir = ROOT / 'images' / CARD_DIR_NAME
    if cards_dir.is_dir():
        for card in sorted(cards_dir.rglob('*')):
            if card.is_file() and str(card.relative_to(cards_dir)) not in expected:
                card.unlink()
                pruned += 1

    parts = [f'{len(wanted)} card images']
    if built:
        parts.append(f'{built} rebuilt')
    if pruned:
        parts.append(f'{pruned} pruned')
    print(f'Card thumbs at {CARD_LONG_EDGE}px/q{CARD_QUALITY} (' + ', '.join(parts) + ')')


def prune_stale_thumbs():
    """Delete thumbs under images/.thumbs/ whose source image no longer exists."""
    thumbs_dir = ROOT / 'images' / THUMB_DIR_NAME
    if not thumbs_dir.is_dir():
        return
    pruned = 0
    for thumb in sorted(thumbs_dir.rglob('*')):
        if not thumb.is_file():
            continue
        rel = thumb.relative_to(thumbs_dir)
        # Thumbs are always .jpg; the source may have any image extension.
        source_exists = any(
            (ROOT / 'images' / rel.with_suffix(ext)).is_file()
            for ext in IMAGE_EXTS | {ext.upper() for ext in IMAGE_EXTS}
        )
        if not source_exists:
            thumb.unlink()
            pruned += 1
    if pruned:
        print(f"Pruned {pruned} stale thumb(s) from images/{THUMB_DIR_NAME}/")


def build_all_images_data():
    """Scan images/ and emit js/all-images-data.js as [path, w, h, thumb] tuples.

    Pre-generates 400px-on-long-edge JPEG thumbnails under images/.thumbs/ so the
    canvas page loads small files instead of full-resolution originals.
    """
    images_dir = ROOT / 'images'
    if not images_dir.is_dir():
        print("images/ directory not found, skipping all-images-data.js")
        return
    prune_stale_thumbs()

    entries = []
    skipped = 0
    thumbs_built = 0
    for img in sorted(images_dir.rglob('*')):
        if not (img.is_file() and img.suffix.lower() in IMAGE_EXTS):
            continue
        if THUMB_DIR_NAME in img.parts or CARD_DIR_NAME in img.parts:
            continue  # never include generated derivatives in the data array
        rel = str(img.relative_to(ROOT)).replace('\\', '/')
        try:
            with Image.open(img) as im:
                w, h = im.size
        except Exception as e:
            print(f"  skipped {rel}: {e}")
            skipped += 1
            continue
        thumb_exists_before = False
        thumb_path_obj = ROOT / 'images' / THUMB_DIR_NAME / img.relative_to(ROOT / 'images').with_suffix('.jpg')
        if thumb_path_obj.is_file():
            thumb_exists_before = thumb_path_obj.stat().st_mtime >= img.stat().st_mtime
        thumb_rel = ensure_thumb(img) or rel
        if not thumb_exists_before and thumb_rel != rel:
            thumbs_built += 1
        entries.append((rel, w, h, thumb_rel))

    if not entries:
        print("No images found, skipping all-images-data.js")
        return

    items = ',\n    '.join(
        f'[{json.dumps(p)}, {w}, {h}, {json.dumps(t)}]'
        for p, w, h, t in entries
    )
    js = (
        "// AUTO-GENERATED by scripts/build-sitemap.py — do not edit.\n"
        "// Each entry: [src, width, height, thumbSrc]\n"
        "window.allImagesData = [\n"
        f"    {items}\n"
        "];\n"
    )
    out = ROOT / 'js' / 'all-images-data.js'
    out.write_text(js)
    parts = [f"{len(entries)} images"]
    if thumbs_built:
        parts.append(f"{thumbs_built} new thumbs")
    if skipped:
        parts.append(f"{skipped} skipped")
    print(f"Generated {out} (" + ", ".join(parts) + ")")


def build_blog_nav():
    """Rewrite the blogPosts array in js/blog-nav.js between AUTOGEN markers."""
    blog_dir = ROOT / 'blog'
    nav_path = ROOT / 'js' / 'blog-nav.js'
    if not blog_dir.is_dir() or not nav_path.is_file():
        print("blog/ or js/blog-nav.js missing, skipping blog-nav update")
        return

    # Only dated posts (YYYY-MM-DD-*) belong in the prev/next chain; rolling
    # pages stay out of it (but remain linked elsewhere).
    posts = sorted(
        (p.name for p in blog_dir.iterdir()
         if p.is_file() and p.suffix == '.html' and not p.name.startswith('.')
         and p.name not in BLOG_FEED_EXCLUDE
         and re.match(r'\d{4}-\d{2}-\d{2}-', p.name)),
        reverse=True,
    )
    body = ',\n'.join(f'        "{name}"' for name in posts)
    replacement = (
        "    // AUTOGEN-START blogPosts — populated by scripts/build-sitemap.py\n"
        "    var blogPosts = [\n"
        f"{body}\n"
        "    ];\n"
        "    // AUTOGEN-END blogPosts"
    )
    pattern = re.compile(
        r"    // AUTOGEN-START blogPosts.*?    // AUTOGEN-END blogPosts",
        re.DOTALL,
    )
    original = nav_path.read_text()
    if not pattern.search(original):
        print(f"AUTOGEN markers not found in {nav_path}, skipping")
        return
    nav_path.write_text(pattern.sub(replacement, original))
    print(f"Updated {nav_path} ({len(posts)} blog posts)")


def build_blog_list():
    """Rewrite the blog list in blog.html between AUTOGEN markers."""
    blog_dir = ROOT / 'blog'
    blog_html_path = ROOT / 'blog.html'
    if not blog_dir.is_dir() or not blog_html_path.is_file():
        print("blog/ or blog.html missing, skipping blog list update")
        return

    posts = []
    title_pattern = re.compile(r'<title>(.*?) - nuBlog</title>')

    for p in sorted(blog_dir.iterdir()):
        if not p.is_file() or p.suffix != '.html' or p.name.startswith('.') or p.name in BLOG_FEED_EXCLUDE:
            continue
        try:
            date_str = p.name[:10]
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            date_formatted = dt.strftime('%B %d, %Y').replace(' 0', ' ')
        except ValueError:
            continue

        content = p.read_text()
        match = title_pattern.search(content)
        if match:
            title = match.group(1)
        else:
            title = p.stem

        posts.append((p.name, title, date_formatted, dt))

    if not posts:
        print("No dated blog posts found, skipping blog list update")
        return

    posts.sort(key=lambda x: (x[3], x[0]), reverse=True)

    # data-added drives the '*new!' badge; js/whats-new.js picks the newest and
    # drops it once it ages out, so the flag is never stale.
    items = '\n'.join(
        f'            <div class="blog-item" data-added="{dt.strftime("%Y-%m-%d")}">'
        f'<a href="blog/{filename}">{title}</a>'
        f' <span class="blog-item-date">{date_formatted}</span></div>'
        for filename, title, date_formatted, dt in posts
    )

    replacement = (
        "    <!-- AUTOGEN-START blog-list — populated by scripts/build-sitemap.py -->\n"
        f"{items}\n"
        "    <!-- AUTOGEN-END blog-list -->"
    )

    pattern = re.compile(
        r"    <!-- AUTOGEN-START blog-list.*?    <!-- AUTOGEN-END blog-list -->",
        re.DOTALL,
    )
    original = blog_html_path.read_text()
    if not pattern.search(original):
        print(f"AUTOGEN markers not found in {blog_html_path}, skipping")
        return
    blog_html_path.write_text(pattern.sub(replacement, original))
    print(f"Updated {blog_html_path} ({len(posts)} blog posts)")


def build_homepage_recent_blog():
    """Keep the homepage's recent blog card synced to the newest dated post."""
    index_path = ROOT / 'index.html'
    blog_dir = ROOT / 'blog'
    if not index_path.is_file() or not blog_dir.is_dir():
        return

    posts = sorted(
        (
            path for path in blog_dir.glob('*.html')
            if re.match(r'\d{4}-\d{2}-\d{2}-', path.name)
            and path.name not in BLOG_FEED_EXCLUDE
        ),
        key=lambda path: path.name,
        reverse=True,
    )
    if not posts:
        return

    latest = posts[0]
    content = latest.read_text()
    title_match = re.search(r'<title>(.*?) - nuBlog</title>', content)
    title = unescape(title_match.group(1)) if title_match else latest.stem
    date = datetime.strptime(latest.name[:10], '%Y-%m-%d')

    og_match = re.search(
        r'<meta\s+property="og:image"\s+content="([^"]+)"',
        content,
        re.IGNORECASE,
    )
    source_path = 'images/badges/reshirii.gif'
    thumb_path = f'images/{CARD_DIR_NAME}/badges/reshirii{CARD_EXT}'
    if og_match:
        raw_src = og_match.group(1)
        if raw_src.startswith(('http://', 'https://')):
            image_rel = urlparse(raw_src).path.lstrip('/')
        else:
            image_rel = str((latest.parent / raw_src).resolve().relative_to(ROOT))
        image_path = Path(image_rel)
        if image_path.parts and image_path.parts[0] == 'images':
            # Render the card here rather than testing for it: a brand new post
            # brings a brand new og:image, which has never been rendered before.
            rendered = ensure_card(ROOT / image_path)
            if rendered:
                source_path = image_rel
                thumb_path = rendered

    card = (
        '                    <!-- AUTOGEN-START recent-blog -->\n'
        f'                    <a class="recent-card" href="blog/{latest.name}"'
        f' data-date="{date.strftime("%Y-%m-%d")}"'
        f' data-preview-source="{escape(source_path, quote=True)}">\n'
        f'                        <div class="card-thumb" style="background-image: url(\'{thumb_path}\');"></div>\n'
        '                        <div class="card-section">blog</div>\n'
        f'                        <div class="card-text">{escape(title)}</div>\n'
        f'                        <div class="card-when">{date.month}/{date.day:02d}</div>\n'
        '                    </a>\n'
        '                    <!-- AUTOGEN-END recent-blog -->'
    )
    pattern = re.compile(
        r'                    <!-- AUTOGEN-START recent-blog -->.*?'
        r'                    <!-- AUTOGEN-END recent-blog -->',
        re.DOTALL,
    )
    original = index_path.read_text()
    if not pattern.search(original):
        print(f"AUTOGEN recent-blog markers not found in {index_path}, skipping")
        return
    index_path.write_text(pattern.sub(card, original))
    print(f"Updated {index_path} recent blog card ({latest.name})")


def sort_homepage_recent_cards():
    """Order the homepage 'recent' strip newest-first.

    The cards are hand-authored (except the blog one) and were drifting out of
    order as sections got updated at different times. Sorting here by
    data-date means adding a card anywhere in the list self-corrects on the
    next build instead of silently sitting in the wrong place.
    """
    index_path = ROOT / 'index.html'
    if not index_path.is_file():
        return
    text = index_path.read_text()

    open_tag = '<div class="recent-cards">'
    start = text.find(open_tag)
    if start == -1:
        print("recent-cards container not found, skipping sort")
        return
    body_start = start + len(open_tag)

    # walk to the matching close so we never depend on fixed indentation
    depth, i = 1, body_start
    for m in re.finditer(r'<(/?)div\b', text[body_start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            i = body_start + m.start()
            break
    else:
        print("unbalanced recent-cards container, skipping sort")
        return
    body = text[body_start:i]

    # a unit is one card, plus the AUTOGEN comment pair when it has one
    unit_re = re.compile(
        r'[ \t]*(?:<!-- AUTOGEN-START recent-blog -->\s*)?'
        r'<a class="recent-card".*?</a>'
        r'(?:\s*<!-- AUTOGEN-END recent-blog -->)?',
        re.DOTALL,
    )
    units = [m.group(0).strip('\n') for m in unit_re.finditer(body)]
    if len(units) < 2:
        return

    undated = [u for u in units if 'data-date="' not in u]
    if undated:
        print(f"WARNING: {len(undated)} recent card(s) missing data-date, leaving order alone")
        return

    def key(unit):
        return re.search(r'data-date="([\d-]+)"', unit).group(1)

    ordered = sorted(units, key=key, reverse=True)
    if ordered == units:
        return

    rebuilt = '\n' + '\n'.join(ordered) + '\n                '
    index_path.write_text(text[:body_start] + rebuilt + text[i:])
    print(f"Sorted {index_path} recent cards newest-first ({len(ordered)} cards)")


def build_monthly_galleries():
    """Auto-generate monthly gallery grids from images/monthly/ directories.

    Scans gallery pages (not image dirs) so all pages get updated, even empty months.
    """
    images_monthly = ROOT / 'images' / 'monthly'
    galleries_monthly = ROOT / 'galleries' / 'monthly'
    marker_pattern = re.compile(
        r'        <!-- AUTOGEN-START gallery-grid -->.*?        <!-- AUTOGEN-END gallery-grid -->',
        re.DOTALL,
    )

    if not galleries_monthly.is_dir():
        print("Monthly galleries dir missing, skipping")
        return

    updated = 0

    for gallery_file in sorted(galleries_monthly.glob('*.html')):
        if gallery_file.name.startswith('.'):
            continue

        original = gallery_file.read_text()
        if not marker_pattern.search(original):
            continue
        title_match = re.search(r'<h1>(.*?)</h1>', original, re.DOTALL)
        gallery_title = (
            re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            if title_match else gallery_file.stem.replace('-', ' ')
        )

        # Parse YYYY-MM from filename: 2025-01-jan.html
        stem = gallery_file.stem  # "2025-01-jan"
        parts = stem.split('-', 2)
        if len(parts) < 3:
            continue
        year, month_num, month_name = parts  # "2025", "01", "jan"

        source_match = re.search(r'<!-- AUTOGEN-SOURCE ([^>]+) -->', original)
        explicit_source = bool(source_match)
        if explicit_source:
            image_dir = ROOT / source_match.group(1).strip()
        else:
            image_dir = images_monthly / year / f'{month_num}-{month_name}'
        sections = []

        if image_dir.is_dir():
            loose_files = sorted(
                [
                    p for p in image_dir.iterdir()
                    if p.is_file()
                    and not p.name.startswith('.')
                    and p.suffix.lower() in PHOTO_EXTS
                ],
                key=lambda p: monthly_sort_key(p, year, month_num),
            )
            section_dirs = []
            if not explicit_source:
                section_dirs = sorted(
                    [
                        p for p in image_dir.iterdir()
                        if p.is_dir()
                        and not p.name.startswith('.')
                        and any(
                            child.is_file()
                            and not child.name.startswith('.')
                            and child.suffix.lower() in PHOTO_EXTS
                            for child in p.iterdir()
                        )
                    ],
                    key=monthly_section_sort_key,
                )

            if section_dirs:
                if loose_files:
                    sections.append(('unfiled', loose_files, True))
                for section_dir in section_dirs:
                    section_files = sorted(
                        [
                            p for p in section_dir.iterdir()
                            if p.is_file()
                            and not p.name.startswith('.')
                            and p.suffix.lower() in PHOTO_EXTS
                        ],
                        key=lambda p: monthly_sort_key(p, year, month_num),
                    )
                    sections.append((monthly_section_label(section_dir), section_files, True))
            else:
                sections.append(('', loose_files, False))

        blocks = []
        photo_number = 0
        for label, img_files, sectioned in sections:
            items = []
            horizontal = []
            vertical = []
            for img_file in img_files:
                photo_number += 1
                context = f'{gallery_title} photo {photo_number}'
                if label:
                    context = f'{gallery_title}, {label}, photo {photo_number}'
                item = monthly_gallery_item(img_file, context)
                if not item:
                    continue
                if sectioned:
                    items.append(item)
                    continue
                try:
                    with Image.open(img_file) as img:
                        w, h = img.size
                        orient = img.getexif().get(EXIF_TAGS.get('Orientation'), 1)
                    if orient in (5, 6, 7, 8):
                        w, h = h, w
                    if w >= h:
                        horizontal.append(item)
                    else:
                        vertical.append(item)
                except Exception:
                    continue

            if not sectioned:
                items = horizontal[:]
                if horizontal and vertical:
                    items.append(
                        '            <div style="grid-column: 1 / -1; height: 0; '
                        'margin: 0; padding: 0;"></div>'
                    )
                items.extend(vertical)

            if label:
                blocks.append(f'        <h2>{label}</h2>')
            blocks.append(monthly_gallery_grid(items))

        if not blocks:
            blocks.append(monthly_gallery_grid([]))

        grid = '\n'.join(blocks)

        replacement = (
            '        <!-- AUTOGEN-START gallery-grid -->\n'
            f'{grid}\n'
            '        <!-- AUTOGEN-END gallery-grid -->'
        )
        gallery_file.write_text(marker_pattern.sub(replacement, original))
        updated += 1

    if updated:
        print(f"Updated {updated} monthly gallery page(s)")


def enrich_image_metadata():
    """Add stable alt, width, height, and lazy-loading attributes to HTML images."""
    image_tag_pattern = re.compile(r'<img\b[^>]*>', re.IGNORECASE | re.DOTALL)
    attr_pattern = lambda name: re.compile(
        rf'(\s{name}\s*=\s*)(["\'])(.*?)\2',
        re.IGNORECASE | re.DOTALL,
    )
    filename_alt_pattern = re.compile(
        r'^(?:IMG|IDG|DSC|R1-|PXL|MVIMG|[0-9A-F]{8}-)[A-Z0-9_.\-\s]*$',
        re.IGNORECASE,
    )

    def attr_value(tag, name):
        match = attr_pattern(name).search(tag)
        return unescape(match.group(3)) if match else None

    def set_attr(tag, name, value):
        pattern = attr_pattern(name)
        rendered = escape(str(value), quote=True)
        if pattern.search(tag):
            return pattern.sub(lambda match: f'{match.group(1)}"{rendered}"', tag, count=1)
        if tag.endswith('/>'):
            return tag[:-2].rstrip() + f' {name}="{rendered}" />'
        return tag[:-1] + f' {name}="{rendered}">'

    updated_pages = 0
    updated_images = 0
    failures = []
    for page in sorted(ROOT.rglob('*.html')):
        if any(part in {'.git', 'archive', 'partials'} for part in page.parts):
            continue
        original = page.read_text()
        tags = image_tag_pattern.findall(original)
        if not tags:
            continue

        title_match = re.search(r'<h1\b[^>]*>(.*?)</h1>', original, re.IGNORECASE | re.DOTALL)
        if not title_match:
            title_match = re.search(r'<title>(.*?)</title>', original, re.IGNORECASE | re.DOTALL)
        page_title = page.stem.replace('-', ' ')
        if title_match:
            page_title = unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip()
            page_title = re.sub(r'\s+-\s+nuBlog.*$', '', page_title, flags=re.IGNORECASE)

        image_number = 0

        def update_tag(match):
            nonlocal image_number, updated_images
            tag = match.group(0)
            src = attr_value(tag, 'src')
            if not src:
                failures.append((str(page.relative_to(ROOT)), '(missing src)'))
                return tag

            image_number += 1
            if src.startswith(('https://i.ytimg.com/', 'http://i.ytimg.com/')):
                width, height = 480, 360
            elif src.startswith(('http://', 'https://', '//', 'data:')):
                failures.append((str(page.relative_to(ROOT)), src))
                return tag
            else:
                image_path = (
                    ROOT / src.lstrip('/')
                    if src.startswith('/')
                    else (page.parent / src).resolve()
                )
                if not image_path.is_file():
                    failures.append((str(page.relative_to(ROOT)), src))
                    return tag
                try:
                    with Image.open(image_path) as image:
                        width, height = image.size
                        orient = image.getexif().get(EXIF_TAGS.get('Orientation'), 1)
                    if orient in (5, 6, 7, 8):
                        width, height = height, width
                except Exception:
                    failures.append((str(page.relative_to(ROOT)), src))
                    return tag

            alt = attr_value(tag, 'alt')
            stem = Path(urlparse(src).path).stem
            decorative = '/badges/' in src or 'youtube.com/' in src or 'ytimg.com/' in src
            if alt is None:
                alt = '' if decorative else (
                    f'{page_title} photo {image_number}' if len(tags) > 1
                    else f'{page_title} photo'
                )
            elif alt and (
                alt.strip().lower() == stem.lower()
                or filename_alt_pattern.fullmatch(alt.strip())
                or re.search(r'\.(?:jpe?g|png|gif|webp)$', alt, re.IGNORECASE)
            ):
                alt = (
                    f'{page_title} photo {image_number}' if len(tags) > 1
                    else f'{page_title} photo'
                )

            rendered = set_attr(tag, 'alt', alt)
            rendered = set_attr(rendered, 'width', width)
            rendered = set_attr(rendered, 'height', height)
            rendered = set_attr(rendered, 'loading', 'lazy')
            if rendered != tag:
                updated_images += 1
            return rendered

        rendered = image_tag_pattern.sub(update_tag, original)
        if rendered != original:
            page.write_text(rendered)
            updated_pages += 1

    if failures:
        sample = ', '.join(f'{page}: {src}' for page, src in failures[:5])
        raise RuntimeError(f'Could not enrich {len(failures)} image(s): {sample}')
    print(f"Enriched image metadata ({updated_images} images across {updated_pages} pages)")


def check_image_sizes():
    """Warn about images exceeding 1 MB."""
    images_dir = ROOT / 'images'
    if not images_dir.is_dir():
        return
    oversized = []
    for img in images_dir.rglob('*'):
        if img.is_file() and img.suffix.lower() in IMAGE_EXTS:
            if THUMB_DIR_NAME in img.parts or CARD_DIR_NAME in img.parts:
                continue  # generated derivatives aren't worth warning about
            if img.relative_to(ROOT) in IMAGE_SIZE_WARNING_EXCLUDE:
                continue  # intentionally protected animation; see AGENTS.md
            size = img.stat().st_size
            if size > MB:
                oversized.append((str(img.relative_to(ROOT)), size))
    if oversized:
        print(f"WARNING: {len(oversized)} image(s) exceed 1 MB:")
        for path, size in sorted(oversized):
            print(f"  {path} ({size/MB:.1f} MB)")
    else:
        print("All images within 1 MB limit")


def main():
    tree = build_tree(ROOT)
    data = json.dumps(tree, indent=2, ensure_ascii=False)
    js = (
        "// Auto-generated by build-sitemap.py — edits will be overwritten\n"
        f"window.__SITEMAP__ = {data};\n"
    )
    out_path = ROOT / "js" / "sitemap-data.js"
    out_path.write_text(js)
    print(f"Generated {out_path} ({len(data)} bytes)")

    build_all_images_data()
    build_blog_nav()
    build_blog_list()
    build_homepage_recent_blog()
    sort_homepage_recent_cards()  # must follow: the blog card supplies its date
    build_card_thumbs()  # must follow: the recent-blog card can add a new ref
    build_monthly_galleries()
    enrich_image_metadata()
    check_image_sizes()


if __name__ == "__main__":
    main()
