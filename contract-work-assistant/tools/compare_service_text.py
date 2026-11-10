#!/usr/bin/env python3
"""Read-only textual comparison of two UTF-8 TXT or DOCX documents."""
import argparse
import difflib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
HEADING = re.compile(r'^第[一二三四五六七八九十百千万零〇两0-9]+条\s*[:：、.．]?\s*(.{1,35})$')

def heading_candidates(first, second):
    """Identify unambiguous exact titles, never semantic equivalence."""
    def index(rows):
        found = {}
        for location, text in rows:
            match = HEADING.match(text.strip())
            if not match:
                continue
            title = match.group(1).strip().rstrip('：:')
            # A sentence or numbered clause body is not safely identifiable as a title.
            if not title or re.search(r'[。；;！？!?\n]', title):
                continue
            found.setdefault(title, []).append({'location': location, 'text': text})
        return found
    a, b = index(first), index(second)
    matches, ambiguous = [], []
    for title in sorted(a.keys() & b.keys()):
        item = {'heading': title, 'first': a[title], 'second': b[title]}
        (matches if len(a[title]) == len(b[title]) == 1 else ambiguous).append(item)
    return {'unique_title_candidates': matches, 'ambiguous_titles': ambiguous,
            'only_first_titles': sorted(a.keys() - b.keys()),
            'only_second_titles': sorted(b.keys() - a.keys())}

def read_document(path):
    if path.suffix.lower() == '.txt':
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        return [(f'line {i}', line) for i, line in enumerate(lines, 1) if line.strip()]
    if path.suffix.lower() != '.docx':
        raise ValueError('Only UTF-8 TXT and DOCX are supported; PDF and DOC are not supported')
    with zipfile.ZipFile(path) as package:
        root = ET.fromstring(package.read('word/document.xml'))
    paragraphs = root.findall('.//' + W + 'body//' + W + 'p')
    result = []
    for i, paragraph in enumerate(paragraphs, 1):
        text = ''.join(node.text or '' for node in paragraph.iter(W + 't'))
        if text.strip():
            result.append((f'body paragraph {i}', text))
    return result

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    args = parser.parse_args()
    try:
        a, b = read_document(args.first), read_document(args.second)
        changes = []
        matcher = difflib.SequenceMatcher(None, [x[1] for x in a], [x[1] for x in b], autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                changes.append({'operation': tag, 'first': [{'location': x, 'text': y} for x, y in a[i1:i2]],
                                'second': [{'location': x, 'text': y} for x, y in b[j1:j2]]})
        result = {'files': [str(args.first), str(args.second)], 'nonempty_paragraph_or_line_counts': [len(a), len(b)],
                  'changes': changes, 'heading_candidates': heading_candidates(a, b),
                  'limitations': ['Heading matches are exact title candidates only, not evidence of semantic equivalence.',
                    'Text-sequence differences only; not semantic or legal conclusions.',
                    'DOCX: document body paragraphs and table paragraphs only; headers, footers, notes, comments, text boxes, images and revisions are not fully covered.',
                    'TXT line or DOCX body paragraph positions are not page numbers.', 'Results may include sensitive source text.']}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, UnicodeError, ET.ParseError, zipfile.BadZipFile, KeyError) as exc:
        print(f'Cannot compare: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
