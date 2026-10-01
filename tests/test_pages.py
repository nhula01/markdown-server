import os
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
            self.assertIn('/markdown-server/pdfs/Open%20Systems/Input%20Output.pdf', viewer)
            page = (out / 'docs/welcome.md/index.html').read_text()
            self.assertIn('/markdown-server/docs/notes/next.md/', page)
            self.assertIn('/markdown-server/docs/pic.png', page)
            self.assertTrue((out / '.nojekyll').exists())
