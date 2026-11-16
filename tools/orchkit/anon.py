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
import unicodedata
import zipfile
import zlib

WORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ANON_WORDS.txt')
JOB_NAME = re.compile(r'^a15_cot_ap[0-9a-f]{16}\Z')
MAX_BLOB = 256 * 1024 * 1024
MAX_DEPTH = 8
LZMA_STREAMS = 64


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
    normal = _normal_paths(text) if '/.' in text else None
    for rule in rules:
        if rule.scope == 'name' and scope != 'name':
            continue
        if rule.regex.search(text) or (normal is not None and rule.regex.search(normal)):
            hits.append({'where': where, 'scope': scope, 'rule': rule.label})
    return hits


PATH_END = r'(?![^/\s"\',;:)\]}])'
DOT = re.compile(r'/\.' + PATH_END)
DOTDOT = re.compile(r'/[^/\s"\',;:=(\[{]+/\.\.' + PATH_END)
ROOT_DOTDOT = re.compile(r'(?<![^\s"\'=:,;(\[{])/\.\.(?=/)')


def _normal_paths(text):
    """The text with every path written lexically normal, as os.path.normpath would: '/./' and
    'x/../' components dropped, '/..' at the root dropped, repeated slashes kept (rules use /+)."""
    previous = None
    while previous != text:
        previous = text
        text = ROOT_DOTDOT.sub('', DOTDOT.sub('', DOT.sub('', text)))
    return text


ESCAPE = re.compile(r'\\(?:u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8})|x([0-9a-fA-F]{2})|([0-7]{1,3})|N\{([^}]{1,80})\})')


def _unescape(text):
    """Resolve JSON and Python escapes: \\uXXXX, \\UXXXXXXXX, \\xXX, octal \\NNN, \\N{NAME}; any other
    backslash pair (\\/, \\n) becomes its second character."""
    def one(match):
        if match.group(5) is not None:
            try:
                return unicodedata.lookup(match.group(5))
            except KeyError:
                return ''
        if match.group(4) is not None:
            return chr(int(match.group(4), 8))
        code = int(match.group(1) or match.group(2) or match.group(3), 16)
        return chr(code) if code < 0x110000 else ''
    text = re.sub(r'\\(?:\r\n|\r|\n)', '', text)
    return re.sub(r'\\([\s\S])', r'\1', ESCAPE.sub(one, text))


def text_views(data):
    """Every text reading of a blob that a standard decoder gives: Latin-1, NUL bytes dropped,
    UTF-16 and UTF-32 (either byte order, with or without a BOM), each also with JSON and Python
    escapes (\\uXXXX, \\UXXXXXXXX, \\xXX) resolved."""
    views = [data.decode('latin-1')]
    if b'\x00' in data:
        views.append(data.replace(b'\x00', b'').decode('latin-1'))
        for codec in ('utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le', 'utf-32-be'):
            try:
                views.append(data.decode(codec))
            except (UnicodeDecodeError, ValueError):
                continue
    out = []
    for view in views:
        out.append(view)
        if '\\' in view:
            out.append(_unescape(view))
    return out


def scan_bytes(where, data, rules, scope='text'):
    """Rules over every text view of the bytes (see text_views); one hit per rule."""
    hits, seen = [], set()
    for view in text_views(data):
        for hit in scan_text(where, view, rules, scope):
            if hit['rule'] not in seen:
                seen.add(hit['rule'])
                hits.append(hit)
    return hits


MAGIC = ((b'\x1f\x8b', 'gz'), (b'BZh', 'bz2'), (b'\xfd7zXZ\x00', 'xz'), (b'PK\x03\x04', 'zip'),
         (b'PK\x05\x06', 'zip'))
NAME_JSON = ('CONFIG.json', 'PINS.json', 'JOB.json', 'DRYRUN_REPORT.json')


UNSUPPORTED = ((b'7z\xbc\xaf\x27\x1c', '7z'), (b'Rar!\x1a\x07', 'rar'), (b'\x28\xb5\x2f\xfd', 'zstd'),
               (b'\x04\x22\x4d\x18', 'lz4'), (b'070707', 'cpio'), (b'070701', 'cpio'),
               (b'070702', 'cpio'), (b'!<arch>\n', 'ar'), (b'hsqs', 'squashfs'), (b'\x89LZO', 'lzo'),
               (b'LZIP', 'lzip'), (b'\x1f\x9d', 'compress'), (b'MSCF', 'cab'))


def _gzip_header_text(data):
    """The stored extra field, file name and comment of every gzip member (RFC 1952), as bytes.
    Members follow one another as Python's gzip reads them, NUL padding between them skipped."""
    out, at = [], 0
    while len(data) - at >= 10 and data.startswith(b'\x1f\x8b', at):
        flags, at = data[at + 3], at + 10
        if flags & 4:
            size = int.from_bytes(data[at:at + 2], 'little')
            out.append(data[at + 2:at + 2 + size])
            at += 2 + size
        for bit in (8, 16):
            if flags & bit:
                end = data.find(b'\x00', at)
                end = len(data) if end < 0 else end
                out.append(data[at:end])
                at = end + 1
        if flags & 2:
            at += 2
        engine, chunk, produced = zlib.decompressobj(-zlib.MAX_WBITS), data[at:], 0
        try:
            while not engine.eof and produced <= MAX_BLOB:
                piece = engine.decompress(chunk, 1 << 20)
                chunk = engine.unconsumed_tail
                produced += len(piece)
                if not piece and not chunk:
                    break
        except zlib.error:
            break
        if not engine.eof:
            break
        at = len(data) - len(engine.unused_data) + 8
        while at < len(data) and data[at] == 0:
            at += 1
    return b'\n'.join(part for part in out if part)


def _zlib_header(data):
    """A zlib header (RFC 1950) of any window size: deflate, CINFO <= 7, FCHECK valid."""
    return len(data) >= 2 and data[0] & 15 == 8 and data[0] >> 4 <= 7 and \
        (data[0] * 256 + data[1]) % 31 == 0


def _lzma_alone_start(data):
    """An LZMA-alone header the standard decoder accepts: any lc/lp/pb property byte, any
    dictionary size, a valid size field; the decoder itself is the judge."""
    if len(data) < 13 or data[0] >= 225:
        return False
    try:
        lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(data[:4096], 1)
    except (lzma.LZMAError, MemoryError):
        return False
    return True


def _interpretations(where, data):
    """Every container reading of a blob: a compression at its start, a zip anywhere (Python
    reads a zip with a prefix), a tar; a container Python cannot open is 'unsupported'."""
    kinds = [kind for magic, kind in MAGIC[:3] if data.startswith(magic)]
    if _lzma_alone_start(data):
        kinds.append('lzma')
    if _zlib_header(data) and _decompress('zlib', data) is not None:
        kinds.append('zlib')
    if any(data.startswith(magic) for magic, _ in UNSUPPORTED):
        kinds.append('unsupported')
    try:
        zipped = zipfile.is_zipfile(io.BytesIO(data))
    except (OSError, ValueError):
        zipped = False
    if zipped:
        kinds.append('zip')
    elif b'PK\x03\x04' in data or b'PK\x05\x06' in data:
        kinds.append('unsupported')
    if len(data) > 262 and data[257:262] == b'ustar':
        kinds.append('tar')
    elif len(data) >= 512:
        archive = _open_tar(data)
        if archive is not None:
            archive.close()
            kinds.append('tar')
        elif _tar_like(data):
            kinds.append('unsupported')
    return kinds


OCTAL = re.compile(rb'^[0-7 ]*\x00?[ \x00]*$')


def _tar_like(data):
    """A first block shaped like a tar header (a printable name, octal mode, size and checksum
    fields) that tarfile still refuses: a damaged tar, refused rather than read as text."""
    head = data[:512]
    name = head[:100].rstrip(b'\x00')
    if not name or any(byte < 32 or byte == 127 for byte in name):
        return False
    return all(OCTAL.match(head[start:end]) and head[start:end].strip(b' \x00')
               for start, end in ((100, 108), (124, 136), (148, 156)))


def _decompress(kind, data):
    """Decompressed bytes bounded by MAX_BLOB + 1, or None when the stream does not decode, does
    not end, or carries bytes after its end."""
    try:
        if kind == 'gz':
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as handle:
                return handle.read(MAX_BLOB + 1)
        if kind == 'zlib':
            return _zlib_stream(data)
        if kind == 'lzma':
            return _lzma_alone(data)
        if kind in ('bz2', 'xz'):
            engine = bz2.BZ2Decompressor() if kind == 'bz2' else lzma.LZMADecompressor(
                format=lzma.FORMAT_ALONE if kind == 'lzma' else lzma.FORMAT_AUTO)
            out = engine.decompress(data, MAX_BLOB + 1)
            if engine.unused_data or not engine.eof:
                return None
            return out
    except (OSError, EOFError, ValueError, lzma.LZMAError, zlib.error):
        return None
    return None


def _zlib_stream(data):
    """What zlib's incremental decoder yields, 64 KiB of input at a time: the output up to an
    error, the end of the stream, or the end of the input (bytes after the stream stay in the
    container's own scan); None when nothing decodes."""
    engine, out, size = zlib.decompressobj(), [], 0
    for at in range(0, len(data), 1 << 16):
        try:
            piece = engine.decompress(data[at:at + (1 << 16)], MAX_BLOB + 1 - size)
        except zlib.error:
            break
        out.append(piece)
        size += len(piece)
        if engine.eof or size > MAX_BLOB or engine.unconsumed_tail:
            break
    return b''.join(out) if out else None


def _lzma_alone(data):
    """Decode as lzma.decompress(FORMAT_ALONE) does: streams one after another (a run of 18 NUL
    bytes is one empty stream), the output of a truncated last stream kept. None when the first
    stream fails or more than LZMA_STREAMS streams follow."""
    out, size, at = [], 0, 0
    for _ in range(LZMA_STREAMS):
        zeros = len(data) - at - len(data[at:].lstrip(b'\x00'))
        if zeros >= 18:
            at += zeros - zeros % 18
            out.append(b'')
        if at >= len(data) or (out and len(data) - at < 13):
            return b''.join(out)
        engine = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        try:
            piece = engine.decompress(data[at:], MAX_BLOB + 1 - size)
        except (lzma.LZMAError, MemoryError):
            return b''.join(out) if out else None
        out.append(piece)
        size += len(piece)
        if size > MAX_BLOB or not engine.eof or not engine.unused_data:
            return b''.join(out)
        at = len(data) - len(engine.unused_data)
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
    """Yield (where, bytes or None, kind) for a blob and everything inside it under every
    container reading that applies, failing closed: a blob that is too large, nested too deep,
    undecodable, in an unsupported container, or a special tar member is yielded with bytes None.
    A container's own bytes are yielded too (kind 'archive'), so its headers are scanned."""
    if len(data) > MAX_BLOB:
        yield where, None, 'too-large'
        return
    kinds = _interpretations(where, data)
    if not kinds:
        yield where, data, 'file'
        return
    if depth >= MAX_DEPTH:
        yield where, None, 'too-deep'
        return
    yield where, data, 'archive'
    for kind in kinds:
        if kind == 'unsupported':
            yield where, None, 'unsupported-container'
        elif kind in ('gz', 'bz2', 'xz', 'lzma', 'zlib'):
            header = _gzip_header_text(data) if kind == 'gz' else b''
            if header:
                yield where + '!gzip-header', header, 'meta'
            inner = _decompress(kind, data)
            if inner is None:
                yield where, None, 'undecodable'
            elif len(inner) > MAX_BLOB:
                yield where, None, 'too-large'
            else:
                for row in _expand(where + '!' + kind, inner, depth + 1):
                    yield row
        elif kind == 'zip':
            for row in _zip_members(where, data, depth):
                yield row
        else:
            for row in _tar_members(where, data, depth):
                yield row


def _zip_members(where, data, depth):
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        infos = archive.infolist()
    except (zipfile.BadZipFile, OSError, ValueError):
        yield where, None, 'undecodable'
        return
    if archive.comment:
        yield where + '!/', archive.comment, 'meta'
    for info in infos:
        name = where + '!/' + info.filename
        if info.comment:
            yield name, info.comment, 'meta'
        if info.extra:
            yield name, info.extra, 'meta'
        if info.file_size > MAX_BLOB:
            yield name, None, 'too-large'
            continue
        try:
            blob = archive.read(info)
        except (zipfile.BadZipFile, OSError, ValueError, NotImplementedError, RuntimeError):
            yield name, None, 'undecodable'
            continue
        for row in _expand(name, blob, depth + 1):
            yield row


def _tar_members(where, data, depth):
    archive = _open_tar(data)
    if archive is None:
        yield where, None, 'undecodable'
        return
    try:
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
    except (tarfile.TarError, EOFError, OSError):
        yield where, None, 'undecodable'


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
    """Every key and string of a JSON value parsed with object_pairs_hook=list (objects become
    lists of [key, value] pairs, so duplicate keys are kept)."""
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        yield value[0]
        for text in _json_strings(value[1]):
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
            hits.extend(scan_bytes(where, data, rules, 'name'))
        elif data:
            hits.extend(scan_bytes(where, data, rules))
        if kind == 'file' and where in NAME_JSON:
            hits.extend(row for row in scan_bytes(where, data, rules, 'name') if row not in hits)
            try:
                parsed = json.loads(data.decode('utf-8'), object_pairs_hook=list)
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
