#!/usr/bin/env python3
"""Lint the design-record index against one saved listing of its folder.

Usage: index_lint.py --index INDEX.md --listing design_ls.txt [--json] [--max-main-lines N]

Reads two files and nothing else. Exit 0 when no defect is found, 1 otherwise. Defect classes:
  duplicate      a folder entry named by two rows (or twice in one row)
  missing        a listed entry that the listing does not hold
  outside_folder a row whose File names a path outside the folder (a link belongs in Status)
  unlisted       an entry of the listing that no row names
  empty_row      a row that names no file
  no_status      a row without a status
  no_verdict     a row without a verdict, or one outside the allowed set
  bad_evidence   an Evidence cell outside the allowed set (grouped form only)
  long_row       a row line above 300 characters
  long_status    a status above 160 characters (grouped form only)
  archive_status an archived row whose status does not start with SUPERSEDED_BY: or CLOSED:
  dangling_supersede  a SUPERSEDED_BY: target that the listing does not hold
  main_too_long  more lines above the archive section than --max-main-lines
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


def lint(text, listing, max_main_lines=None):
    """Return a list of defect dicts {class, line, file, text}."""
    rows, tables = indexfmt.parse(text)
    grouped = any('verdict' in ' '.join(cols) for _, cols in tables)
    present = set(listing)
    defects = []

    def add(cls, row=None, name=None, text_=''):
        defects.append({'class': cls, 'line': row.lineno if row else None, 'file': name,
                        'text': text_})

    seen = {}
    for row in rows:
        if not row.files:
            add('empty_row', row, None, (row.raw or '')[:80])
        for name in row.files:
            if name in seen:
                add('duplicate', row, name, 'first listed on line %d' % seen[name])
            else:
                seen[name] = row.lineno
            if '/' in name:
                add('outside_folder', row, name)
            elif name not in present:
                add('missing', row, name)
        if not (row.status or '').strip():
            add('no_status', row, row.files[0] if row.files else None)
        verdict = (row.verdict or '').strip()
        if verdict not in indexfmt.VERDICTS:
            add('no_verdict', row, row.files[0] if row.files else None, verdict)
        if grouped:
            evidence = (row.evidence or '').strip()
            if evidence not in indexfmt.EVIDENCE:
                add('bad_evidence', row, row.files[0] if row.files else None, evidence)
            if len((row.status or '').strip()) > indexfmt.MAX_STATUS_CHARS:
                add('long_status', row, row.files[0] if row.files else None,
                    '%d chars' % len(row.status.strip()))
        if len(row.raw) > indexfmt.MAX_ROW_CHARS:
            add('long_row', row, row.files[0] if row.files else None, '%d chars' % len(row.raw))
        if row.archived:
            status = (row.status or '').strip()
            if not status.startswith(indexfmt.ARCHIVE_PREFIXES):
                add('archive_status', row, row.files[0] if row.files else None, status[:60])
            target = re.match(r'^SUPERSEDED_BY:\s*`?([^`;,\s]+)`?', status)
            if target and target.group(1).rstrip('/') not in present:
                add('dangling_supersede', row, target.group(1))
    for name in listing:
        if name not in seen:
            add('unlisted', None, name)
    if max_main_lines is not None:
        lines = text.splitlines()
        main = len(lines)
        for idx, line in enumerate(lines):
            if re.match(r'^##\s+Archive', line, re.I):
                main = idx
                break
        if main > max_main_lines:
            add('main_too_long', None, None, '%d lines above the archive' % main)
    return defects


def summarize(defects):
    counts = {}
    for item in defects:
        counts[item['class']] = counts.get(item['class'], 0) + 1
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--index', required=True)
    parser.add_argument('--listing', required=True, help='saved one-name-per-line ls of the folder')
    parser.add_argument('--ignore', action='append', default=None,
                        help='listing names to skip (default INDEX.md)')
    parser.add_argument('--max-main-lines', type=int, default=None)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    ignore = tuple(args.ignore) if args.ignore else ('INDEX.md',)
    with open(args.index, 'r') as handle:
        text = handle.read()
    listing = indexfmt.read_listing(args.listing, ignore=ignore)
    defects = lint(text, listing, args.max_main_lines)
    counts = summarize(defects)
    if args.json:
        sys.stdout.write(json.dumps({'counts': counts, 'defects': defects}, indent=1,
                                    sort_keys=True) + '\n')
    else:
        for item in defects:
            sys.stdout.write('%s\tline=%s\t%s\t%s\n' % (item['class'], item['line'], item['file'],
                                                       item['text']))
        sys.stdout.write('SUMMARY %s\n' % (json.dumps(counts, sort_keys=True) if counts else 'clean'))
    return 1 if defects else 0


if __name__ == '__main__':
    sys.exit(main())
