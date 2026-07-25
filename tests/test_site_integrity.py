import hashlib
import importlib.util
import io
import json
import re
import unittest
from contextlib import redirect_stdout
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WATER_SHA256 = hashlib.sha256((ROOT / "images/water.gif").read_bytes()).hexdigest()
EXPECTED_WATER_SHA256 = "ba8f1fd15995431f2d72799b13573760fc39798189a6f14cd58ee5b49a225e46"


class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.levels = []

    def handle_starttag(self, tag, attrs):
        if re.fullmatch(r"h[1-6]", tag):
            self.levels.append(int(tag[1]))


class ReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.preview_sources = []
        self.blank_targets = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        attr_name = {
            "a": "href",
            "img": "src",
            "iframe": "src",
            "script": "src",
            "link": "href",
        }.get(tag)
        if attr_name and values.get(attr_name):
            self.references.append((tag, values[attr_name]))
        if values.get("data-preview-source"):
            self.preview_sources.append(values["data-preview-source"])
        if values.get("target") == "_blank":
            self.blank_targets.append(values)


def actual_pages():
    return sorted(
        page
        for page in ROOT.rglob("*.html")
        if ".git" not in page.parts
        and "archive" not in page.parts
        and "partials" not in page.parts
    )


class SiteIntegrityTests(unittest.TestCase):
    def test_water_gif_is_protected(self):
        self.assertEqual(WATER_SHA256, EXPECTED_WATER_SHA256)

    def test_protected_water_gif_does_not_trigger_size_warning(self):
        spec = importlib.util.spec_from_file_location(
            "build_sitemap", ROOT / "scripts/build-sitemap.py"
        )
        build_sitemap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_sitemap)
        output = io.StringIO()
        with redirect_stdout(output):
            build_sitemap.check_image_sizes()
        self.assertNotIn("images/water.gif", output.getvalue())

    def test_homepage_recent_blog_entry_matches_latest_blog_entry(self):
        blog = (ROOT / "blog.html").read_text()
        latest = re.search(
            r'AUTOGEN-START blog-list.*?<a href="(blog/[^"]+\.html)">',
            blog,
            re.DOTALL,
        ).group(1)
        homepage = (ROOT / "index.html").read_text()
        recent = re.search(
            r'AUTOGEN-START recent-blog.*?class="recent-card" href="(blog/[^"]+\.html)"',
            homepage,
            re.DOTALL,
        )
        self.assertIsNotNone(recent)
        self.assertEqual(recent.group(1), latest)

    def test_navigation_order_is_consistent(self):
        header = (ROOT / "partials/header.html").read_text()
        sitemap = (ROOT / "sitemap.html").read_text()
        expected = ["home", "photos", "blog", "builds", "plants", "about"]
        header_labels = re.findall(r'title="([^"]+)"', header)
        sitemap_nav = re.search(
            r'<nav class="nav"[^>]*>(.*?)</nav>', sitemap, re.DOTALL
        ).group(1)
        sitemap_labels = [
            label.rstrip("+") for label in re.findall(r">([^<]+)</a>", sitemap_nav)
        ]
        self.assertEqual(header_labels, expected)
        self.assertEqual(sitemap_labels, expected)
        self.assertRegex(
            sitemap_nav,
            r'<a href="about\.html" aria-current="page">about</a>',
        )

    def test_blog_navigation_supports_newer_and_older(self):
        script = (ROOT / "js/blog-nav.js").read_text()
        self.assertIn("newerIndex", script)
        self.assertIn("newer", script)
        self.assertIn("olderIndex", script)

    def test_gallery_loader_initializes_each_grid(self):
        script = (ROOT / "js/gallery.js").read_text()
        self.assertRegex(script, r"querySelectorAll\(['\"]\.gallery-grid['\"]\)")
        self.assertNotIn(
            "const items = Array.from(document.querySelectorAll('.gallery-grid-item'))",
            script,
        )
        ipod = (ROOT / "blog/builds/ipod.html").read_text()
        self.assertIn("../../js/gallery.js", ipod)

    def test_dynamic_video_iframe_is_lazy_loaded(self):
        script = (ROOT / "js/lite-yt.js").read_text()
        self.assertRegex(script, r"iframe\.loading\s*=\s*['\"]lazy['\"]")

    def test_rolling_books_page_is_in_sitemap_data(self):
        data = (ROOT / "js/sitemap-data.js").read_text()
        self.assertIn("2025-09-04-review-books-i-have-read-2023-2024-2025.html", data)

    def test_shared_accessibility_contracts(self):
        header = (ROOT / "partials/header.html").read_text()
        css = (ROOT / "styles/style.css").read_text()
        self.assertIn('class="skip-link"', header)
        include_script = (ROOT / "js/include.js").read_text()
        self.assertIn("aria-current", include_script)
        self.assertIn("let currentSection = null", include_script)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        homepage = (ROOT / "index.html").read_text()
        self.assertNotIn("<marquee", homepage)
        self.assertIn("pageShell.setAttribute('inert', '')", homepage)
        self.assertIn("event.key === 'Tab'", homepage)
        self.assertNotIn("user-scalable=no", (ROOT / "all-images.html").read_text())

    def test_programmatic_main_focus_does_not_draw_a_page_border(self):
        css = (ROOT / "styles/style.css").read_text()
        self.assertNotIn("[tabindex]:focus-visible", css)
        self.assertRegex(
            css,
            r"#main-content:focus\s*\{\s*outline:\s*none;",
        )
        self.assertIn("a:focus-visible", css)
        self.assertIn("button:focus-visible", css)

    def test_home_boot_overlay_hidden_state_removes_it_from_layout(self):
        homepage = (ROOT / "index.html").read_text()
        self.assertRegex(
            homepage,
            r"#boot-overlay\[hidden\]\s*\{\s*display:\s*none;",
        )

    def test_home_boot_overlay_finishes_within_prescribed_window(self):
        homepage = (ROOT / "index.html").read_text()
        auto_delay = int(
            re.search(
                r"autoBootTimeout\s*=\s*setTimeout\(bootNuBlog,\s*(\d+)\)",
                homepage,
            ).group(1)
        )
        fade_delay = int(
            re.search(r"reducedMotion\s*\?\s*0\s*:\s*(\d+)", homepage).group(1)
        )
        total_delay = auto_delay + fade_delay
        self.assertGreaterEqual(total_delay, 3000)
        self.assertLessEqual(total_delay, 5000)

    def test_bot_blocker_allows_local_preview_without_weakening_public_block(self):
        script = (ROOT / "js/bot-blocker.js").read_text()
        self.assertIn("isLocalPreview", script)
        self.assertRegex(script, r"if\s*\(isBot\s*&&\s*!isLocalPreview\)")

    def test_every_page_has_main_landmark(self):
        missing = []
        for page in actual_pages():
            text = page.read_text(errors="replace")
            if not re.search(r"<main(?:\s|>)|role=[\"']main[\"']", text, re.IGNORECASE):
                missing.append(str(page.relative_to(ROOT)))
        self.assertEqual(missing, [])

    def test_pages_have_h1_and_do_not_skip_heading_levels(self):
        failures = []
        for page in actual_pages():
            parser = HeadingParser()
            parser.feed(page.read_text(errors="replace"))
            if 1 not in parser.levels:
                failures.append((str(page.relative_to(ROOT)), "missing h1"))
            if any(second > first + 1 for first, second in zip(parser.levels, parser.levels[1:])):
                failures.append((str(page.relative_to(ROOT)), "heading level jump"))
        self.assertEqual(failures, [])

    def test_images_have_lazy_loading_alt_and_intrinsic_dimensions(self):
        failures = []
        for page in actual_pages():
            parser = ImageParser()
            parser.feed(page.read_text(errors="replace"))
            for image in parser.images:
                missing = []
                if "alt" not in image:
                    missing.append("alt")
                missing.extend(
                    name for name in ("width", "height", "loading") if not image.get(name)
                )
                if missing:
                    failures.append(
                        (
                            str(page.relative_to(ROOT)),
                            image.get("src"),
                            ",".join(missing),
                        )
                    )
                    continue
                src = image.get("src", "")
                if src.startswith(("https://i.ytimg.com/", "http://i.ytimg.com/")):
                    expected = (480, 360)
                elif src.startswith(("http://", "https://", "//", "data:")):
                    continue
                else:
                    image_path = (
                        ROOT / src.lstrip("/")
                        if src.startswith("/")
                        else (page.parent / src).resolve()
                    )
                    with Image.open(image_path) as opened:
                        expected = opened.size
                        if opened.getexif().get(274, 1) in (5, 6, 7, 8):
                            expected = (expected[1], expected[0])
                actual = (int(image["width"]), int(image["height"]))
                if actual != expected:
                    failures.append(
                        (
                            str(page.relative_to(ROOT)),
                            src,
                            f"dimensions {actual} != {expected}",
                        )
                    )
        self.assertEqual(failures, [])

    def test_non_decorative_image_alt_text_is_not_a_filename(self):
        failures = []
        filename_pattern = re.compile(
            r"^(?:IMG|IDG|DSC|R1-|PXL|MVIMG|[0-9A-F]{8}-)[A-Z0-9_.\-\s]*$",
            re.IGNORECASE,
        )
        for page in actual_pages():
            parser = ImageParser()
            parser.feed(page.read_text(errors="replace"))
            for image in parser.images:
                alt = image.get("alt", "").strip()
                src = image.get("src", "")
                if not alt:
                    continue
                stem = Path(src.split("?", 1)[0]).stem
                if alt.lower() == stem.lower() or filename_pattern.fullmatch(alt):
                    failures.append((str(page.relative_to(ROOT)), src, alt))
        self.assertEqual(failures, [])

    def test_local_references_and_preview_sources_exist(self):
        failures = []
        ignored_prefixes = (
            "http://",
            "https://",
            "//",
            "mailto:",
            "tel:",
            "javascript:",
            "data:",
            "#",
        )
        for page in actual_pages():
            text = page.read_text(errors="replace")
            parser = ReferenceParser()
            parser.feed(text)
            references = parser.references + [
                ("background", url)
                for url in re.findall(r"url\(['\"]?([^'\")]+)", text)
            ]
            references += [("preview", src) for src in parser.preview_sources]
            for tag, raw in references:
                path = raw.split("#", 1)[0].split("?", 1)[0]
                if not path or path.startswith(ignored_prefixes):
                    continue
                target = ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path
                if not target.exists():
                    failures.append((str(page.relative_to(ROOT)), tag, raw))
            for attrs in parser.blank_targets:
                rel = set(attrs.get("rel", "").split())
                if "noopener" not in rel:
                    failures.append(
                        (str(page.relative_to(ROOT)), "target=_blank", attrs.get("href"))
                    )

        gallery_data = (ROOT / "js/gallery-data.js").read_text()
        for kind in ("sourceImage", "previewImage"):
            for src in re.findall(rf"{kind}:\s*['\"]([^'\"]+)", gallery_data):
                if not (ROOT / src).is_file():
                    failures.append(("js/gallery-data.js", kind, src))

        css = (ROOT / "styles/style.css").read_text()
        for src in re.findall(r"url\(['\"]?([^'\")]+)", css):
            if src.startswith(ignored_prefixes):
                continue
            if not ((ROOT / "styles") / src).resolve().is_file():
                failures.append(("styles/style.css", "background", src))
        self.assertEqual(failures, [])

    def test_all_images_data_matches_source_dimensions(self):
        source = (ROOT / "js/all-images-data.js").read_text()
        entries = json.loads(
            re.search(r"window\.allImagesData\s*=\s*(\[.*\]);", source, re.DOTALL).group(1)
        )
        failures = []
        for src, width, height, thumb in entries:
            source_path = ROOT / src
            thumb_path = ROOT / thumb
            if not source_path.exists() or not thumb_path.exists():
                failures.append((src, "missing"))
                continue
            with Image.open(source_path) as image:
                if image.size != (width, height):
                    failures.append((src, "dimensions"))
        self.assertEqual(failures, [])

    def test_confirmed_external_citation_is_not_malformed(self):
        page = (
            ROOT / "blog/2021-04-28-final-project-for-fintech-2021.html"
        ).read_text()
        self.assertNotIn("american-jobs-plan/.", page)
        self.assertIn("presidency.ucsb.edu/documents/fact-sheet-the-american-jobs-plan", page)

    def test_new_badge_is_derived_not_hand_written(self):
        """A hand-written '*new!' cannot expire, so nothing may set is-new in
        markup. js/whats-new.js assigns it from data-added, and only inside the
        freshness window — that is the whole point of the mechanism."""
        offenders = []
        for page in actual_pages():
            text = page.read_text(errors="replace")
            if re.search(r'class="[^"]*\bis-new\b', text):
                offenders.append(str(page.relative_to(ROOT)))
            if "camera-highlight" in text:
                offenders.append(f"{page.relative_to(ROOT)} (retired class)")
        self.assertEqual(offenders, [])

    def test_dated_cards_live_inside_a_new_scope(self):
        """data-added outside a [data-new-scope] container is inert: the badge
        would silently never appear."""
        orphans = []
        for page in actual_pages():
            text = page.read_text(errors="replace")
            if "data-added=" in text and "data-new-scope" not in text:
                orphans.append(str(page.relative_to(ROOT)))
        self.assertEqual(orphans, [])

    def test_spec_box_is_not_re_inlined(self):
        """.spec-box is canonical in style.css. It was previously copied into
        10 builds pages and drifted into 3 variants; re-inlining restarts that."""
        offenders = []
        for page in sorted((ROOT / "blog/builds").glob("*.html")):
            text = page.read_text(errors="replace")
            for block in re.findall(r"<style>(.*?)</style>", text, re.DOTALL):
                if ".spec-box" in block:
                    offenders.append(str(page.relative_to(ROOT)))
        self.assertEqual(offenders, [])
        self.assertIn(".spec-box {", (ROOT / "styles/style.css").read_text())

    def test_homepage_recent_cards_are_newest_first(self):
        """The strip is called 'recent'; a card out of date order makes it lie.
        Every card needs data-date or build-sitemap.py cannot sort it."""
        text = (ROOT / "index.html").read_text()
        block = re.search(
            r'<div class="recent-cards">(.*?)\n\s*</div>\s*</div>', text, re.DOTALL
        )
        self.assertIsNotNone(block, "recent-cards container not found")
        cards = re.findall(r'<a class="recent-card"[^>]*>', block.group(1))
        self.assertGreater(len(cards), 1)
        undated = [c for c in cards if "data-date=" not in c]
        self.assertEqual(undated, [])
        dates = [re.search(r'data-date="([\d-]+)"', c).group(1) for c in cards]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_cards_are_one_size_outside_the_blog_strip(self):
        """One card size sitewide. The 3:1 rolling strip on blog.html is the
        single sanctioned exception; a second override means drift restarting."""
        css = (ROOT / "styles/style.css").read_text()
        self.assertIn("aspect-ratio: 3 / 2;", css)
        self.assertIn("box-sizing: border-box;", css)

        overrides = []
        for page in actual_pages():
            text = page.read_text(errors="replace")
            for block in re.findall(r"<style>(.*?)</style>", text, re.DOTALL):
                if "aspect-ratio" in block and (
                    "big-link-box" in block or "gallery-entry-preview" in block
                ):
                    overrides.append(str(page.relative_to(ROOT)))
        self.assertEqual(overrides, ["blog.html"])

    def test_post_images_use_only_sanctioned_scales(self):
        """Post images come in three widths and no others: the measure
        (default), .wide, and .tall. An inline max-width reintroduces the
        fourth, fifth and sixth."""
        offenders = []
        for page in sorted(ROOT.glob("blog/**/*.html")):
            text = page.read_text(errors="replace")
            for tag in re.findall(r"<img[^>]*>", text):
                if re.search(r"style=\"[^\"]*(max-)?width\s*:", tag):
                    offenders.append(f"{page.relative_to(ROOT)}: {tag[:70]}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
