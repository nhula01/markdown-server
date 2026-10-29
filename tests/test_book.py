import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import book_content
import app
import chapter_content


class CollectedBookTests(unittest.TestCase):
    def test_topic_order_page_destinations_and_original_pages(self):
        names = ['Obsidian/Quantum Pictures.pdf', 'Obsidian/Crystal.pdf', 'Obsidian/Draft.pdf']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'Obsidian').mkdir()
            originals = {}
            for i, name in enumerate(names):
                writer = PdfWriter()
                writer.add_blank_page(width=500+i, height=700+i)
                writer.write(root/name)
                originals[name] = (root/name).read_bytes()
            data, entries = book_content.build(names, root)
            import io
            reader = PdfReader(io.BytesIO(data))
            matter, quantum = entries[1:3]
            for entry, width in [(matter,501),(quantum,500)]:
                note=entry['notes'][0]
                self.assertGreater(note['source_page'],note['page'])
                self.assertEqual(float(reader.pages[note['source_page']-1].mediabox.width),width)
            destinations={page.indirect_reference.idnum:i for i,page in enumerate(reader.pages)}
            links=[a.get_object() for page in reader.pages if '/Annots' in page for a in page['/Annots']]
            internal=[a for a in links if '/Dest' in a]
            self.assertGreater(len(internal),3)
            for annotation in internal:
                self.assertIn(annotation['/Dest'][0].idnum,destinations)
            qp=quantum['notes'][0]
            activators=[a for a in internal if a.get('/Contents')=='Read the original activator']
            self.assertEqual(len(activators),1)
            self.assertEqual(destinations[activators[0]['/Dest'][0].idnum],qp['source_page']-1)
            self.assertTrue(any('/A' in a and a['/A'].get('/URI','').startswith('https://nhula01.github.io/markdown-server/') for a in links))
            for name, original in originals.items():
                self.assertEqual((root/name).read_bytes(), original)
            self.assertEqual(data, book_content.build(names, root)[0])

    def test_home_and_chapter_context(self):
        html = __import__('site_content').home(app.pdf_files())
        self.assertIn('href="/book/"', html)
        self.assertNotIn('In the margins', html)
        chapter = chapter_content.viewer('Obsidian/Quantum Pictures.pdf', '/pdfs/test.pdf', app.pdf_files())
        self.assertIn('Activator</p>', chapter)
        self.assertIn(chapter_content.CHAPTERS['Quantum Pictures']['activator']['text'], chapter)
        self.assertIn('data-pdf-page="1"', chapter)
