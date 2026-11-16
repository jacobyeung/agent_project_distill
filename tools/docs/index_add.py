#!/usr/bin/env python3
"""Add one row to the grouped design-record index under a lock.

Usage: index_add.py --index FILE --topic T --file F --status S --verdict V --evidence E
                    [--group "New records"] [--folder DIR]

The row lands at the end of the table of section `## <group>` (default "New records"); when that
section is missing it is created just above the archive section (or at the end of the file when
there is no archive). The orchestrator sorts new rows into their topic groups when it next swaps
the index. The command refuses a file the index already names, a verdict or evidence outside the
allowed sets, a status above 160 characters, a row above 300 characters, a pipe or newline in a
cell, and, with --folder, a file that the folder does not hold.

Writers serialize on an flock of `<index>.lock` (a sidecar that is created once and left in
place), read the index inside the lock, and replace it with util.atomic_write, so two parallel
adds both land and a reader never sees a partial file. Standard library only; Python 3.6-safe.
"""
import argparse
import fcntl
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import indexfmt  # noqa: E402
from orchkit import util  # noqa: E402

HEADER = '| Topic | File | Status | Verdict | Evidence |'
SEPARATOR = '|---|---|---|---|---|'


class Refused(Exception):
    pass


def format_row(topic, files, status, verdict, evidence):
    for label, value in (('topic', topic), ('status', status), ('verdict', verdict),
                         ('evidence', evidence)):
        if '|' in value or '\n' in value:
            raise Refused('%s holds a pipe or a newline' % label)
    for name in files:
        if '|' in name or '`' in name or '\n' in name or '/' in name.rstrip('/'):
            raise Refused('file name %r is not a plain folder entry' % name)
    if verdict not in indexfmt.VERDICTS:
        raise Refused('verdict %r is not one of %s' % (verdict, ', '.join(indexfmt.VERDICTS)))
    if evidence not in indexfmt.EVIDENCE:
        raise Refused('evidence %r is not one of %s' % (evidence, ', '.join(indexfmt.EVIDENCE)))
    if not status.strip():
        raise Refused('status is empty')
    if len(status) > indexfmt.MAX_STATUS_CHARS:
        raise Refused('status is %d characters; limit %d' % (len(status), indexfmt.MAX_STATUS_CHARS))
    cell = ' + '.join('`%s`' % name for name in files)
    row = '| %s | %s | %s | %s | %s |' % (topic.strip(), cell, status.strip(), verdict, evidence)
    if len(row) > indexfmt.MAX_ROW_CHARS:
        raise Refused('row is %d characters; limit %d' % (len(row), indexfmt.MAX_ROW_CHARS))
    return row


def insert_row(text, row, group):
    """Return the index text with row appended to the table of section `## group`."""
    lines = text.split('\n')
    trailing_newline = text.endswith('\n')
    if trailing_newline:
        lines = lines[:-1]
    heading = '## ' + group
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx
            break
    if start is None:
        archive = len(lines)
        for idx, line in enumerate(lines):
            if line.strip().lower().startswith('## archive'):
                archive = idx
                break
        block = [heading, '', HEADER, SEPARATOR, row, '']
        if archive > 0 and lines[archive - 1].strip():
            block.insert(0, '')
        lines[archive:archive] = block
    else:
        end = len(lines)
        for idx in range(start + 1, len(lines)):
            if lines[idx].startswith('#'):
                end = idx
                break
        last_row = None
        for idx in range(start + 1, end):
            if lines[idx].strip().startswith('|'):
                last_row = idx
        if last_row is None:
            lines[start + 1:start + 1] = ['', HEADER, SEPARATOR, row]
        else:
            lines.insert(last_row + 1, row)
    out = '\n'.join(lines)
    return out + '\n' if trailing_newline or not text else out


def add(index, topic, files, status, verdict, evidence, group='New records', folder=None):
    """Add one row under the lock; return the row text. Raise Refused on any refusal."""
    if folder is not None:
        for name in files:
            if not os.path.exists(os.path.join(folder, name.rstrip('/'))):
                raise Refused('%s is not in %s' % (name, folder))
    row = format_row(topic, files, status, verdict, evidence)
    lock_path = index + '.lock'
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with open(index, 'r') as handle:
            text = handle.read()
        rows, _ = indexfmt.parse(text)
        named = set(indexfmt.listed_files(rows))
        for name in files:
            if name.rstrip('/') in named:
                raise Refused('%s is already listed' % name)
        util.atomic_write(index, insert_row(text, row, group).encode('utf-8'))
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    return row


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--index', required=True)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--file', required=True, action='append',
                        help='folder entry; repeat for a record and its evidence archives')
    parser.add_argument('--status', required=True)
    parser.add_argument('--verdict', required=True, choices=indexfmt.VERDICTS)
    parser.add_argument('--evidence', required=True, choices=indexfmt.EVIDENCE)
    parser.add_argument('--group', default='New records')
    parser.add_argument('--folder', default=None, help='refuse a file this folder does not hold')
    args = parser.parse_args(argv)
    try:
        row = add(args.index, args.topic, args.file, args.status, args.verdict, args.evidence,
                  args.group, args.folder)
    except Refused as err:
        sys.stderr.write('REFUSED: %s\n' % err)
        return 2
    sys.stdout.write(row + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
