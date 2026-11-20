"""Observe the native row reader with the launch's current pins."""
from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import random
import sqlite3
from unittest.mock import patch

SEED = 20261124
CHECKS = ('wording', 'text', 'extents', 'r1', 'reserve', 'r2')
DB = '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
TREE = 'de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)+'\n').encode()


def write(path, value):
    Path(path).write_bytes(raw(value))


def key(stream, part, index, row):
    return [stream, part, index, str(row.get('qid', row.get('id', '')))]


def key_hash(keys):
    return hashlib.sha256(raw(sorted(keys))).hexdigest()


class Trace:
    """Count calls without changing return values, exceptions or reader order."""
    def __init__(self):
        self.counts = {name: Counter() for name in CHECKS}
        self.first = []
        self.rows = self.refused = self.depth = 0
        self.current = None

    def wrap(self, name, function):
        def observed(*args):
            if self.depth:
                return function(*args)
            self.depth += 1
            try:
                result = function(*args)
            except Exception as error:
                self.current[name] = 'FAIL'
                if len(self.first) < 10:
                    self.first.append(dict(row_key=self.row_key, check=name,
                        exception=type(error).__name__+': '+str(error)))
                raise
            else:
                self.current[name] = 'PASS'
                return result
            finally:
                self.depth -= 1
        return observed

    def hooks(self, reader):
        from student_pilot import row_text_audit, r1_training
        from student_pilot.extent_receipt import Extents
        from student_pilot.r0_exclusion import Reserve
        from student_pilot.r2_contract import Admission
        from student_pilot.r1_coverage import WordingExclusion
        self.enabled = dict(wording=reader.wording_exclusion is not None, text=True,
            extents=True, r1=bool(reader.r1_training),
            reserve=bool(reader.b7_inputs or reader.r1_training), r2=reader.r2_admission is not None)
        stack = ExitStack()
        for name, obj, attr, fn in [('wording', WordingExclusion, 'check', WordingExclusion.check),
                ('text', row_text_audit, 'check', row_text_audit.check), ('extents', Extents, 'check', Extents.check),
                ('r1', r1_training, 'row_check', r1_training.row_check), ('reserve', Reserve, 'check', Reserve.check),
                ('r2', Admission, 'check', Admission.check)]:
            stack.enter_context(patch.object(obj, attr, self.wrap(name, fn)))
        return stack

    def row(self, reader, stream, part, index, value):
        self.row_key = key(stream, part, index, value)
        self.current = {}
        self.rows += 1
        try:
            reader.row(stream, index)
        except Exception as error:
            self.refused += 1
            if 'FAIL' not in self.current.values() and len(self.first) < 10:
                self.first.append(dict(row_key=self.row_key, check='reader',
                    exception=type(error).__name__+': '+str(error)))
        finally:
            for name in CHECKS:
                state = self.current.get(name, 'NOT_REACHED' if self.enabled[name] else 'NOT_BOUND')
                self.counts[name][state] += 1

    def result(self):
        return dict(status='PASS' if self.rows and not self.refused else 'FAIL',
            rows_checked=self.rows, refused_rows=self.refused, counts=self.counts,
            first_ten_refusals=self.first)


def stores(cfg, stream, directory):
    from student_pilot.p3_provenance import file_pin, load, pinned
    if stream == 'routing':
        return [dict(database=file_pin(Path(directory)/'selection/rows.sqlite'))]
    receipt = load(pinned(cfg['streams'][stream]))
    if receipt.get('schema') == 'c1-pose-mix-v1':
        from student_pilot.c1_pose_mix import validate_spec
        validate_spec(receipt)
        out = []
        for source in receipt['sources']:
            if source['kind'] != 'rows':
                raise ValueError('E98:source')
            out.append(load(pinned(source['receipt'])))
        return out
    return [receipt]


def scan(cfg, stream, sources, sample_size=None):
    from student_pilot.carrier_c1_run import Rows
    from student_pilot.p3_provenance import pinned
    trace = Trace(); catalog = []; connections = []; readers = []
    result = dict(status='UNAVAILABLE', staged=False, database_rows=None, rows_checked=0)
    try:
        for part, source in enumerate(sources):
            database = pinned(source['database'])
            c = sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)
            connections.append(c)
            catalog.extend((part, i) for (i,) in c.execute('SELECT i FROM rows ORDER BY i'))
        result.update(staged=True, database_rows=len(catalog), databases=[s['database'] for s in sources])
        for source, c in zip(sources, connections):
            count = c.execute('SELECT count(*) FROM rows').fetchone()[0]
            # Same construction as the native routing composer. The stream view
            # includes every physical row; it applies no preparation filtering.
            database = dict(source['database'], path=str(pinned(source['database'])))
            receipt = dict(cfg, streams={stream: dict(database=database, count=count)})
            readers.append(Rows(receipt, None))
        if sample_size is None:
            selected = catalog
        elif len(catalog) >= sample_size:
            selected = random.Random(SEED).sample(catalog, sample_size)
        elif catalog:
            selected = random.Random(SEED).choices(catalog, k=sample_size)
        else:
            selected = []
        dbkeys = []
        if stream == 'routing':
            for part, c in enumerate(connections):
                for i, text in c.execute('SELECT i,row FROM rows ORDER BY i'):
                    dbkeys.append(key(stream, part, i, json.loads(text)))
        checked = []
        for part in range(len(readers)):
            with trace.hooks(readers[part]):
                for current, index in selected:
                    if current != part:
                        continue
                    value = json.loads(connections[part].execute('SELECT row FROM rows WHERE i=?', (index,)).fetchone()[0])
                    checked.append(key(stream, part, index, value))
                    trace.row(readers[part], stream, part, index, value)
        result.update(trace.result(), seed=SEED if sample_size else None,
            sample_size_requested=sample_size, unique_rows_checked=len(set(map(tuple, checked))),
            replacement=sample_size is not None and len(catalog) < sample_size,
            checked_key_set_sha256=key_hash(set(map(tuple, checked))))
        if stream == 'routing':
            result.update(database_key_set_sha256=key_hash(dbkeys),
                complete=trace.rows == len(catalog) and len(checked) == len(dbkeys)
                and key_hash(checked) == key_hash(dbkeys))
            if not result['complete']:
                result['status'] = 'FAIL'
    except Exception as error:
        result.update(trace.result(), status='UNAVAILABLE', reason=type(error).__name__+': '+str(error))
    finally:
        for reader in readers:
            reader.close()
        for c in connections:
            c.close()
    return result


def candidate(cfg, directory, output):
    """Carry authenticated audit entries; the native content function builds digests."""
    from student_pilot.extent_receipt import content
    from student_pilot.p3_provenance import digest, load, pinned, sha256, encoded
    directory, output = Path(directory), Path(output)
    pin = cfg.get('extent_receipt')
    summary = dict(status='UNAVAILABLE', source_receipt=pin, candidate_pinned=False,
        new_audit=False, builder='native content/digest; audit entry carry', native_receipt_builder=False)
    try:
        source = load(pinned(pin))
        if source.get('schema') != 'full-extent-receipt-v1':
            raise ValueError('E98:schema')
        summary['source_sha256'] = sha256(pinned(pin))
        summary['source_qid_set_sha256'] = key_hash(list(source['rows']))
        summary['source_fields'] = {k:v for k,v in source.items() if k != 'rows'}
        summary['source_rows'] = len(source['rows'])
        rows = {}
        with sqlite3.connect((directory/'selection/rows.sqlite').as_uri()+'?mode=ro', uri=True) as c:
            for (text,) in c.execute('SELECT row FROM rows ORDER BY i'):
                value = json.loads(text)
                if value.get('s1_source'):
                    qid = value['qid']
                    if qid in rows:
                        raise ValueError('E98:duplicate')
                    rows[qid] = digest(content(value))
        summary.update(pool_rows=len(rows), row_set_sha256=key_hash(list(rows)),
            row_set_encoding='sorted qids; compact sorted-key UTF-8 JSON plus LF')
        n_equal = sum(source['rows'].get(q, {}).get('content_sha256') == h for q,h in rows.items())
        summary.update(pinned_N_content_equal=n_equal, pinned_N_content_mismatch=len(rows)-n_equal)
        summary['P_database_sha256'] = sha256(directory/'base/rows.sqlite')
        if summary['P_database_sha256'] != DB:
            raise ValueError('E98:gate')
        control = directory/'base_input.json'
        if control.is_file():
            p_config = load(control)['config']
            summary['P_config_sha256'] = digest(p_config)
            summary['P_config_extent_receipt'] = p_config.get('extent_receipt')
        old_digests = {}; duplicates = set(); p_pool = set()
        with sqlite3.connect((directory/'base/rows.sqlite').as_uri()+'?mode=ro', uri=True) as c:
            for (text,) in c.execute('SELECT row FROM rows ORDER BY i'):
                value = json.loads(text); qid = value.get('qid')
                if value.get('s1_source'):
                    p_pool.add(qid)
                if qid in rows or qid in source['rows']:
                    if qid in old_digests:
                        duplicates.add(qid)
                    old_digests[qid] = digest(content(value))
        common = set(old_digests) & set(source['rows'])
        summary.update(P_pool_rows=len(p_pool), P_pool_qid_set_sha256=key_hash(list(p_pool)),
            source_qids_in_P=len(common), source_qids_absent_from_P=len(set(source['rows'])-common),
            source_content_equal_P=sum(source['rows'][q].get('content_sha256') == old_digests[q] for q in common))
        absent = sorted(set(rows)-set(source['rows']))
        unmatched = sorted(q for q in rows if q not in old_digests or
            source['rows'].get(q, {}).get('content_sha256') != old_digests.get(q))
        summary.update(missing_source_entries=len(absent), missing_or_changed_P_rows=len(unmatched),
            duplicate_P_qids=len(duplicates), first_ten_missing=absent[:10], first_ten_unmatched=unmatched[:10])
        if absent or unmatched or duplicates or not rows:
            raise ValueError('E98:source')
        entries = {}; fields = {}
        for qid, h in rows.items():
            before = source['rows'][qid]; after = dict(before, content_sha256=h)
            entries[qid] = after
            for name in sorted(set(before) | set(after)):
                stat = fields.setdefault(name, dict(equal=0, changed=0))
                stat['equal' if before.get(name) == after.get(name) else 'changed'] += 1
        # No new box/repair certification. Retain all receipt-level audit fields.
        value = dict(source, rows=entries)
        payload = (encoded(value)+'\n').encode()
        packed = gzip.compress(payload, mtime=0)
        (output/'cand.json.gz').write_bytes(packed)
        summary.update(status='PASS', source_sha256=sha256(pinned(pin)),
            candidate_sha256=hashlib.sha256(payload).hexdigest(), candidate_bytes=len(payload),
            compressed_sha256=hashlib.sha256(packed).hexdigest(), compressed_bytes=len(packed),
            fields=fields, qid_set_equal=set(entries) == set(rows),
            all_content_digests_equal=all(entries[q]['content_sha256'] == h for q,h in rows.items()),
            audit_fields_unchanged=all({k:v for k,v in entries[q].items() if k != 'content_sha256'} ==
                {k:v for k,v in source['rows'][q].items() if k != 'content_sha256'} for q in rows))
    except Exception as error:
        summary.update(status='REFUSE', reason=type(error).__name__+': '+str(error))
    write(output/'cand_cmp.json', summary)
    return summary


def run(cfg, directory, output):
    from student_pilot.p3_provenance import digest
    output = Path(output)
    value = dict(status='UNAVAILABLE', config_sha256=digest(cfg), extent_receipt=cfg.get('extent_receipt'),
        streams={}, first_ten_refusals=[], key_encoding='sorted [stream,part,i,qid]; compact sorted-key UTF-8 JSON plus LF',
        population=dict(status='NOT_REACHED', mode_r_reaches_preparation=False,
            rows=None, key_set_sha256=None,
            first_entry='s1_admission.admit -> carrier_c1_run.prepare -> r1_population.bind_prepared'),
        candidate_used=False)
    for stream in ('routing', 'vqa', 'pointing', 'pose'):
        try:
            result = scan(cfg, stream, stores(cfg, stream, directory), None if stream == 'routing' else 20000)
        except Exception as error:
            result = dict(status='UNAVAILABLE', staged=False, rows_checked=0,
                reason=type(error).__name__+': '+str(error))
        value['streams'][stream] = result
        if stream == 'routing':
            value['population'].update(database_rows=result.get('database_rows'),
                database_key_set_sha256=result.get('database_key_set_sha256'))
        value['first_ten_refusals'].extend(result.get('first_ten_refusals', [])[:10-len(value['first_ten_refusals'])])
        value['status'] = value['streams']['routing']['status']
        write(output/'chain.json', value)
    value['all_streams_status'] = 'PASS' if all(v['status'] == 'PASS' for v in value['streams'].values()) else 'FAIL'
    value['candidate'] = candidate(cfg, directory, output)
    write(output/'chain.json', value)
    return value


def bound(kit, root):
    import sys
    import z
    root = Path(root)
    namespace = z.load(Path(kit)/'k/p.json')['namespace']
    tree = Path(namespace)/'p/s'; directory = Path(namespace)/'p/q'
    sys.path.insert(0, str(tree))
    from student_pilot.p3_provenance import digest, load
    from student_pilot.source_seal import inventory
    from student_pilot.r1_persisted import scope
    if digest(inventory(tree)) != TREE:
        raise ValueError('E98:tree')
    paths = z.load(root/'pins.json')['paths'].copy()
    for p in (directory/'u').iterdir():
        if p.is_file() and len(p.name) == 64:
            paths[p.name] = str(p)
    # This file is captured from the exact stage_host result passed to regenerate.
    cfg = load(root/'ch_cfg.json')
    with scope(paths):
        return run(cfg, directory, root)
