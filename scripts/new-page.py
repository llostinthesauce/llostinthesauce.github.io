#!/usr/bin/env python3
"""Scaffold a new page with correct boilerplate.

Run from repo root:  python3 scripts/new-page.py --type blog --title "My Post"

Default filenames follow what the build expects: blog posts are
YYYY-MM-DD-<slug>.html (today), monthly galleries YYYY-MM-mmm.html (the month
in --date, else this month).
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

TEMPLATES = {
    "blog": {
        "dir": "blog",
        "depth": 1,
        "base": "..",
        "css": "../styles/style.css",
        "template": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noai, noimageai">
    <title>{title} - nuBlog</title>
    <link rel="stylesheet" href="{css}">
    <!-- essay | university | field-notes | creative | other (groups writing.html) -->
    <meta name="nublog:category" content="essay">
    <script src="../js/theme.js" data-page="post"></script>
    <link rel="icon" href="../favicon.ico" type="image/x-icon">
</head>
<body>
    <div class="content">
        <div id="site-header"></div>
        <main id="main-content" tabindex="-1">
        <a href="../blog.html" class="back-link">&larr; back to blog</a>
        
        <h1>{title}</h1>
        <div class="blog-post-date">{date}</div>
        <div class="blog-post-content">
            <p>start writing here...</p>
        </div>
        </main>
        <div id="site-footer"></div>
    </div>
    <script src="../js/include.js" data-base=".."></script>
</body>
</html>
""",
    },
    "builds-project": {
        "dir": "blog/builds",
        "depth": 2,
        "base": "../..",
        "css": "../../styles/style.css",
        "template": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noai, noimageai">
    <title>{title} - builds+ - nuBlog</title>
    <link rel="stylesheet" href="{css}">
    <link rel="icon" href="../../favicon.ico" type="image/x-icon">
</head>
<body>
    <div class="content">
        <div id="site-header"></div>
        <main id="main-content" tabindex="-1">
        <a href="index.html" class="back-link">&larr; back to builds+</a>
        <h1>{title}</h1>
        <div class="blog-post-date">{date}</div>

        <div class="blog-post-content">
            <p>start writing here...</p>
        </div>

        </main>
        <div id="site-footer"></div>
    </div>
    <script src="../../js/include.js" data-base="../.."></script>
</body>
</html>
""",
    },
    "builds-machine": {
        "dir": "blog/builds",
        "depth": 2,
        "base": "../..",
        "css": "../../styles/style.css",
        "template": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noai, noimageai">
    <title>{title} - builds+ - nuBlog</title>
    <link rel="stylesheet" href="{css}">
    <link rel="icon" href="../../favicon.ico" type="image/x-icon">
</head>
<body>
    <div class="content">
        <div id="site-header"></div>
        <main id="main-content" tabindex="-1">
        <a href="index.html" class="back-link">&larr; back to builds+</a>
        <h1>{title}</h1>
        <div class="blog-post-date">{date}</div>

        <div class="blog-post-content">
            <div class="spec-box">
                <table>
                    <tr><td>cpu</td><td></td></tr>
                    <tr><td>gpu</td><td></td></tr>
                    <tr><td>memory</td><td></td></tr>
                    <tr><td>storage</td><td></td></tr>
                    <tr><td>os</td><td></td></tr>
                </table>
            </div>
            <p>description here...</p>
        </div>

        </main>
        <div id="site-footer"></div>
    </div>
    <script src="../../js/include.js" data-base="../.."></script>
</body>
</html>
""",
    },
    "monthly-gallery": {
        "dir": "galleries/monthly",
        "depth": 2,
        "base": "../..",
        "css": "../../styles/style.css",
        "template": """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noai, noimageai">
    <title>{title} - nuBlog</title>
    <link rel="stylesheet" href="{css}">
    <link rel="icon" href="../../favicon.ico" type="image/x-icon">
    
</head>

<body>
    <div class="content">
        <div id="site-header"></div>
        <main id="main-content" tabindex="-1">
        <a href="../../galleries.html" class="back-link">&larr; back to galleries</a>
        <h1>{title}</h1>
        <p class="note">sorted chronologically — horizontal photos first, then vertical photos</p>

        <!-- AUTOGEN-START gallery-grid -->
        <div class="gallery-grid">
        </div>
        <!-- AUTOGEN-END gallery-grid -->

        </main>
        <div id="site-footer"></div>
    </div>
    <script src="../../js/include.js" data-base="../.."></script>
    
    <script src="../../js/gallery.js"></script>
</body>

</html>
""",
    },
}


def slugify(title):
    """Convert title to a URL-friendly slug."""
    return title.lower().replace(' ', '-').replace('/', '-')


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new nuBlog page")
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=list(TEMPLATES.keys()),
        help="Page type",
    )
    parser.add_argument(
        "--title", "-T",
        required=True,
        help="Page title (used for <h1> and filename)",
    )
    parser.add_argument(
        "--date", "-d",
        help='Date line text (default: "Originally published: <today>" for '
             'blog posts, "<Month> <Year>" otherwise; a monthly gallery reads '
             'its month from it)',
    )
    parser.add_argument(
        "--filename", "-f",
        help="Output filename (default: auto-generated from title)",
    )
    args = parser.parse_args()

    tmpl = TEMPLATES[args.type]
    today = datetime.now()
    slug = slugify(args.title)
    if args.type == "blog":
        date = args.date or f"Originally published: {today:%B} {today.day}, {today.year}"
        default_name = f"{today:%Y-%m-%d}-{slug}.html"
    elif args.type == "monthly-gallery":
        date = args.date or today.strftime('%B %Y')
        try:
            month = datetime.strptime(date, '%B %Y')
        except ValueError:
            sys.exit('ERROR: --date must look like "September 2026" for a monthly gallery')
        default_name = f"{month:%Y-%m}-{month:%b}.html".lower()
    else:
        date = args.date or today.strftime('%B %Y')
        default_name = f"{slug}.html"
    filename = args.filename or default_name
    out_path = ROOT / tmpl["dir"] / filename

    if out_path.exists():
        sys.exit(f"ERROR: {out_path} already exists — aborting")

    html = tmpl["template"].format(
        title=args.title,
        date=date,
        css=tmpl["css"],
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"Created {out_path}")
    print(f"  type: {args.type} (depth={tmpl['depth']}, data-base={tmpl['base']})")
    print(f"  next: add a thumbnail + index card if builds+ page, then run:")
    print(f"        python3 scripts/build-sitemap.py")


if __name__ == "__main__":
    main()
