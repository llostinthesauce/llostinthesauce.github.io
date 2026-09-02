import importlib.util
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BuildAssetTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('build_sitemap', ROOT / 'scripts/build-sitemap.py')
        self.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.build)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build.ROOT = self.root

    def version_loader(self):
        version = getattr(self.build, 'version_shared_loader', None)
        self.assertTrue(callable(version), 'the build must invalidate cached shared loaders')
        with redirect_stdout(io.StringIO()):
            version()

    def test_loader_url_changes_when_either_counter_or_loader_changes(self):
        (self.root / 'js').mkdir()
        loader = self.root / 'js/include.js'
        counter = self.root / 'js/counter.js'
        loader.write_text('loader one')
        counter.write_text('counter one')
        page = self.root / 'index.html'
        page.write_text('<script src="js/include.js" data-base="."></script>')
        self.version_loader()
        first = page.read_text()
        self.assertRegex(first, r'js/include\.js\?v=[a-f0-9]+')
        self.version_loader()
        self.assertEqual(page.read_text(), first)
        counter.write_text('counter two')
        self.version_loader()
        second = page.read_text()
        self.assertNotEqual(second, first)
        loader.write_text('loader two')
        self.version_loader()
        self.assertNotEqual(page.read_text(), second)
        self.assertIn('data-base="."', page.read_text())

    def test_versioning_keeps_nested_paths_and_leaves_external_scripts_alone(self):
        (self.root / 'js').mkdir()
        (self.root / 'js/include.js').write_text('loader')
        (self.root / 'js/counter.js').write_text('counter')
        (self.root / 'plants').mkdir()
        page = self.root / 'plants/page.html'
        external = '<script src="https://example.com/js/include.js?v=keep"></script>'
        page.write_text('<script src="../js/include.js?v=old" data-base=".."></script>' + external)
        self.version_loader()
        self.assertRegex(page.read_text(), r'\.\./js/include\.js\?v=[a-f0-9]+')
        self.assertIn(external, page.read_text())
        self.assertIn('data-base=".."', page.read_text())

    def test_goodreads_embed_geometry_survives_offline_build(self):
        page = self.root / 'index.html'
        page.write_text('<h1>books</h1><img src="https://i.gr-assets.com/cover.jpg" alt="The Odyssey" width="50" height="75">')
        with redirect_stdout(io.StringIO()):
            self.build.enrich_image_metadata()
        self.assertIn('loading="lazy"', page.read_text())
        self.assertIn('width="50" height="75"', page.read_text())

    def test_goodreads_images_without_valid_dimensions_still_fail_build(self):
        (self.root / 'index.html').write_text('<img src="https://i.gr-assets.com/cover.jpg" width="0" height="75">')
        with self.assertRaises(RuntimeError):
            self.build.enrich_image_metadata()

    def test_browser_script_runtime(self):
        result = subprocess.run(['node', '--test', str(ROOT / 'tests/counter.test.js'), str(ROOT / 'tests/goodreads.test.js')], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
