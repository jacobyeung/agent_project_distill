#!/usr/bin/env python3
"""Audit store scene identities against pinned physical-room lists, without network IO."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shlex
import sqlite3
import sys
import types
import uuid

NAMES = ('R0', 'withheld-80', 'BENCH v2', 'dev-S1', 'K1')
DATASETS = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes', 'scannetppv2': 'scannetpp'}
TOKEN_DS = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}
HASHED = re.compile(r'd[123]/v[0-9a-f]{12}\Z')


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: '+key)
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


class Inputs:
    def __init__(self):
        self.pins = {}

    def pin(self, path, expected=None):
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError('MISSING: '+str(path))
        pin = {'sha256': sha256(path), 'bytes': path.stat().st_size}
        self.pins[str(path)] = pin
        if expected is not None and pin['sha256'] != expected:
            raise ValueError('SHA256 mismatch: '+str(path))
        return path

    def read(self, path, expected=None):
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError('MISSING: '+str(path))
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        self.pins[str(path)] = {'sha256': actual, 'bytes': len(raw)}
        if expected is not None and actual != expected:
            raise ValueError('SHA256 mismatch: '+str(path))
        return raw

    def document(self, path, expected=None):
        return decode(self.read(path, expected))


def load_tree(tree, ledger):
    """Load only the selected tree's room modules, without its package startup code."""
    package_name = '_room_audit_'+uuid.uuid4().hex
    package = types.ModuleType(package_name)
    package.__path__ = []  # No implicit imports from another installed tree.
    sys.modules[package_name] = package
    modules = {}
    for name in ('p3_provenance', 'r1_persisted', 'r1_rooms'):
        path = tree/'student_pilot'/(name+'.py')
        raw = ledger.read(path)
        full = package_name+'.'+name
        module = types.ModuleType(full)
        module.__file__ = str(path)
        module.__package__ = package_name
        sys.modules[full] = module
        exec(compile(raw, str(path), 'exec'), module.__dict__)
        modules[name] = module
    path = tree/'student_pilot/carrier_c1_routing.py'
    parsed = ast.parse(ledger.read(path), str(path))
    nodes = [n for n in parsed.body if
             (isinstance(n, ast.FunctionDef) and n.name == 'alias_of') or
             (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('ALIAS','NATIVE') for t in n.targets))]
    if len(nodes) != 3:
        raise ValueError('Unsupported alias_of source: '+str(path))
    namespace = {'hashlib': hashlib}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return modules['r1_rooms'].Rooms, namespace['alias_of']


def normalize_scene(value):
    if not isinstance(value, str) or '/' not in value:
        raise ValueError('Invalid canonical scene')
    ds, capture = value.split('/', 1)
    ds = DATASETS.get(ds, ds)
    patterns = {'scannet': r'scene\d+_\d+', 'scannetpp': r'[0-9a-f]{10}', 'arkitscenes': r'\d+'}
    if ds not in patterns or not re.fullmatch(patterns[ds], capture):
        raise ValueError('Invalid canonical scene: '+value)
    return ds+'/'+capture


def list_room(value, rooms, venue_captures):
    """Pass each listed room through Rooms.room using a witnessed capture if needed."""
    if not isinstance(value, str) or '/' not in value:
        raise ValueError('Invalid list room: '+repr(value))
    ds, capture = value.split('/', 1)
    ds = DATASETS.get(ds, ds)
    native = ds+'/'+capture
    if ds == 'arkitscenes' and capture.startswith('venue'):
        canonical = venue_captures.get(native)
        if canonical is None:
            raise ValueError('MISSING visit-table capture for list room: '+value)
        result = rooms.room(canonical)
        if result != native:
            raise ValueError('Visit-table room mismatch: '+value)
        return result
    if ds == 'arkitscenes' and capture.startswith('capture'):
        result = rooms.room(normalize_scene(ds+'/'+capture[len('capture'):]))
        if result != native:
            raise ValueError('Capture-room mismatch: '+value)
        return result
    if ds == 'scannet' and re.fullmatch(r'scene\d+', capture):
        return rooms.room(native)
    if ds == 'scannetpp' and re.fullmatch(r'[0-9a-f]+', capture):
        # Preserve literal authority labels, including R0's nine-digit label.
        return rooms.room(native)
    return rooms.room(normalize_scene(native))


def prepare(tree, directory, ledger):
    manifest = ledger.document(directory/'manifest.json')
    if manifest.get('schema') != 'store-room-audit-inputs-v1':
        raise ValueError('Unsupported input manifest schema')
    cls, mint = load_tree(tree, ledger)
    pins = {}
    for name, pin in manifest['authority'].items():
        path = ledger.pin(directory/pin['path'], pin['sha256'])
        pins[name] = {'path': str(path), 'sha256': pin['sha256']}
    rooms = cls(pins)  # Execute this tree's complete constructor and authority checks.
    venues = {}
    for video, visit in sorted(rooms.visits.items()):
        if visit and visit != 'NA':
            venues.setdefault('arkitscenes/venue'+visit, 'arkitscenes/'+video)
    if set(manifest['lists']) != set(NAMES):
        raise ValueError('Manifest requires exactly these lists: '+', '.join(NAMES))
    sets, checks = {}, {}
    for name in NAMES:
        pin = manifest['lists'][name]
        raw = ledger.read(directory/pin['path'], pin['sha256'])
        field = pin['field']
        if field == 'text':
            values = raw.decode().split()
        else:
            doc = decode(raw)
            if field == 'heldout_captures':
                values = []
                for capture in doc['captures']:
                    if capture['k1_split'] != 'heldout':
                        continue
                    canonical = normalize_scene(capture['canonical'])
                    room = rooms.room(canonical)
                    if 'room' in capture and list_room(capture['room'], rooms, venues) != room:
                        raise ValueError('K1 capture/room disagreement: '+canonical)
                    values.append(canonical)
            elif field in ('rooms', 'physical_groups'):
                values = doc[field]
            else:
                raise ValueError('Unsupported list field: '+field)
        sets[name] = {list_room(value, rooms, venues) for value in values}
        checks[name] = {'entries': len(values), 'rooms': len(sets[name]), 'field': field}
    aliases, quarantine = {}, set()
    if 'alias_map' in manifest:
        pin = manifest['alias_map']
        doc = ledger.document(directory/pin['path'], pin['sha256'])
        quarantine = set(doc.get('quarantined_tokens', []))
        for token, entry in doc['aliases'].items():
            canonical = normalize_scene(entry['canonical'])
            if entry['tier'] not in ('A', 'B', 'C'):
                raise ValueError('Invalid proof tier: '+token)
            if HASHED.fullmatch(token) and mint(canonical) != token:
                raise ValueError('Alias preimage mismatch: '+token)
            aliases[token] = {'canonical': canonical, 'tier': entry['tier']}
    for token, canonical in rooms.aliases.items():
        canonical = normalize_scene(canonical)
        if HASHED.fullmatch(token) and mint(canonical) != token:
            raise ValueError('Authority alias preimage mismatch: '+token)
        if token in aliases and aliases[token]['canonical'] != canonical:
            raise ValueError('Authority/tiered alias disagreement: '+token)
        aliases.setdefault(token, {'canonical': canonical, 'tier': 'authority'})
    rooms.aliases = {token: entry['canonical'] for token, entry in aliases.items()}
    return rooms, mint, sets, checks, aliases, quarantine


def iter_rows(path):
    if path.suffix in ('.sqlite', '.db', '.sqlite3'):
        with sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1', uri=True) as conn:
            for index, raw in conn.execute('SELECT i, row FROM rows ORDER BY i'):
                yield index, decode(raw)
    elif path.suffix == '.json':
        doc = decode(path.read_bytes())
        for index, row in enumerate(doc if isinstance(doc, list) else doc['rows']):
            yield index, row
    else:
        with path.open() as handle:
            for index, line in enumerate(handle):
                if line.strip():
                    yield index, decode(line)


def resolve(row, rooms, mint, aliases, quarantine):
    ds, scene = row.get('dataset', ''), row.get('scene', '')
    if not isinstance(ds, str) or not isinstance(scene, str):
        return '', None, None, None, 'invalid_dataset_or_scene'
    token = TOKEN_DS.get(ds, ds)+'/'+scene
    if token in quarantine:
        return token, None, None, None, 'quarantined_token'
    try:
        canonical, route = rooms.canonical(row)
        canonical = normalize_scene(canonical)
        entry = aliases.get(token)
        if entry and canonical != entry['canonical']:
            raise ValueError('row_alias_conflict')
        if HASHED.fullmatch(token):
            if mint(canonical) != token:
                raise ValueError('row_preimage_mismatch')
        elif route == 'row_field':
            # A native dataset/scene field must agree with its explicit witness.
            try:
                native = normalize_scene(ds+'/'+scene)
            except ValueError:
                native = None
            if native is not None and native != canonical:
                raise ValueError('native_row_field_conflict')
        room = rooms.room(canonical)
        if not isinstance(room, str) or not room:
            raise ValueError('empty_room')
        tier = entry['tier'] if entry else ('A' if route == 'row_field' else 'native')
        return token, canonical, room, tier, None
    except (ValueError, TypeError, AttributeError, KeyError) as error:
        return token, None, None, None, str(error)


def audit(args, ledger):
    tree, directory, store = args.tree.resolve(), args.lists.resolve(), args.store.resolve()
    rooms, mint, sets, list_checks, aliases, quarantine = prepare(tree, directory, ledger)
    ledger.pin(store)
    if store.suffix in ('.sqlite', '.db', '.sqlite3'):
        for suffix in ('-wal', '-journal'):
            if Path(str(store)+suffix).exists():
                raise ValueError('Store must be an offline SQLite snapshot; sidecar exists: '+str(store)+suffix)
    report = {'schema': 'store-room-audit-v1', 'command': shlex.join([sys.executable]+sys.argv),
              'inputs': ledger.pins, 'tree': str(tree), 'store': str(store), 'list_checks': list_checks,
              'scope': 'Row scene identities only; frames are not inspected.',
              'allow_unresolved': args.allow_unresolved}
    counts = Counter()
    hits = {name: Counter() for name in NAMES}
    streams = {name: Counter() for name in NAMES}
    families = {name: Counter() for name in NAMES}
    joint, unresolved, reasons, coverage = Counter(), Counter(), Counter(), Counter()
    unique_rooms = set()
    database = args.out/'rows.sqlite'
    with sqlite3.connect(database) as conn:
        conn.execute('CREATE TABLE rows (row_index INTEGER PRIMARY KEY, row_id TEXT, dataset TEXT, scene_token TEXT, token TEXT, scene TEXT, room TEXT, tier TEXT, stream TEXT, family TEXT, hits TEXT, unresolved_reason TEXT)')
        conn.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
        conn.execute('INSERT INTO metadata VALUES (?, ?)', ('status', 'RUNNING'))
        for index, row in iter_rows(store):
            if not isinstance(row, dict):
                raise ValueError('Store row is not an object: '+str(index))
            token, canonical, room, tier, reason = resolve(row, rooms, mint, aliases, quarantine)
            stream = str(row.get('pool', 'MISSING'))
            family = str(row.get('question_type', 'MISSING'))
            matched = []
            counts['rows'] += 1
            if room is None:
                counts['unresolved_rows'] += 1
                unresolved[token] += 1
                reasons[reason] += 1
            else:
                counts['resolved_rows'] += 1
                unique_rooms.add(room)
                coverage[tier] += 1
                for name in NAMES:
                    if room in sets[name]:
                        matched.append(name)
                        hits[name][tier] += 1
                        streams[name][stream] += 1
                        families[name][family] += 1
                        joint[(name, tier, stream, family)] += 1
            conn.execute('INSERT INTO rows VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                         (index, str(row.get('qid', 'MISSING')), str(row.get('dataset', '')),
                          str(row.get('scene', '')), token, canonical, room, tier, stream, family,
                          json.dumps(matched), reason))
        complete = counts['unresolved_rows'] == 0
        report.update(status='PASS' if complete else ('INCOMPLETE' if args.allow_unresolved else 'REFUSED'),
                      complete=complete, counts_are_lower_bounds=not complete,
                      rows=counts['rows'], resolved_rows=counts['resolved_rows'],
                      unresolved_rows=counts['unresolved_rows'], unresolved_token_count=len(unresolved),
                      unresolved_tokens=dict(unresolved), unresolved_reasons=dict(reasons),
                      rooms_resolved=len(unique_rooms), coverage_by_tier=dict(coverage),
                      hits={n: sum(hits[n].values()) for n in NAMES},
                      hits_by_tier={n: dict(hits[n]) for n in NAMES},
                      hits_by_stream={n: dict(streams[n]) for n in NAMES},
                      hits_by_family={n: dict(families[n]) for n in NAMES},
                      hits_by_list_tier_stream_family=[dict(list=n, tier=t, stream=s, family=f, rows=v)
                                                     for (n,t,s,f),v in sorted(joint.items())])
        conn.execute('UPDATE metadata SET value=? WHERE key=?', (report['status'], 'status'))
        conn.execute('INSERT INTO metadata VALUES (?, ?)', ('audit', json.dumps(report, sort_keys=True)))
    report['row_records'] = {'path': 'rows.sqlite', 'sha256': sha256(database), 'bytes': database.stat().st_size}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('store', 'tree', 'lists', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--allow-unresolved', action='store_true', help='Emit incomplete lower-bound counts and exit 0.')
    args = parser.parse_args(argv)
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        parser.error('--out must be empty to prevent stale audit results: '+str(args.out))
    ledger = Inputs()
    ledger.pin(Path(__file__))
    try:
        report = audit(args, ledger)
        code = 0 if report['complete'] or args.allow_unresolved else 2
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        report = {'schema': 'store-room-audit-v1', 'status': 'MISSING' if isinstance(error, FileNotFoundError) or 'MISSING' in str(error) else 'ERROR',
                  'complete': False, 'error': str(error), 'inputs': ledger.pins,
                  'command': shlex.join([sys.executable]+sys.argv)}
        code = 1
    with (args.out/'audit.json').open('x') as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write('\n')
    if 'hits' in report:
        print(', '.join(name+'='+str(report['hits'][name]) for name in NAMES))
        print('{}: unresolved tokens={}, rows={}'.format(report['status'], report['unresolved_token_count'], report['unresolved_rows']))
    else:
        print(report['status']+': '+report['error'], file=sys.stderr)
    return code


if __name__ == '__main__':
    sys.exit(main())
