#!/usr/bin/env python3
"""One opacity check for everything bound for the batch host.

    anon.py scan [--words ANON_WORDS.txt] PATH ...     files, directories and nested tars
    anon.py name [--words ANON_WORDS.txt] TEXT ...     job names, argument or environment strings

Covers file names, text bytes, members of nested tars (plain or compressed, any depth), the
rendered batch script, argument and environment names and values, and the job name. The word list
(ANON_WORDS.txt beside this file) stays on the cluster side and in the repository; it is never
packed. Rules, one per line, '#' starts a comment:

    name   WORD    case-insensitive substring, checked in names, paths, arguments, environment, job name
    text   WORD    case-insensitive substring, checked in names and in every byte of every file
    textre REGEX   Python regular expression, checked like text

Exit 1 when anything is found; the hit list names the place and the rule, never the matched bytes
around it. Python 3.6-safe, standard library only.
"""
import argparse
import io
import json
import os
import re
import sys
import tarfile

WORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ANON_WORDS.txt')
JOB_NAME = re.compile(r'^a15_cot_ap[0-9a-f]{16}$')
MAX_BLOB = 256 * 1024 * 1024
MAX_DEPTH = 4


class Rule(object):
    def __init__(self, scope, pattern, label):
        self.scope = scope
        self.regex = pattern
        self.label = label

    def __repr__(self):
        return 'Rule(%s %s)' % (self.scope, self.label)


def load_rules(path=None):
    """Parse the word list into rules. A missing list is an error: no list, no check."""
    path = path or os.environ.get('ORCHKIT_ANON_WORDS') or WORDS
    rules = []
    with open(path, 'rb') as handle:
        lines = handle.read().decode('utf-8').splitlines()
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        scope, _, value = line.partition(' ')
        value = value.strip()
        if not value or scope not in ('name', 'text', 'textre'):
            raise ValueError('%s:%d: expected "name|text|textre VALUE"' % (path, number))
        if scope == 'textre':
            rules.append(Rule('text', re.compile(value), 'rule %d' % number))
        else:
            rules.append(Rule(scope, re.compile(re.escape(value), re.I), 'rule %d' % number))
    if not rules:
        raise ValueError('%s holds no rules' % path)
    return rules


def scan_text(where, text, rules, scope='text'):
    """Hits of rules in one string; scope 'name' applies name and text rules, 'text' text rules."""
    hits = []
    for rule in rules:
        if rule.scope == 'name' and scope != 'name':
            continue
        if rule.regex.search(text):
            hits.append({'where': where, 'scope': scope, 'rule': rule.label})
    return hits


def scan_bytes(where, data, rules):
    return scan_text(where, data.decode('latin-1'), rules, 'text')


def _is_tar(name, data):
    lower = name.lower()
    if lower.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz')):
        return True
    return len(data) > 262 and data[257:262] == b'ustar'


def _open_tar(data):
    try:
        return tarfile.open(fileobj=io.BytesIO(data), mode='r:*')
    except (tarfile.TarError, EOFError, OSError):
        return None


def _members(where, archive, depth):
    with archive:
        for item in archive:
            name = where + '!/' + item.name
            if item.issym() or item.islnk():
                yield name, item.linkname.encode('utf-8', 'replace'), 'link'
                continue
            if not item.isfile():
                yield name, b'', 'dir'
                continue
            if item.size > MAX_BLOB:
                yield name, None, 'too-large'
                continue
            blob = archive.extractfile(item).read()
            inner = _open_tar(blob) if depth < MAX_DEPTH and _is_tar(item.name, blob) else None
            if inner is None:
                yield name, blob, 'file'
                continue
            yield name, blob, 'tar'
            for row in _members(name, inner, depth + 1):
                yield row


def walk_blobs(root, nested=True):
    """Yield (where, bytes) for every regular file under root, and for every member of every tar.

    where is the path relative to root; a tar member is 'a.tar!/member'. A symlink yields its
    target text. A single file root yields its own base name. A tar that opens is represented by
    its members, not by its own bytes; a tar that does not open is scanned as plain bytes.
    """
    for where, data, kind in _walk(root, nested):
        if data is not None and kind in ('file', 'link'):
            yield where, data


def _walk(root, nested=True):
    root = str(root)
    if os.path.isfile(root) or os.path.islink(root):
        pairs = [(os.path.basename(root), root)]
    else:
        pairs = []
        for base, dirs, files in os.walk(root):
            dirs.sort()
            for name in sorted(files) + sorted(d for d in dirs if os.path.islink(os.path.join(base, d))):
                full = os.path.join(base, name)
                pairs.append((os.path.relpath(full, root), full))
            for name in sorted(dirs):
                pairs.append((os.path.relpath(os.path.join(base, name), root) + '/', None))
    for where, full in pairs:
        if full is None:
            yield where, b'', 'dir'
            continue
        if os.path.islink(full):
            yield where, os.readlink(full).encode('utf-8', 'replace'), 'link'
            continue
        if os.path.getsize(full) > MAX_BLOB:
            yield where, None, 'too-large'
            continue
        with open(full, 'rb') as handle:
            data = handle.read()
        archive = _open_tar(data) if nested and _is_tar(where, data) else None
        if archive is None:
            yield where, data, 'file'
            continue
        yield where, data, 'tar'
        for row in _members(where, archive, 1):
            yield row


def scan_tree(root, rules):
    """Hits in every name and every byte under root (files, links, nested tar members)."""
    hits = []
    for where, data, kind in _walk(root):
        hits.extend(scan_text(where, where, rules, 'name'))
        if data is None:
            hits.append({'where': where, 'scope': 'size', 'rule': kind})
            continue
        if kind == 'link':
            hits.extend(scan_text(where, data.decode('utf-8', 'replace'), rules, 'name'))
        elif data and kind != 'tar':
            hits.extend(scan_bytes(where, data, rules))
    return hits


def scan_job(rules, job_name=None, script=None, argv=(), env=None):
    """Hits in the parts of a submission that never sit in a file: name, script, argv, environment."""
    hits = []
    if job_name is not None:
        if not JOB_NAME.match(job_name):
            hits.append({'where': 'job_name', 'scope': 'name', 'rule': 'job-name-format'})
        hits.extend(scan_text('job_name', job_name, rules, 'name'))
    if script is not None:
        hits.extend(scan_text('script', script, rules, 'text'))
        for number, line in enumerate(script.splitlines(), 1):
            if line.startswith('#SBATCH'):
                hits.extend(scan_text('script:%d' % number, line, rules, 'name'))
    for index, value in enumerate(argv):
        hits.extend(scan_text('argv[%d]' % index, str(value), rules, 'name'))
    for key, value in sorted((env or {}).items()):
        hits.extend(scan_text('env:name', key, rules, 'name'))
        hits.extend(scan_text('env:%s' % key, str(value), rules, 'name'))
    return hits


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')
    p_scan = sub.add_parser('scan')
    p_scan.add_argument('--words')
    p_scan.add_argument('paths', nargs='+')
    p_name = sub.add_parser('name')
    p_name.add_argument('--words')
    p_name.add_argument('texts', nargs='+')
    args = parser.parse_args(argv)
    if args.command not in ('scan', 'name'):
        parser.print_help()
        return 2
    rules = load_rules(args.words)
    hits = []
    if args.command == 'scan':
        for path in args.paths:
            for hit in scan_tree(path, rules):
                hit['root'] = path
                hits.append(hit)
    else:
        for index, text in enumerate(args.texts):
            hits.extend(scan_text('arg[%d]' % index, text, rules, 'name'))
    print(json.dumps({'hits': len(hits), 'rows': hits}, sort_keys=True, indent=1))
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
