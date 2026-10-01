"""Import complete official PDF exports unchanged, skipping metadata-only churn."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

import pymupdf


def fingerprint(path):
    digest = hashlib.sha256()
    with pymupdf.open(path) as document:
        if document.is_encrypted or not document.page_count:
            raise ValueError(f'Unreadable or empty PDF: {path.name}')
        digest.update(str(document.page_count).encode())
        for page in document:
            digest.update(str(tuple(page.rect)).encode())
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1, 1), alpha=False)
            digest.update(pixmap.samples)
    return digest.digest()


def import_pdfs(source, destination):
    files = sorted(source.glob('*.pdf'))
    if not files:
        raise ValueError('No PDF exports found; leave the existing library intact')
    prepared = []
    # Validate every source before replacing any existing file.
    for path in files:
        if path.is_symlink() or path.name.startswith('.') or path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError(f'Invalid export: {path.name}')
        prepared.append((path, fingerprint(path)))
    destination.mkdir(parents=True, exist_ok=True)
    changed = []
    for path, signature in prepared:
        target = destination / path.name
        if target.exists() and fingerprint(target) == signature:
            print(f'Unchanged: {path.name}')
            continue
        with tempfile.NamedTemporaryFile(dir=destination, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
        try:
            shutil.copyfile(path, temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        changed.append(path.name)
        print(f'Updated: {path.name}')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('export_directory', type=Path)
    parser.add_argument('--destination', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'pdfs' / 'Obsidian')
    args = parser.parse_args()
    import_pdfs(args.export_directory, args.destination)
