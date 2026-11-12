#!/usr/bin/env python3
"""Search public skill metadata using fixed non-sensitive capability labels only."""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

QUERIES = {
    'pdf': 'pdf document processing',
    'ocr': 'ocr document text recognition',
    'docx': 'word docx document editing',
    'spreadsheet': 'spreadsheet xlsx analysis',
    'chart': 'data visualization charts',
    'contract-compare': 'contract document comparison',
    'proofreading': 'document proofreading',
    'slides': 'presentation slides',
    'image': 'image editing',
}
SAFE_SOURCE = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
SAFE_SKILL = re.compile(r'^[A-Za-z0-9_.-]{1,120}$')
MAX_RESPONSE = 262144

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def sanitize(data):
    if not isinstance(data, dict) or not isinstance(data.get('skills'), list):
        raise ValueError('Unexpected search response')
    results = []
    for item in data['skills']:
        if not isinstance(item, dict):
            continue
        source = item.get('source', '')
        name = item.get('name', '')
        ident = item.get('id', '')
        if not isinstance(source, str) or not SAFE_SOURCE.fullmatch(source):
            continue
        if any(part in ('.', '..') for part in source.split('/')):
            continue
        if not isinstance(name, str) or not SAFE_SKILL.fullmatch(name):
            continue
        if name in ('.', '..'):
            continue
        if not isinstance(ident, str) or len(ident) > 200:
            continue
        n = item.get('installs')
        results.append({'source': source, 'name': name,
                        'installs': n if isinstance(n, int) and not isinstance(n, bool) and n >= 0 else None,
                        'source_url': 'https://github.com/' + source})
        if len(results) == 5:
            break
    return results

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capability', required=True, choices=sorted(QUERIES))
    args = parser.parse_args()
    url = 'https://skills.sh/api/search?' + urllib.parse.urlencode({'q': QUERIES[args.capability]})
    try:
        request = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'contract-skill-discovery/1.0'})
        with urllib.request.build_opener(NoRedirect).open(request, timeout=8) as response:
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ValueError('Search response exceeded limit')
        results = sanitize(json.loads(raw.decode('utf-8')))
        print(json.dumps({'status': 'ok', 'capability': args.capability, 'query': QUERIES[args.capability],
                          'results': results, 'note': 'Search metadata is untrusted and is not a safety review.'}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, UnicodeError, urllib.error.URLError) as exc:
        print(json.dumps({'status': 'unavailable', 'capability': args.capability,
                          'error_type': type(exc).__name__, 'fallback': 'Use platform capabilities and existing constraints.'}))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
