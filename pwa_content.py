"""Installable review app metadata shared by the server and static export."""
import json
from pathlib import Path


def manifest(base=''):
    return json.dumps({
        'id': base + '/', 'name': 'Physics Notebook · Daily Review',
        'short_name': 'Physics Review', 'description': 'Recall ideas and review your handwritten physics notebooks, online or offline.',
        'lang': 'en', 'start_url': base + '/notes/review/', 'scope': base + '/',
        'display': 'standalone', 'background_color': '#f7f5ef', 'theme_color': '#244b68',
        'icons': [{'src': base + f'/assets/icons/review-{size}.png', 'sizes': f'{size}x{size}', 'type': 'image/png', 'purpose': 'any maskable'} for size in (192, 512)],
    })


def worker(version):
    return (Path(__file__).parent / 'assets/service-worker.js').read_text().replace('__BUILD_VERSION__', version)


def offline_panel():
    return '''<section id="download-app" class="review-app" aria-labelledby="review-app-title"><div><p class="kicker">Take your notebook with you</p><h2 id="review-app-title">Physics Notebook on your phone.</h2><p>Add Physics Review to your home screen, then download the notebooks here for offline practice.</p><a href="/notes/review/">Open daily review →</a></div><div class="review-app-actions"><button type="button" class="button" data-app-install hidden>Install review app</button><button type="button" class="button" data-offline-download disabled>Download for offline review</button><p data-offline-status role="status" aria-live="polite">Checking offline support…</p><details><summary>Add to your home screen</summary><p>On iPhone, open this page in Safari, tap Share, then Add to Home Screen. On Android, open it in Chrome and choose Install app or Add to Home screen from the menu.</p><p>Open the app while connected and finish the offline download before leaving. Your completion checkmarks stay on this device. Your browser may clear downloaded files to free storage; check the offline status before a trip.</p></details></div></section>'''
