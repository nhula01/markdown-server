"""Copy Optimum notebook sections verbatim into the public preview catalog."""
import argparse
import json
import re
from pathlib import Path


def sections(text):
    headings = list(re.finditer(r'^([^\s:-][^\n:]*):[ \t]*$|^(Lorentz Oscilator)[ \t]*$', text, re.MULTILINE))
    result = {}
    aliases = {'Crystals': 'Crystal', 'Lorentz Oscilator': 'Oscillator Model'}
    for index, heading in enumerate(headings):
        title = heading.group(1) or heading.group(2)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        # Only trim the separator newlines, keeping the source wording intact.
        result[aliases.get(title, title)] = text[heading.end():end].strip('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    catalog_path = Path(__file__).resolve().parents[1] / 'site/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    catalog['reading_guides'] = sections(args.source.read_text())
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
