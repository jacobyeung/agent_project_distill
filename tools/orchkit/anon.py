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
import bz2
import gzip
import io
import json
import lzma
import os
import re
import sys
import tarfile
import zipfile

WORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ANON_WORDS.txt')
JOB_NAME = re.compile(r'^a15_cot_ap[0-9a-f]{16}\Z')
MAX_BLOB = 256 * 1024 * 1024
MAX_DEPTH = 8


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
    """Text rules over the bytes read as Latin-1, and again with NUL bytes dropped, so UTF-16 and
    UTF-32 text cannot hide a word."""
    hits = scan_text(where, data.decode('latin-1'), rules, 'text')
    if b'\x00' in data:
        seen = set(hit['rule'] for hit in hits)
        hits.extend(hit for hit in scan_text(where, data.replace(b'\x00', b'').decode('latin-1'),
                                             rules, 'text') if hit['rule'] not in seen)
    return hits


MAGIC = ((b'\x1f\x8b', 'gz'), (b'BZh', 'bz2'), (b'\xfd7zXZ\x00', 'xz'), (b'PK\x03\x04', 'zip'),
         (b'PK\x05\x06', 'zip'))
NAME_JSON = ('CONFIG.json', 'PINS.json', 'JOB.json', 'DRYRUN_REPORT.json')


def _compression(data):
    for magic, kind in MAGIC:
        if data.startswith(magic):
            return kind
    return None


def _decompress(kind, data):
    """Decompressed bytes bounded by MAX_BLOB + 1, or None when the stream does not decode, does
    not end, or carries bytes after its end."""
    try:
        if kind == 'gz':
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as handle:
                return handle.read(MAX_BLOB + 1)
        if kind in ('bz2', 'xz'):
            engine = bz2.BZ2Decompressor() if kind == 'bz2' else lzma.LZMADecompressor()
            out = engine.decompress(data, MAX_BLOB + 1)
            if engine.unused_data or not engine.eof:
                return None
            return out
    except (OSError, EOFError, ValueError, lzma.LZMAError):
        return None
    return None


def _is_tar(name, data):
    if len(data) > 262 and data[257:262] == b'ustar':
        return True
    name = re.sub(r'(!(gz|bz2|xz))+$', '', name.lower())
    return name.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz'))


def _open_tar(data):
    try:
        return tarfile.open(fileobj=io.BytesIO(data), mode='r:')
    except (tarfile.TarError, EOFError, OSError):
        return None


def _meta(item):
    """Header text of a tar member that is not its name or body: owner names, link, pax fields."""
    parts = [item.uname or '', item.gname or '', item.linkname or '']
    for key, value in sorted((item.pax_headers or {}).items()):
        parts.extend([key, value])
    return '\n'.join(part for part in parts if part)


def _expand(where, data, depth):
    """Yield (where, bytes or None, kind) for a blob and everything inside it, failing closed:
    a blob that is too large, nested too deep, compressed but undecodable, or a special tar member
    is yielded with bytes None."""
    if len(data) > MAX_BLOB:
        yield where, None, 'too-large'
        return
    kind = _compression(data)
    if kind in ('gz', 'bz2', 'xz'):
        if depth >= MAX_DEPTH:
            yield where, None, 'too-deep'
            return
        yield where, data, 'archive'
        inner = _decompress(kind, data)
        if inner is None:
            yield where, None, 'undecodable'
            return
        if len(inner) > MAX_BLOB:
            yield where, None, 'too-large'
            return
        for row in _expand(where + '!' + kind, inner, depth + 1):
            yield row
        return
    if kind == 'zip':
        if depth >= MAX_DEPTH:
            yield where, None, 'too-deep'
            return
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
            infos = archive.infolist()
        except (zipfile.BadZipFile, OSError, ValueError):
            yield where, None, 'undecodable'
            return
        yield where, data, 'archive'
        for info in infos:
            name = where + '!/' + info.filename
            if info.file_size > MAX_BLOB:
                yield name, None, 'too-large'
                continue
            try:
                blob = archive.read(info)
            except (zipfile.BadZipFile, OSError, ValueError, NotImplementedError):
                yield name, None, 'undecodable'
                continue
            if info.comment:
                yield name, info.comment, 'meta'
            for row in _expand(name, blob, depth + 1):
                yield row
        return
    archive = _open_tar(data) if _is_tar(where, data) else None
    if archive is None:
        yield where, data, 'file'
        return
    if depth >= MAX_DEPTH:
        yield where, None, 'too-deep'
        return
    yield where, data, 'archive'
    with archive:
        for item in archive:
            name = where + '!/' + item.name
            meta = _meta(item)
            if meta:
                yield name, meta.encode('utf-8', 'replace'), 'meta'
            if item.issym() or item.islnk():
                yield name, item.linkname.encode('utf-8', 'replace'), 'link'
            elif item.isdir():
                yield name, b'', 'dir'
            elif not item.isfile():
                yield name, None, 'special'
            elif item.size > MAX_BLOB:
                yield name, None, 'too-large'
            else:
                for row in _expand(name, archive.extractfile(item).read(), depth + 1):
                    yield row


def walk_blobs(root, nested=True):
    """Yield (where, bytes) for every regular file under root, and for every member of every
    archive when nested. where is the path relative to root; an archive member is
    'a.tar!/member'. A symlink yields its target text. A single file root yields its base name.
    An archive is represented by its members, not by its own bytes."""
    for where, data, kind in _walk(root, nested):
        if data is not None and kind in ('file', 'link'):
            yield where, data


def walk_all(root):
    """Yield (where, bytes or None, kind) for everything under root, archive raw bytes and header
    fields included; bytes are None for a blob that cannot be read (see _expand)."""
    for row in _walk(root):
        yield row


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
        if not os.path.isfile(full):
            yield where, None, 'special'
            continue
        if os.path.getsize(full) > MAX_BLOB:
            yield where, None, 'too-large'
            continue
        with open(full, 'rb') as handle:
            data = handle.read()
        if not nested:
            yield where, data, 'file'
            continue
        for row in _expand(where, data, 0):
            yield row


def _json_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            for text in _json_strings(item):
                yield text
    elif isinstance(value, list):
        for item in value:
            for text in _json_strings(item):
                yield text
    elif isinstance(value, str):
        yield value


def scan_tree(root, rules):
    """Hits in every name and every byte under root (files, links, archive members at any depth,
    tar header fields), failing closed on anything it cannot read. Every string key and value of
    the top-level CONFIG.json, PINS.json, JOB.json and DRYRUN_REPORT.json is a name."""
    hits = []
    for where, data, kind in _walk(root):
        hits.extend(scan_text(where, where, rules, 'name'))
        if data is None:
            hits.append({'where': where, 'scope': 'size', 'rule': kind})
            continue
        if kind in ('link', 'meta'):
            hits.extend(scan_text(where, data.decode('utf-8', 'replace'), rules, 'name'))
        elif data:
            hits.extend(scan_bytes(where, data, rules))
        if kind == 'file' and where in NAME_JSON:
            try:
                parsed = json.loads(data.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                hits.append({'where': where, 'scope': 'name', 'rule': 'unparseable-json'})
                continue
            for text in _json_strings(parsed):
                hits.extend(row for row in scan_text(where, text, rules, 'name')
                            if row not in hits)
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
