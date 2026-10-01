"""Import only curated questions and numbered trail links from the Obsidian note."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lead_content import parse_leads

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, nargs='?', default=Path('/Users/nph/Documents/MyBrain/Follow a thread.md'))
    args = parser.parse_args()
    # Validate everything before writing. Other vault prose is never imported.
    leads = parse_leads(args.source.read_text())
    target = Path(__file__).resolve().parents[1] / 'site/leads.md'
    intro = target.read_text().split('\n## ', 1)[0]
    text = intro + '\n\n' + '\n\n'.join('## ' + lead['question'] + '\n' + '\n'.join(f'{i}. [[{title}]]' for i, title in enumerate(lead['steps'], 1)) for lead in leads) + '\n'
    if target.read_text() != text:
        target.write_text(text)
        print(f'Imported {len(leads)} curated leads')
