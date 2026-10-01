import os
import re
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PagesTests(unittest.TestCase):
    def test_static_library_preserves_pdf_and_project_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = root / 'content'; content.mkdir()
            (content / 'welcome.md').write_text('[Next](notes/next.md)\n\n![Sketch](pic.png)')
            (content / 'notes').mkdir()
            (content / 'notes/next.md').write_text('# Next')
            (content / 'pic.png').write_bytes(b'PNG')
            pdfs = root / 'pdfs'; (pdfs / 'Open Systems').mkdir(parents=True)
            data = b'%PDF-1.4 unchanged handwriting bytes'
            (pdfs / 'Open Systems/Input Output.pdf').write_bytes(data)
            out = root / 'site'
            subprocess.run([sys.executable, 'scripts/build-pages.py', '--output', str(out)],
                           env={**os.environ, 'MD_ROOT': str(content), 'PDF_ROOT': str(pdfs)},
                           check=True, capture_output=True)
            self.assertEqual((out / 'pdfs/Open Systems/Input Output.pdf').read_bytes(), data)
            viewer = (out / 'notebooks/Open Systems/Input Output.pdf/index.html').read_text()
            self.assertIn('/markdown-server/pdfs/Open%20Systems/Input%20Output.pdf?v=' + hashlib.sha256(data).hexdigest()[:16], viewer)
            page = (out / 'docs/welcome.md/index.html').read_text()
            self.assertIn('/markdown-server/docs/notes/next.md/', page)
            self.assertIn('/markdown-server/docs/pic.png', page)
            self.assertTrue((out / '.nojekyll').exists())

    def test_topic_navigation_and_unfiled_exports_remain_reachable(self):
        from html.parser import HTMLParser
        from urllib.parse import unquote, urlsplit

        class Links(HTMLParser):
            def __init__(self):
                super().__init__(); self.urls = []
            def handle_starttag(self, tag, attrs):
                self.urls.extend(value for key, value in attrs if key in {'href', 'src'})

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = root / 'content'; content.mkdir()
            pdfs = root / 'pdfs'; (pdfs / 'Obsidian').mkdir(parents=True)
            (pdfs / 'Obsidian/Crystal.pdf').write_bytes(b'%PDF original')
            (pdfs / 'Obsidian/A new notebook.pdf').write_bytes(b'%PDF new')
            out = root / 'site'
            subprocess.run([sys.executable, 'scripts/build-pages.py', '--output', str(out)],
                           env={**os.environ, 'MD_ROOT': str(content), 'PDF_ROOT': str(pdfs)},
                           check=True, capture_output=True)
            # Menu navigation must bypass cached HTML, not just cached CSS.
            for route in ['index.html', 'notes/index.html', 'research/index.html', 'about/index.html']:
                html = (out / route).read_text()
                for section in ['notes', 'research', 'about']:
                    self.assertRegex(html, f'/markdown-server/{section}/\\?v=[a-f0-9]{{16}}')
            notes = (out / 'notes/index.html').read_text()
            self.assertIn('A new notebook', re.sub('<[^>]+>', '', notes))
            self.assertIn('Outline · notes to come', notes)
            matter = (out / 'notes/light-and-matter/index.html').read_text()
            self.assertIn('/markdown-server/notebooks/Obsidian/Crystal.pdf/', matter)
            quantum = (out / 'notes/quantum-optics/index.html').read_text()
            self.assertIn('no published notebooks here yet', quantum)
            self.assertNotIn('<iframe', quantum)
            for page in out.rglob('*.html'):
                parser = Links(); parser.feed(page.read_text())
                for url in parser.urls:
                    path = unquote(urlsplit(url).path)
                    if not path.startswith('/markdown-server/'):
                        continue
                    target = out / path.removeprefix('/markdown-server/')
                    with self.subTest(page=page.relative_to(out), url=url):
                        self.assertTrue(target.is_file() or (target / 'index.html').is_file())
