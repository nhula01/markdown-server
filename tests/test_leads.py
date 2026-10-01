import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

import app
import chapter_content
import lead_content


class LeadTests(unittest.TestCase):
    def test_source_parsing_excludes_private_prose_and_rejects_invalid_trails(self):
        text = '# Personal note\nPrivate comment\n\n## What follows?\n1. [[Crystal]]\nDo not publish this prose.\n2. [[Linear Light]]\n'
        self.assertEqual(lead_content.parse_leads(text)[0]['steps'], ['Crystal', 'Linear Light'])
        self.assertNotIn('Private', json.dumps(lead_content.parse_leads(text)))
        for source in ['## Empty\n', '## Broken\n1. not a link\n2. [[Crystal]]',
                       '## Duplicate\n1. [[Crystal]]\n2. [[Crystal]]']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                lead_content.parse_leads(source)

    def test_remaining_trail_and_future_pdf_resolution(self):
        lead = next(lead for lead in lead_content.for_note('Oscillator Model') if lead['question'] == 'How does matter respond to light?')
        self.assertEqual(lead['steps'], ['Oscillator Model', 'Linear Light'])
        self.assertFalse(any(lead['question'] == 'How does matter respond to light?' for lead in lead_content.for_note('Linear Light')))
        self.assertEqual(lead_content.step('Plane Waves', [])['status'], 'Planned chapter')
        future = lead_content.step('Plane Waves', ['Obsidian/Plane Waves.pdf'])
        self.assertEqual(future['status'], 'Handwritten note')
        self.assertEqual(future['url'], '/notebooks/Obsidian/Plane%20Waves.pdf/')
        self.assertEqual(lead_content.step('A future notebook', [])['url'], '/notes/')

    def test_local_server_exposes_explorer_data(self):
        response = {}
        def start(status, headers):
            response['status'] = status
            response['headers'] = dict(headers)
        body = b''.join(app.application({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/leads-index.json'}, start))
        self.assertEqual(response['status'], '200 OK')
        data = json.loads(body)
        self.assertTrue(data['leads'])
        self.assertTrue(all(note['url'].startswith('/notebooks/') for note in data['starts']))
        planned = chapter_content.concept_page('normal-modes', app.pdf_files())
        self.assertIn('Electromagnetic Pieces', planned)
        self.assertIn('Maxwell', planned)

    def test_static_explorer_paths_and_chapter_launches(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            subprocess.run([sys.executable, 'scripts/build-pages.py', '--output', directory], check=True, capture_output=True)
            data = json.loads((out / 'leads-index.json').read_text())
            self.assertEqual(len(data['starts']), len(app.pdf_files()))
            self.assertIn('id="thread-query"', (out / 'index.html').read_text())
            self.assertIn('/markdown-server/assets/leads.js', (out / 'index.html').read_text())
            for lead in data['leads']:
                for step in lead['steps']:
                    target = out / unquote(urlsplit(step['url']).path).removeprefix('/markdown-server/')
                    self.assertTrue((target / 'index.html').exists(), step)
            crystal = (out / 'notebooks/Obsidian/Crystal.pdf/index.html').read_text()
            self.assertIn('Follow a lead', crystal)
            self.assertIn('start=Crystal&amp;lead=', crystal)
            self.assertNotIn('Physical picture', crystal)
            source = next(entry for entry in data['starts'] if entry['title'] == 'Electromagnetic Pieces')
            self.assertIn('outflow', source['text'])
            self.assertIn('How does matter respond to light?', source['text'])
