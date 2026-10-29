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
            self.assertEqual(len(reader.pages), 6)  # 2 front matter + 2 dividers + 2 notes
            matter, quantum = entries[1:3]
            self.assertEqual(matter['notes'][0]['page'], 4)
            self.assertEqual(quantum['notes'][0]['page'], 6)
            self.assertEqual(float(reader.pages[3].mediabox.width), 501)
            self.assertEqual(float(reader.pages[5].mediabox.width), 500)
            self.assertEqual(len(reader.outline), 4)  # topic and nested note per section
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
