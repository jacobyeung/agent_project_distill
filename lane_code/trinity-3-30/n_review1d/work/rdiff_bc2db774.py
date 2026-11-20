#!/usr/bin/env python3
"""Compare every admitted row, preserving all SQL columns and raw JSON text."""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sqlite3
import struct
import sys

VERSION = 'rdiff-v1'
EXPECTED_P = '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def packed(values):
    """Injective typed framing. TEXT bytes are never parsed or normalized here."""
    out = bytearray(b'rdiff-v1\x00')
    for value in values:
        if value is None:
            tag, data = b'n', b''
        elif type(value) is int:
            tag, data = b'i', str(value).encode('ascii')
        elif type(value) is float:
            tag, data = b'f', struct.pack('>d', value)
        elif type(value) is str:
            tag, data = b't', value.encode('utf-8')
        elif type(value) is bytes:
            tag, data = b'b', value
        else:
            raise ValueError('Unsupported SQLite value type')
        out.extend(tag + struct.pack('>Q', len(data)) + data)
    return out


def open_db(path):
    # mode=ro prevents a missing input from becoming an empty database.
    db = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA temp_store=MEMORY')
    db.execute('PRAGMA cache_size=-8192')
    return db


def schema(db):
    columns = list(db.execute('PRAGMA table_info(rows)'))
    if [c[1] for c in columns] != ['i', 'row', 'target']:
        raise ValueError('Expected native rows(i,row,target) table or view')
    return [dict(name=c[1], type=c[2]) for c in columns]


def rows(db, removal):
    # rows is the training view; rejected candidates and pool_qids are not rows.
    # Include i: a change in ordinal is an actual content mismatch, not erased.
    for values in db.execute('SELECT * FROM rows ORDER BY i'):
        i, raw, target = values
        if type(i) is not int or not isinstance(raw, str) or not isinstance(target, str):
            raise ValueError('Native row column type differs')
        row = json.loads(raw)
        if not isinstance(row, dict) or not isinstance(row.get('qid'), str) or not row['qid']:
            raise ValueError('Native row requires a nonempty string qid')
        src = row.get('s1_source') or {}
        if not isinstance(src, dict):
            raise ValueError('s1_source is not an object')
        # qid is the native deduplication identity. dataset/scene/source distinguish
        # sources without using mutable sequence numbers or JSON formatting.
        key = [row.get('dataset'), row.get('scene'), row['qid'], src.get('name')]
        key_text = json.dumps(key, ensure_ascii=True, separators=(',', ':'))
        matches = removal.match(row)  # calls the staged tree's row_keys function
        yield dict(key=key, key_text=key_text, i=i,
                   sha256=hashlib.sha256(packed(values)).hexdigest(),
                   faithful=src.get('name') == 'U_Faithful',
                   listed=[removal.files[j]['sha256'] for j in matches],
                   removal_keys=sorted(removal.row_key_function(row)))


def get_removals(args):
    tree = Path(args.tree).resolve(strict=True)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(tree))
    module = importlib.import_module('student_pilot.row_removals')
    if Path(module.__file__).resolve() != tree / 'student_pilot/row_removals.py':
        raise ValueError('Removal module did not load from --tree')
    rules = []
    if args.removal_manifest:
        manifest = Path(args.removal_manifest).resolve(strict=True)
        value = json.loads(manifest.read_text())
        rules = value['remove_files'] if isinstance(value, dict) else value
        if not isinstance(rules, list):
            raise ValueError('Removal manifest must be an array or config.remove_files')
        rules = [dict(r) for r in rules]
        for r in rules:
            p = Path(r['path'])
            if not p.is_absolute():
                p = (Path(args.base).resolve() if args.base else manifest.parent) / p
            r['path'] = str(p.resolve(strict=True))
    for path in args.remove_files:
        p = Path(path).resolve(strict=True)
        rules.append(dict(path=str(p), sha256=sha_file(p)))
    restrictions = {}
    for value in args.defects:
        h, sep, names = value.partition('=')
        if not sep or h in restrictions:
            raise ValueError('Expected one SHA256=defect,defect restriction per list')
        restrictions[h] = names.split(',')
    for h in restrictions:
        found = False
        for r in rules:
            if r['sha256'] == h:
                if 'defects' in r and r['defects'] != restrictions[h]:
                    raise ValueError('Conflicting defect restriction')
                r['defects'] = restrictions[h]
                found = True
        if not found:
            raise ValueError('Defect restriction names no supplied list')
    # Never silently treat the known extent-containing list as unrestricted.
    restricted = '8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2'
    for r in rules:
        if r['sha256'] == restricted and r.get('defects') != ['identity', 'absent', 'merged']:
            raise ValueError('Pinned list requires defects=identity,absent,merged')
        if sha_file(r['path']) != r['sha256']:
            raise ValueError('Removal-list SHA256 differs: ' + r['sha256'])
    removal = module.Removals(rules)
    removal.row_key_function = module.row_keys
    return removal, dict(path=str(tree), row_removals_sha256=sha_file(module.__file__),
                        key_function='student_pilot.row_removals.row_keys',
                        reader='student_pilot.row_removals.Removals')


def compare(args):
    removal, tree = get_removals(args)
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    diff_path, summary_path = output/'rdiff.json.gz', output/'rdiff_summary.json'
    if diff_path.exists() or summary_path.exists():
        raise ValueError('Output exists; choose a fresh opaque directory')
    expected = None if args.expected_p_sha256 == 'none' else args.expected_p_sha256
    p_sha = sha_file(args.p_db)
    if expected is not None and p_sha != expected:
        raise ValueError('P database SHA256 differs: ' + p_sha)
    summary = dict(schema=VERSION, N_rows=0, P_rows=0, matched_identical=0,
                   mismatched=0, N_rows_without_P=0, P_rows_absent_from_N=0,
                   absent_and_listed=0, absent_and_unlisted=0,
                   N_rows_listed=0, U_Faithful=dict(P=0, N=0, listed=0,
                   absent_listed=0, N_listed=0), script_sha256=sha_file(__file__),
                   tree=tree, removal_files=removal.files,
                   inputs=dict(P=dict(path=str(Path(args.p_db).resolve()), sha256=p_sha),
                               N=dict(path=str(Path(args.n_db).resolve()), sha256=sha_file(args.n_db))),
                   content_columns=['i','row','target'],
                   content_encoding='typed length-prefixed SQLite values; raw UTF-8 TEXT; includes i',
                   key_columns=['dataset','scene','qid','s1_source.name'])
    pmap = {}
    with open_db(args.p_db) as p, open_db(args.n_db) as n:
        summary['P_schema'], summary['N_schema'] = schema(p), schema(n)
        for row in rows(p, removal):
            if row['key_text'] in pmap:
                raise ValueError('Duplicate P semantic key: ' + row['key_text'])
            pmap[row['key_text']] = row
            summary['P_rows'] += 1
            if row['faithful']:
                summary['U_Faithful']['P'] += 1
                summary['U_Faithful']['listed'] += bool(row['listed'])
        nkeys = set()
        with diff_path.open('xb') as rawout:
            with gzip.GzipFile(filename='', mode='wb', fileobj=rawout, mtime=0) as gz:
                def emit(value):
                    gz.write(json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('utf-8'))
                gz.write(b'{"schema":"rdiff-v1","N":[')
                first = True
                for row in rows(n, removal):
                    if row['key_text'] in nkeys:
                        raise ValueError('Duplicate N semantic key: ' + row['key_text'])
                    nkeys.add(row['key_text'])
                    prior = pmap.get(row['key_text'])
                    identical = prior is not None and prior['sha256'] == row['sha256']
                    summary['N_rows'] += 1
                    summary['matched_identical'] += identical
                    summary['mismatched'] += not identical
                    summary['N_rows_without_P'] += prior is None
                    summary['N_rows_listed'] += bool(row['listed'])
                    if row['faithful']:
                        summary['U_Faithful']['N'] += 1
                        summary['U_Faithful']['N_listed'] += bool(row['listed'])
                    if not first:
                        gz.write(b',')
                    first = False
                    emit(dict(key=row['key'], i=row['i'], content_sha256=row['sha256'],
                              P=None if prior is None else dict(key=prior['key'], i=prior['i'],
                                  content_sha256=prior['sha256']), identical=identical,
                              removal_list_sha256s=row['listed']))
                gz.write(b'],"P_absent":[')
                first = True
                for key, row in pmap.items():
                    if key in nkeys:
                        continue
                    summary['P_rows_absent_from_N'] += 1
                    summary['absent_and_listed'] += bool(row['listed'])
                    summary['absent_and_unlisted'] += not row['listed']
                    if row['faithful'] and row['listed']:
                        summary['U_Faithful']['absent_listed'] += 1
                    if not first:
                        gz.write(b',')
                    first = False
                    emit(dict(key=row['key'], i=row['i'], content_sha256=row['sha256'],
                              removal_list_sha256=row['listed'][0] if row['listed'] else 'none',
                              removal_list_sha256s=row['listed'], removal_keys=row['removal_keys']))
                gz.write(b'],"U_Faithful":')
                emit(summary['U_Faithful'])
                gz.write(b'}\n')
    summary['status'] = ('PASS' if summary['mismatched'] == 0
                         and summary['absent_and_unlisted'] == 0
                         and summary['N_rows_listed'] == 0 else 'FAIL')
    summary['rdiff_sha256'] = sha_file(diff_path)
    with summary_path.open('x') as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps({k:summary[k] for k in ('status','N_rows','P_rows','matched_identical',
          'mismatched','P_rows_absent_from_N','absent_and_listed','absent_and_unlisted','U_Faithful')}))
    return 0 if summary['status'] == 'PASS' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('n_db')
    parser.add_argument('p_db')
    parser.add_argument('--tree', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--remove-files', nargs='*', default=[])
    parser.add_argument('--removal-manifest')
    parser.add_argument('--base', help='Base for relative paths in removal manifest')
    parser.add_argument('--defects', action='append', default=[])
    parser.add_argument('--expected-p-sha256', default=EXPECTED_P,
                        help='P pin; use none only for explicitly synthetic tests')
    args = parser.parse_args()
    if not args.removal_manifest and not args.remove_files:
        parser.error('Supply pinned removal files or a removal manifest (empty array allowed)')
    try:
        return compare(args)
    except (ValueError, OSError, sqlite3.Error, KeyError, ImportError) as error:
        print('rdiff: ' + type(error).__name__ + ': ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
