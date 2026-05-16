#!/usr/bin/env python3
"""Build js/sitemap-data.js and all-images.html from filesystem scan.

Run from repo root:  python3 scripts/build-sitemap.py
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from PIL import ExifTags, Image

ROOT = Path(__file__).parent.parent.resolve()
EXCLUDE_DIRS = {'.git', '__pycache__', '.remember', '.DS_Store', 'node_modules', 'scripts', 'docs', 'partials'}
EXCLUDE_FILES = {
    'AGENTS.md', 'CLAUDE.md', 'agents-wiki.md',
    'corbin-style-guide.md', 'corbin-style-guide-builds.md',
    'audit-report-042926.md', 'audit-guide-and-review-for-deepseek.md',
    'deepseekv4proaudit.md', 'geminiflashaudit.md',
    'glm5-1audit.md', 'glm5-1auditthourough.md',
    'opusreport.md', 'qwen3.6moe-report.md',
    'ssg-migration-design.md', 'nublogv2.1 full changes.md',
    'HANDOFF.md', '2025-09-04-review-books-i-have-read-2023-2024-2025.html',
    'spotify.html',
}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
PHOTO_EXTS = {'.jpg', '.jpeg', '.png'}
MB = 1024 * 1024
THUMB_DIR_NAME = '.thumbs'  # under images/, mirrors layout; consumed by the canvas page
THUMB_LONG_EDGE = 400
THUMB_QUALITY = 70
EXIF_TAGS = {value: key for key, value in ExifTags.TAGS.items()}
CAPTURE_DATE_TAGS = ('DateTimeOriginal', 'DateTimeDigitized', 'DateTime')
IDG_NAME_RE = re.compile(r'^IDG_(\d{8})_(\d{6})(?:_\d+)?', re.IGNORECASE)
IMG_NAME_RE = re.compile(r'^IMG_(\d+)', re.IGNORECASE)
MONTH_DAY_NAME_RE = re.compile(r'^[a-z]{3}-([0-9]{2})$', re.IGNORECASE)


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


def ensure_thumb(src_path: Path):
    """Generate a small jpeg thumbnail mirror of src_path under images/.thumbs/.

    Returns the rel path of the thumb, or None to signal 'use the source'.
    Skips regeneration when the thumb is newer than the source.
    """
    if src_path.suffix.lower() == '.svg':
        return None  # PIL can't rasterize SVG; let the canvas use the original
    rel = src_path.relative_to(ROOT / 'images')
    thumb = ROOT / 'images' / THUMB_DIR_NAME / rel.with_suffix('.jpg')
    if thumb.is_file() and thumb.stat().st_mtime >= src_path.stat().st_mtime:
        return str(thumb.relative_to(ROOT)).replace('\\', '/')
    thumb.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(src_path) as im:
            im = im.convert('RGB')
            w, h = im.size
            if max(w, h) > THUMB_LONG_EDGE:
                ratio = THUMB_LONG_EDGE / max(w, h)
                im = im.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.LANCZOS)
            im.save(thumb, 'JPEG', quality=THUMB_QUALITY, optimize=True)
        return str(thumb.relative_to(ROOT)).replace('\\', '/')
    except Exception as e:
        print(f"  thumb failed for {src_path.name}: {e}")
        return None


def build_all_images_data():
    """Scan images/ and emit js/all-images-data.js as [path, w, h, thumb] tuples.

    Pre-generates 400px-on-long-edge JPEG thumbnails under images/.thumbs/ so the
    canvas page loads small files instead of full-resolution originals.
    """
    images_dir = ROOT / 'images'
    if not images_dir.is_dir():
        print("images/ directory not found, skipping all-images-data.js")
        return

    entries = []
    skipped = 0
    thumbs_built = 0
    for img in sorted(images_dir.rglob('*')):
        if not (img.is_file() and img.suffix.lower() in IMAGE_EXTS):
            continue
        if THUMB_DIR_NAME in img.parts:
            continue  # never include the thumbs themselves in the data array
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

    posts = sorted(
        (p.name for p in blog_dir.iterdir()
         if p.is_file() and p.suffix == '.html' and not p.name.startswith('.')
         and p.name not in EXCLUDE_FILES),
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
        if not p.is_file() or p.suffix != '.html' or p.name.startswith('.') or p.name in EXCLUDE_FILES:
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

    posts.sort(key=lambda x: x[3], reverse=True)

    items = '\n'.join(
        f'            <div class="blog-item"><a href="blog/{filename}">{title}</a>'
        f' <span class="blog-item-date">{date_formatted}</span></div>'
        for filename, title, date_formatted, _ in posts
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

        # Parse YYYY-MM from filename: 2025-01-jan.html
        stem = gallery_file.stem  # "2025-01-jan"
        parts = stem.split('-', 2)
        if len(parts) < 3:
            continue
        year, month_num, month_name = parts  # "2025", "01", "jan"

        image_dir = images_monthly / year / f'{month_num}-{month_name}'
        horizontal = []
        vertical = []

        if image_dir.is_dir():
            img_files = sorted(
                image_dir.iterdir(),
                key=lambda p: monthly_sort_key(p, year, month_num),
            )
            for img_file in img_files:
                if not img_file.is_file() or img_file.name.startswith('.'):
                    continue
                if img_file.suffix.lower() not in PHOTO_EXTS:
                    continue
                try:
                    with Image.open(img_file) as img:
                        w, h = img.size
                    alt = img_file.stem
                    rel_path = img_file.relative_to(ROOT)
                    item = (
                        f'            <div class="gallery-grid-item">'
                        f'<img src="../../{rel_path}" alt="{alt}"'
                        f' class="styled-image" loading="lazy"></div>'
                    )
                    if w >= h:
                        horizontal.append(item)
                    else:
                        vertical.append(item)
                except Exception:
                    continue

        if not horizontal and not vertical:
            items = (
                '            <p style="grid-column: 1 / -1; color: #666;">'
                'no photos this month</p>'
            )
        else:
            parts_list = horizontal[:]
            if horizontal and vertical:
                parts_list.append(
                    '            <div style="grid-column: 1 / -1; height: 0; '
                    'margin: 0; padding: 0;"></div>'
                )
            parts_list.extend(vertical)
            items = '\n'.join(parts_list)

        grid = (
            '        <div class="gallery-grid">\n'
            f'{items}\n'
            '        </div>'
        )
        replacement = (
            '        <!-- AUTOGEN-START gallery-grid -->\n'
            f'{grid}\n'
            '        <!-- AUTOGEN-END gallery-grid -->'
        )
        gallery_file.write_text(marker_pattern.sub(replacement, original))
        updated += 1

    if updated:
        print(f"Updated {updated} monthly gallery page(s)")


def check_image_sizes():
    """Warn about images exceeding 1 MB."""
    images_dir = ROOT / 'images'
    if not images_dir.is_dir():
        return
    oversized = []
    for img in images_dir.rglob('*'):
        if img.is_file() and img.suffix.lower() in IMAGE_EXTS:
            if THUMB_DIR_NAME in img.parts:
                continue  # generated thumbs aren't worth warning about
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
    build_monthly_galleries()
    check_image_sizes()


if __name__ == "__main__":
    main()
