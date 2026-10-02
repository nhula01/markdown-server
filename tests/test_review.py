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
        for route in ['/review/', '/review-index.json', '/assets/review.js', '/assets/review-schedule.mjs', '/assets/review-account.mjs', '/assets/review-cloud.mjs', '/auth-config.json']:
            response = {}
            def start(status, headers): response['status'] = status
            b''.join(app.application({'REQUEST_METHOD':'GET','PATH_INFO':route},start))
            self.assertEqual(response['status'], '200 OK', route)
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable,'scripts/build-pages.py','--output',directory],check=True,capture_output=True)
            out = Path(directory)
            page = (out/'review/index.html').read_text()
            self.assertIn('/markdown-server/assets/review.js',page)
            self.assertIn('/markdown-server/review/',(out/'index.html').read_text())
            self.assertEqual(json.loads((out/'auth-config.json').read_text()), review_content.auth_config())
            self.assertTrue((out/'assets/vendor/supabase/supabase.mjs').exists())
            for card in json.loads((out/'review-index.json').read_text()):
                self.assertTrue(card['url'].startswith('/markdown-server/notebooks/'))
                self.assertTrue(card['pdf'].startswith('/markdown-server/pdfs/'))

    def test_auth_build_rejects_secrets(self):
        from unittest.mock import patch
        with patch('review_content.json.loads', return_value={'url':'https://example.supabase.co','publishableKey':'sb_secret_example'}):
            with self.assertRaises(ValueError): review_content.auth_config()
        with patch('review_content.json.loads', return_value={'url':'','publishableKey':'','password':'private'}):
            with self.assertRaises(ValueError): review_content.auth_config()
