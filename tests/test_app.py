import json, tempfile, unittest
from pathlib import Path
import app

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.previous=app.ROOT; app.ROOT=self.root/'content'; app.ROOT.mkdir()
        (app.ROOT/'notes').mkdir()
        (app.ROOT/'welcome.md').write_text('# Hello\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1))\n\n|A|B|\n|-|-|\n|1|2|',encoding='utf-8')
        (app.ROOT/'notes'/'tiếng Việt.md').write_text('## Nested',encoding='utf-8')
        (self.root/'secret.md').write_text('secret',encoding='utf-8')
        (app.ROOT/'escape.md').symlink_to(self.root/'secret.md')
        (app.ROOT/'.hidden.md').write_text('hidden',encoding='utf-8')
        (app.ROOT/'pic.png').write_bytes(b'\x89PNG\r\n\x1a\n')
    def tearDown(self):
        app.ROOT=self.previous; self.tmp.cleanup()
    def request(self,path,method='GET'):
        capture={}
        def start(status,headers): capture.update(status=status,headers=dict(headers))
        body=b''.join(app.application({'PATH_INFO':path.encode('utf-8').decode('latin-1'),'REQUEST_METHOD':method},start))
        return capture['status'],capture['headers'],body
    def test_rendering_and_sanitization(self):
        status,headers,body=self.request('/docs/welcome.md')
        self.assertEqual(status,'200 OK'); self.assertIn(b'<h1>Hello</h1>',body); self.assertIn(b'<table>',body)
        self.assertNotIn(b'<script>',body); self.assertNotIn(b'href="javascript:',body)
        self.assertIn('Content-Security-Policy',headers)
    def test_raw_and_unicode(self):
        self.assertEqual(self.request('/raw/welcome.md')[2],(app.ROOT/'welcome.md').read_bytes())
        self.assertIn(b'<h2>Nested</h2>',self.request('/docs/notes/tiếng Việt.md')[2])
    def test_index_and_api(self):
        status,_,body=self.request('/api/files')
        self.assertEqual(status,'200 OK'); self.assertEqual(json.loads(body)['files'],['notes/tiếng Việt.md','welcome.md'])
        self.assertIn(b'/docs/notes/ti%E1%BA%BFng%20Vi%E1%BB%87t.md',self.request('/')[2])
    def test_traversal_and_private_paths(self):
        for path in ['/docs/../secret.md','/docs/escape.md','/docs/.hidden.md','/docs/notes/../../secret.md','/docs//etc/passwd','/raw/pic.png','/docs/missing.md']:
            with self.subTest(path=path): self.assertEqual(self.request(path)[0],'404 Not Found')
    def test_methods_images_and_health(self):
        get=self.request('/docs/welcome.md'); head=self.request('/docs/welcome.md','HEAD')
        self.assertEqual(head[2],b''); self.assertEqual(head[1]['Content-Length'],str(len(get[2])))
        self.assertEqual(self.request('/','POST')[0],'405 Method Not Allowed')
        self.assertEqual(self.request('/docs/pic.png')[1]['Content-Type'],'image/png')
        self.assertEqual(json.loads(self.request('/healthz')[2]),{'status':'ok'})
    def test_size_limit(self):
        (app.ROOT/'big.md').write_bytes(b'x'*(app.MAX_TEXT+1))
        self.assertEqual(self.request('/docs/big.md')[0],'413 Content Too Large')

if __name__=='__main__': unittest.main()
