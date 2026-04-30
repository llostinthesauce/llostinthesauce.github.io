#!/usr/bin/env python3
"""Build js/sitemap-data.js and all-images.html from filesystem scan.

Run from repo root:  python3 scripts/build-sitemap.py
"""
import json
import re
from datetime import datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent.parent.resolve()
EXCLUDE_DIRS = {'.git', '__pycache__', '.remember', '.DS_Store', 'node_modules'}
EXCLUDE_FILES = {
    'CLAUDE.md', 'agents-wiki.md',
    'corbin-style-guide.md', 'corbin-style-guide-builds.md',
    'audit-report-042926.md', 'audit-guide-and-review-for-deepseek.md',
    'deepseekv4proaudit.md', 'geminiflashaudit.md',
    'glm5-1audit.md', 'glm5-1auditthourough.md',
    'opusreport.md', 'qwen3.6moe-report.md',
    'ssg-migration-design.md', 'nublogv2.1 full changes.md',
    'HANDOFF.md', '2025-09-04-review-books-i-have-read-2023-2024-2025.html',
}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
PHOTO_EXTS = {'.jpg', '.jpeg', '.png'}
MB = 1024 * 1024


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


def build_all_images():
    """Scan images/ directory and generate all-images.html."""
    images_dir = ROOT / 'images'
    if not images_dir.is_dir():
        print("images/ directory not found, skipping all-images.html")
        return

    img_paths = []
    for img in sorted(images_dir.rglob('*')):
        if img.is_file() and img.suffix.lower() in IMAGE_EXTS:
            rel = img.relative_to(ROOT)
            img_paths.append(str(rel))

    if not img_paths:
        print("No images found, skipping all-images.html")
        return

    items = '\n'.join(
        f'            <div class="gallery-grid-item">'
        f'<img src="{p}" alt="" class="styled-image" loading="lazy"></div>'
        for p in img_paths
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noai, noimageai">
    <title>all images - nuBlog</title>
    <link rel="stylesheet" href="styles/style.css">
    <link rel="icon" href="favicon.ico" type="image/x-icon">
</head>
<body>
    <div class="content">
        <div id="site-header"></div>
        <a href="index.html" class="back-link">&larr; back</a>
        <h1 class="underlined-heading">all images</h1>
        <p>a flat view of literally every image file in the repository. auto-generated {img_paths.__len__()} images.</p>

        <div class="gallery-grid">
{items}
        </div>

        <div id="site-footer"></div>
    </div>
    <script src="js/include.js" data-base="."></script>
    <script src="js/gallery.js"></script>
</body>
</html>
"""
    out = ROOT / 'all-images.html'
    out.write_text(html)
    print(f"Generated {out} ({len(img_paths)} images)")


def build_blog_nav():
    """Rewrite the blogPosts array in js/blog-nav.js between AUTOGEN markers."""
    blog_dir = ROOT / 'blog'
    nav_path = ROOT / 'js' / 'blog-nav.js'
    if not blog_dir.is_dir() or not nav_path.is_file():
        print("blog/ or js/blog-nav.js missing, skipping blog-nav update")
        return

    posts = sorted(
        (p.name for p in blog_dir.iterdir()
         if p.is_file() and p.suffix == '.html' and not p.name.startswith('.')),
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
            for img_file in sorted(image_dir.iterdir()):
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

    build_all_images()
    build_blog_nav()
    build_blog_list()
    build_monthly_galleries()
    check_image_sizes()


if __name__ == "__main__":
    main()
