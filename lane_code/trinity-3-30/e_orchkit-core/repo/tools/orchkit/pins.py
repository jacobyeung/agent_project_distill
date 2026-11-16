#!/usr/bin/env python3
"""Pin manifest (orchkit-pins-v1): the only place in a kit that records a per-file hash.

    pins.py build  --root DIR --spec SPEC.json --out PINS.json
    pins.py verify --manifest PINS.json --root DIR
    pins.py check  --kit DIR [--allow FILE:FIELD ...]   the single-place invariant
    pins.py audit  --kit OLD_KIT_DIR [--out AUDIT.json]  duplicate-pin groups in an old-style kit

SPEC.json: {"commit": null, "source_seal": null,
            "entries": [{"role", "logical_path", "file": "<path under --root; default logical_path>",
                         "source": {"kind", "uri", "generation"} (default {"kind": "file", "uri": logical_path}),
                         "standin": "<optional>"}]}

The single-place invariant: outside PINS.json a kit may hold a 64-hex string only when it is the kit
identity (kit_pins_sha256), the config identity (sha256 of CONFIG.json), or a value at an
allowlisted data field that equals the current entry's sha256. Any other 64-hex string, including a
stale copy that matches no entry, fails. Trinity-side; Python 3.6-safe, standard library only.
"""
import argparse
import json
import os
import re
import sys

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import orchkit  # noqa: F401
    __package__ = 'orchkit'  # noqa: A001
from . import util  # noqa: E402
from .anon import walk_blobs  # noqa: E402

SCHEMA = 'orchkit-pins-v1'
ROLES = ('code', 'config', 'input', 'weights', 'env', 'record')
KINDS = ('file', 'gcs', 'orchard')
MANIFEST = 'PINS.json'
CONFIG = 'CONFIG.json'
HEX64 = re.compile(r'(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])')
HEX_FULL = re.compile(r'^[0-9a-f]{64}\Z')
DEFAULT_ALLOW = (('CONFIG.json', 'records[].sha256'),)
ZERO = '0' * 64


class PinError(ValueError):
    pass


def _logical(path):
    if not isinstance(path, str) or not path or path.startswith('/') or '\x00' in path:
        raise PinError('logical_path must be a relative path: %r' % (path,))
    parts = path.split('/')
    if any(part in ('', '.', '..') for part in parts):
        raise PinError('logical_path must be normalized: %r' % (path,))
    return path


def validate_manifest(manifest):
    """Raise PinError unless manifest is a well-formed orchkit-pins-v1 value."""
    if not isinstance(manifest, dict) or manifest.get('schema') != SCHEMA:
        raise PinError('not an %s manifest' % SCHEMA)
    required = {'schema', 'created_utc', 'commit', 'source_seal', 'entries'}
    if set(manifest) != required:
        raise PinError('manifest keys differ: %s' % sorted(set(manifest) ^ required))
    seen = set()
    previous = None
    for entry in manifest['entries']:
        keys = set(entry)
        if not {'role', 'logical_path', 'bytes', 'sha256', 'source'} <= keys or not keys <= {
                'role', 'logical_path', 'bytes', 'sha256', 'source', 'standin'}:
            raise PinError('entry keys differ: %s' % sorted(keys))
        path = _logical(entry['logical_path'])
        if path in seen:
            raise PinError('repeated logical_path: %s' % path)
        seen.add(path)
        if previous is not None and path < previous:
            raise PinError('entries are not sorted by logical_path at %s' % path)
        previous = path
        if entry['role'] not in ROLES:
            raise PinError('unknown role %r for %s' % (entry['role'], path))
        if type(entry['bytes']) is not int or entry['bytes'] < 0:
            raise PinError('bytes must be a non-negative integer for %s' % path)
        if not isinstance(entry['sha256'], str) or not HEX_FULL.match(entry['sha256']):
            raise PinError('sha256 must be 64 lowercase hex for %s' % path)
        source = entry['source']
        if (not isinstance(source, dict) or set(source) != {'kind', 'uri', 'generation'}
                or source['kind'] not in KINDS or not isinstance(source['uri'], str)):
            raise PinError('source must be {kind, uri, generation} for %s' % path)
        if source['kind'] == 'gcs' and not (isinstance(source['generation'], str)
                                            and source['generation'].isdigit()):
            raise PinError('a gcs entry needs its generation: %s' % path)
    return manifest


def kit_identity(manifest):
    """kit_pins_sha256 of a manifest value."""
    return util.canonical_sha256(manifest)


def build(root, spec, now=None):
    """Return a manifest generated from the files under root that spec names."""
    root = os.path.abspath(str(root))
    entries = []
    seen = set()
    for item in spec.get('entries', []):
        path = _logical(item['logical_path'])
        if path in seen:
            raise PinError('repeated logical_path: %s' % path)
        seen.add(path)
        rel = item.get('file', path)
        local = os.path.join(root, rel)
        if os.path.islink(local) or not os.path.isfile(local):
            raise PinError('%s: %s is not a regular file under the root' % (path, rel))
        digest, count = util.sha256_file(local)
        source = item.get('source') or {'kind': 'file', 'uri': path, 'generation': None}
        source = {'kind': source.get('kind'), 'uri': source.get('uri'),
                  'generation': source.get('generation')}
        entry = {'role': item.get('role'), 'logical_path': path, 'bytes': count, 'sha256': digest,
                 'source': source}
        if item.get('standin') is not None:
            entry['standin'] = item['standin']
        entries.append(entry)
    entries.sort(key=lambda row: row['logical_path'])
    manifest = {'schema': SCHEMA, 'created_utc': util.utc_iso(now), 'commit': spec.get('commit'),
                'source_seal': spec.get('source_seal'), 'entries': entries}
    return validate_manifest(manifest)


def verify(manifest, root):
    """Return a list of {logical_path, problem} for every entry whose bytes under root differ.

    A file entry must exist at root/logical_path. A gcs or orchard entry is checked when a copy
    exists at root/logical_path and is otherwise listed with problem 'remote-not-present'.
    """
    validate_manifest(manifest)
    root = str(root)
    out = []
    for entry in manifest['entries']:
        local = os.path.join(root, entry['logical_path'])
        if os.path.islink(local):
            out.append({'logical_path': entry['logical_path'], 'problem': 'symlink'})
            continue
        if not os.path.isfile(local):
            problem = 'missing' if entry['source']['kind'] == 'file' else 'remote-not-present'
            out.append({'logical_path': entry['logical_path'], 'problem': problem})
            continue
        digest, count = util.sha256_file(local)
        if count != entry['bytes'] or digest != entry['sha256']:
            out.append({'logical_path': entry['logical_path'], 'problem': 'differs',
                        'expected': {'bytes': entry['bytes'], 'sha256': entry['sha256']},
                        'actual': {'bytes': count, 'sha256': digest}})
    return out


def differences(report):
    """The verify rows that are failures (a remote entry with no local copy is not one)."""
    return [row for row in report if row['problem'] != 'remote-not-present']


# ---------------------------------------------------------------- single-place invariant

def _field_matches(pattern, path):
    """pattern 'records[].sha256' against a concrete path like ['records', 0, 'sha256']."""
    want = []
    for part in pattern.split('.'):
        if part.endswith('[]'):
            want.extend([part[:-2], int])
        else:
            want.append(part)
    if len(want) != len(path):
        return False
    for expect, actual in zip(want, path):
        if expect is int:
            if not isinstance(actual, int):
                return False
        elif expect != actual:
            return False
    return True


def check_single_place(kit, allow=DEFAULT_ALLOW):
    """Return the violations of the single-place invariant in a packed kit directory.

    Each violation is {where, field, value, reason}. The scan covers every file and every member of
    every nested tar, except the top-level PINS.json.
    """
    kit = str(kit)
    manifest = validate_manifest(util.read_json(os.path.join(kit, MANIFEST)))
    identity = kit_identity(manifest)
    by_path = dict((entry['logical_path'], entry['sha256']) for entry in manifest['entries'])
    current = set(by_path.values())
    identities = {identity}
    config_path = os.path.join(kit, CONFIG)
    if os.path.isfile(config_path):
        identities.add(util.sha256_file(config_path)[0])
    violations = []
    for where, data in walk_blobs(kit):
        if where == MANIFEST:
            continue
        top = where.split('!/')[0]
        parsed = None
        if where.endswith('.json'):
            try:
                parsed = json.loads(data.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                parsed = None
        if parsed is not None:
            for path, found, parent in _json_hex_parent(parsed):
                if found in identities or found == ZERO:
                    continue
                field = '.'.join(str(part) for part in path)
                allowed = any(fname == top and _field_matches(pattern, list(path))
                              for fname, pattern in allow)
                if allowed:
                    named = parent.get('logical_path') if isinstance(parent, dict) else None
                    if found in current and (named is None or by_path.get(named) == found):
                        continue
                    reason = 'allowlisted field holds a value equal to no current entry'
                else:
                    reason = ('copy of a pinned hash outside PINS.json' if found in current
                              else 'hash outside PINS.json that matches no entry (stale or foreign)')
                violations.append({'where': where, 'field': field, 'value': found, 'reason': reason})
            continue
        for found in sorted(set(HEX64.findall(data.decode('latin-1')))):
            if found in identities or found == ZERO:
                continue
            reason = ('copy of a pinned hash outside PINS.json' if found in current
                      else 'hash outside PINS.json that matches no entry (stale or foreign)')
            violations.append({'where': where, 'field': None, 'value': found, 'reason': reason})
    return violations


# ---------------------------------------------------------------- audit of an old-style kit

NAME_KEYS = ('logical_path', 'path', 'file', 'name', 'uri', 'object', 'alias_path')
FILE_RE = re.compile(r'[A-Za-z0-9_.\-]+\.(?:py|json|jsonl|sh|tar|gz|tgz|txt|md|safetensors|pt|npz|so)\b')


def _subject_from_json(path, parent):
    if isinstance(parent, dict):
        for key in NAME_KEYS:
            value = parent.get(key)
            if isinstance(value, str) and value:
                return os.path.basename(value.rstrip('/'))
    if path:
        last = path[-1]
        if isinstance(last, str) and ('/' in last or FILE_RE.search(last)):
            return os.path.basename(last)
        named = [part for part in path if isinstance(part, str)
                 and part not in ('sha256', 'sha', 'digest', 'hash')]
        if named:
            return named[-1]
    return None


def _json_hex_parent(value, path=()):
    """Like _json_hex but yields the dict that holds a string value, for name attribution."""
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                for found in HEX64.findall(item):
                    yield path + (key,), found, value
            else:
                for row in _json_hex_parent(item, path + (key,)):
                    yield row
            for found in HEX64.findall(key):
                yield path + (key,), found, None
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, str):
                for found in HEX64.findall(item):
                    yield path + (index,), found, None
            else:
                for row in _json_hex_parent(item, path + (index,)):
                    yield row


def audit(kit):
    """Report, for an old-style kit, each group of places that record one file's hash.

    A place is (file, field or line, value). Places are grouped by the file they describe (the
    basename attributed from a sibling path key, a mapping key or a file name on the same source
    line). A group with two or more places is a duplicate-pin group; it agrees when every place
    holds one value. When the kit itself holds a file of that name, its actual sha256 is reported.
    """
    kit = str(kit)
    places = []
    actual = {}
    for where, data in walk_blobs(kit, nested=False):
        actual.setdefault(os.path.basename(where), set()).add(util.sha256_bytes(data))
        parsed = None
        if where.endswith('.json'):
            try:
                parsed = json.loads(data.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                parsed = None
        if parsed is not None:
            for path, found, parent in _json_hex_parent(parsed):
                if found == ZERO:
                    continue
                places.append({'where': where, 'field': '.'.join(str(p) for p in path),
                               'subject': _subject_from_json(path, parent), 'value': found})
            continue
        text = data.decode('latin-1')
        for number, line in enumerate(text.splitlines(), 1):
            for found in HEX64.findall(line):
                if found == ZERO:
                    continue
                names = FILE_RE.findall(line)
                places.append({'where': where, 'field': 'line %d' % number,
                               'subject': os.path.basename(names[0]) if names else None,
                               'value': found})
    groups = {}
    for place in places:
        key = place['subject'] or ('value:' + place['value'])
        groups.setdefault(key, []).append(place)
    rows = []
    for key in sorted(groups):
        members = groups[key]
        if len(members) < 2:
            continue
        values = sorted(set(place['value'] for place in members))
        subject = None if key.startswith('value:') else key
        row = {'subject': subject, 'places': len(members), 'values': values,
               'agree': len(values) == 1,
               'where': ['%s:%s' % (p['where'], p['field']) for p in members]}
        if subject and subject in actual:
            row['actual_sha256'] = sorted(actual[subject])
        rows.append(row)
    return {'schema': 'orchkit-pin-audit-v1', 'kit': kit, 'places': len(places),
            'groups': len(rows), 'disagreeing': sum(1 for row in rows if not row['agree']),
            'rows': rows}


def _parse_allow(values):
    allow = list(DEFAULT_ALLOW)
    for value in values or ():
        name, _, field = value.partition(':')
        if not name or not field:
            raise PinError('--allow takes FILE:FIELD, got %r' % value)
        allow.append((name, field))
    return tuple(allow)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')
    p_build = sub.add_parser('build')
    p_build.add_argument('--root', required=True)
    p_build.add_argument('--spec', required=True)
    p_build.add_argument('--out', required=True)
    p_verify = sub.add_parser('verify')
    p_verify.add_argument('--manifest', required=True)
    p_verify.add_argument('--root', required=True)
    p_check = sub.add_parser('check')
    p_check.add_argument('--kit', required=True)
    p_check.add_argument('--allow', action='append')
    p_audit = sub.add_parser('audit')
    p_audit.add_argument('--kit', required=True)
    p_audit.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        if args.command == 'build':
            if os.path.exists(args.out):
                raise PinError('refusing to overwrite %s' % args.out)
            manifest = build(args.root, util.read_json(args.spec))
            util.write_json(args.out, manifest)
            print(json.dumps({'kit_pins_sha256': kit_identity(manifest),
                              'entries': len(manifest['entries'])}, sort_keys=True))
            return 0
        if args.command == 'verify':
            report = verify(util.read_json(args.manifest), args.root)
            print(json.dumps(report, sort_keys=True, indent=1))
            return 1 if differences(report) else 0
        if args.command == 'check':
            found = check_single_place(args.kit, _parse_allow(args.allow))
            print(json.dumps(found, sort_keys=True, indent=1))
            return 1 if found else 0
        if args.command == 'audit':
            report = audit(args.kit)
            if args.out:
                util.write_json(args.out, report)
            print(json.dumps({key: report[key] for key in ('places', 'groups', 'disagreeing')},
                             sort_keys=True))
            return 0
    except (PinError, OSError, ValueError) as err:
        sys.stderr.write('pins: %s\n' % err)
        return 2
    parser.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
