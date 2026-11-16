#!/usr/bin/env python3
"""Lint the current-state entry page (distill_design/CURRENT_STATE.md).

Usage: state_lint.py --state CURRENT_STATE.md --listing design_ls.txt [--index INDEX.md]
                     [--registered NAME ...] [--known paths.txt] [--max-lines 150] [--json]

Checks:
  too_long        more than --max-lines lines (default 150)
  missing_section a required `## ` section is absent (see REQUIRED)
  missing_file    a cited file does not exist: a bare name must be in the folder listing; a path
                  must be in --known (one path per line) or exist on this host
  no_sha          a line cites a registered record without a sha256 (`sha256 <8+ hex>`) for each
                  registered record it cites. Registered records are the rows of --index whose
                  verdict is REGISTERED, plus every --registered NAME.
A cited file is a backticked token that ends in a file extension. Exit 0 when clean, 1 otherwise.
Standard library only; Python 3.6-safe.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import indexfmt  # noqa: E402

REQUIRED = (
    'Goal',
    'Live runs',
    'Nodes',
    'Standing rulings',
    'Results that bind',
    'Do not redo',
    'Ready-to-launch queue',
    'Where to look next',
)
_CITE_RE = re.compile(r'`([^`\s]+\.(?:md|json|jsonl|tsv|tgz|tar|tar\.gz|txt|sh|py))`')
_SHA_RE = re.compile(r'sha256[ :=]+`?[0-9a-f]{8,64}')


def registered_from_index(text):
    rows, _ = indexfmt.parse(text)
    names = set()
    for row in rows:
        if (row.verdict or '').strip() == 'REGISTERED':
            names.update(row.files)
    return names


def lint(text, listing, registered=(), known=(), max_lines=150, exists=os.path.exists):
    defects = []
    lines = text.splitlines()
    if len(lines) > max_lines:
        defects.append({'class': 'too_long', 'line': None, 'text': '%d lines; limit %d'
                        % (len(lines), max_lines)})
    headings = [line.lstrip('#').strip() for line in lines if line.startswith('## ')]
    for name in REQUIRED:
        if not any(h.lower().startswith(name.lower()) for h in headings):
            defects.append({'class': 'missing_section', 'line': None, 'text': name})
    present = set(listing)
    known = set(known)
    registered = set(registered)
    for lineno, line in enumerate(lines, 1):
        cites = _CITE_RE.findall(line)
        reg_count = 0
        for cite in cites:
            if '/' in cite:
                ok = cite in known or exists(cite)
                base = os.path.basename(cite)
            else:
                ok = cite in present
                base = cite
            if not ok:
                defects.append({'class': 'missing_file', 'line': lineno, 'text': cite})
            if base in registered:
                reg_count += 1
        if reg_count and len(_SHA_RE.findall(line)) < reg_count:
            defects.append({'class': 'no_sha', 'line': lineno,
                            'text': '%d registered record(s), %d sha256'
                            % (reg_count, len(_SHA_RE.findall(line)))})
    return defects


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--state', required=True)
    parser.add_argument('--listing', required=True)
    parser.add_argument('--index', default=None)
    parser.add_argument('--registered', action='append', default=[])
    parser.add_argument('--known', default=None, help='file of paths known to exist')
    parser.add_argument('--max-lines', type=int, default=150)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    with open(args.state, 'r') as handle:
        text = handle.read()
    listing = indexfmt.read_listing(args.listing, ignore=())
    registered = set(args.registered)
    if args.index:
        with open(args.index, 'r') as handle:
            registered |= registered_from_index(handle.read())
    known = []
    if args.known:
        with open(args.known, 'r') as handle:
            known = [line.strip() for line in handle if line.strip()]
    defects = lint(text, listing, registered, known, args.max_lines)
    if args.json:
        sys.stdout.write(json.dumps({'defects': defects}, indent=1, sort_keys=True) + '\n')
    else:
        for item in defects:
            sys.stdout.write('%s\tline=%s\t%s\n' % (item['class'], item['line'], item['text']))
        sys.stdout.write('SUMMARY %s\n' % ('%d defect(s)' % len(defects) if defects else 'clean'))
    return 1 if defects else 0


if __name__ == '__main__':
    sys.exit(main())
