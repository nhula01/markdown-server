import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import app
import review_content
import site_content


class ReviewTests(unittest.TestCase):
    def test_cards_only_include_available_notebooks_and_verbatim_guides(self):
        names = app.pdf_files()
        cards = review_content.index(names)
        self.assertEqual({card['id'] for card in cards}, set(names))
        for card in cards:
            self.assertEqual(card['guide'], site_content.CATALOG.get('reading_guides', {}).get(Path(card['id']).stem, ''))
            self.assertTrue(card['pdf'].startswith('/pdfs/'))
        self.assertEqual(review_content.index([]), [])

    def test_review_routes_and_static_project_paths(self):
        for route in ['/review/', '/review-index.json', '/assets/review.js', '/assets/review-schedule.mjs']:
            response = {}
            def start(status, headers): response['status'] = status
            b''.join(app.application({'REQUEST_METHOD':'GET','PATH_INFO':route},start))
            self.assertEqual(response['status'], '200 OK', route)
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable,'scripts/build-pages.py','--output',directory],check=True,capture_output=True)
            out = Path(directory)
            page = (out/'review/index.html').read_text()
            self.assertIn('/markdown-server/assets/review.js',page)
            self.assertIn('/markdown-server/notes/review/',(out/'notes/index.html').read_text())
            manifest = json.loads((out/'manifest.webmanifest').read_text())
            self.assertEqual(manifest['start_url'], '/markdown-server/notes/review/')
            self.assertEqual(manifest['scope'], '/markdown-server/')
            self.assertEqual(manifest['display'], 'standalone')
            self.assertIn('/markdown-server/manifest.webmanifest', page)
            self.assertIn('/markdown-server/assets/pwa.js', page)
            from urllib.parse import unquote
            offline = json.loads((out/'offline-index.json').read_text())
            for url in offline['files']:
                target = out / unquote(url.removeprefix('/markdown-server/'))
                self.assertTrue(target.is_file() or (target/'index.html').is_file(), url)
                self.assertNotIn('/assets/audio/', url)
            self.assertTrue(any('/pdfs/' in url for url in offline['files']))
            self.assertNotIn('__BUILD_VERSION__', (out/'sw.js').read_text())
            self.assertNotIn('data-account-',page)
            self.assertIn('The same daily set for everyone',page)
            self.assertFalse((out/'auth-config.json').exists())
            self.assertFalse((out/'assets/vendor/supabase/supabase.mjs').exists())
            for card in json.loads((out/'review-index.json').read_text()):
                self.assertTrue(card['url'].startswith('/markdown-server/notebooks/'))
                self.assertTrue(card['pdf'].startswith('/markdown-server/pdfs/'))

    def test_removed_account_routes_are_unavailable(self):
        for route in ['/auth-config.json','/assets/review-account.mjs','/assets/vendor/supabase/supabase.mjs']:
            response = {}
            def start(status,headers): response['status'] = status
            b''.join(app.application({'REQUEST_METHOD':'GET','PATH_INFO':route},start))
            self.assertEqual(response['status'],'404 Not Found')
