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
TREE = '9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'


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
        self.extent_exempted = self.extent_checked = self.extent_required = 0
        self.current = None

    def wrap(self, name, function):
        def observed(*args):
            if self.depth:
                return function(*args)
            self.depth += 1
            if name == 'extents':
                from student_pilot.extent_receipt import required
                if args[0].exempt(args[1], args[2]):
                    self.extent_exempted += 1
                else:
                    self.extent_checked += 1
                    self.extent_required += int(required(args[1], args[2]))
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
            first_ten_refusals=self.first, extent_exempted_rows=self.extent_exempted,
            extent_still_checked_rows=self.extent_checked, extent_required_rows=self.extent_required)


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
    baseline_refused = mismatches = 0
    from student_pilot.extent_receipt import Extents
    baseline = Extents(cfg.get('extent_receipt'))
    baseline_check = Extents.check
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
                    if stream == 'routing':
                        refused = False
                        try:
                            baseline_check(baseline, value, stream)
                        except ValueError:
                            refused = True
                        baseline_refused += int(refused)
                        mismatches += int(readers[part].extents.exempt(value, stream) != refused)
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
            result.update(extent_base_refused_rows=baseline_refused,
                extent_set_mismatch_rows=mismatches)
            if cfg.get('r1_training', {}).get('extent_pool_sources'):
                result['extent_count_status'] = 'PASS' if (
                    trace.extent_exempted == baseline_refused and not mismatches) else 'FAIL'
                if result['extent_count_status'] != 'PASS':
                    result.update(status='FAIL', reason='E98:extent')
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
    routing = value['streams']['routing']
    for name in ('refused_rows', 'extent_exempted_rows', 'extent_still_checked_rows',
                 'extent_base_refused_rows', 'extent_set_mismatch_rows', 'extent_count_status'):
        value[name] = routing.get(name)
    value['all_streams_status'] = 'PASS' if all(v['status'] == 'PASS' for v in value['streams'].values()) else 'FAIL'
    value['candidate'] = candidate(cfg, directory, output)
    try:
        value['extent_scope'] = scope_report(cfg, directory)
        if value['extent_scope']['status'] != 'PASS':
            value['status'] = 'FAIL'
    except Exception as error:
        value['extent_scope'] = dict(status='UNAVAILABLE', reason=type(error).__name__+': '+str(error))
        if cfg.get('r1_training', {}).get('extent_pool_sources'):
            value['status'] = 'FAIL'
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


REFERENCE = 'eyJhbnN3ZXIiOiAiMS40MyIsICJhbnN3ZXJfY29udGVudCI6ICIxLjQzIiwgImNhbmRpZGF0ZV9pZCI6ICJncm91bmQtNzM4ZTRlYzU5NmU4NzU4NTRjMWE5MmRmOGQ3MTQ4YjUxNTVkOGYyNDkwMzA5YWI4YjlhMWRiNzQ3MzM2ZjI4ZiIsICJjYW5vbmljYWwiOiAic2Nhbm5ldHBwL2Q5MThhZjljNWYiLCAiZGlhZ25vc3RpY19vbmx5IjogdHJ1ZSwgImZyYW1lX2luZGljZXMiOiBbMCwgMTE0NCwgMjI4OCwgMzQzMiwgNDU3NywgNTcyMSwgNjg2NSwgODAxMCwgOTE1NCwgMTAyOTgsIDExNDQyLCAxMjU4NywgMTM3MzEsIDE0ODc1LCAxNjAyMCwgMTcxNjQsIDE4MzA4LCAxOTQ1MiwgMjA1OTcsIDIxNzQxLCAyMjg4NSwgMjQwMzAsIDI1MTc0LCAyNjMxOCwgMjc0NjIsIDI4NjA3LCAyOTc1MSwgMzA4OTUsIDMyMDQwLCAzMzE4NCwgMzQzMjgsIDM1NDczXSwgImdlb21ldHJ5X3NvdXJjZSI6ICJndCIsICJndF9hY2NlcHRlZCI6IHRydWUsICJndF9hZ3JlZXMiOiB0cnVlLCAiZ3RfYW5zd2VyIjogMS40MzAyMjE1NDMyNzY0ODQ0LCAiZ3RfYXV0aG9yaXR5IjogeyJjYW5vbmljYWwiOiAic2Nhbm5ldHBwL2Q5MThhZjljNWYiLCAiZnJhbWVfaW5kaWNlcyI6IFswLCAxMTQ0LCAyMjg4LCAzNDMyLCA0NTc3LCA1NzIxLCA2ODY1LCA4MDEwLCA5MTU0LCAxMDI5OCwgMTE0NDIsIDEyNTg3LCAxMzczMSwgMTQ4NzUsIDE2MDIwLCAxNzE2NCwgMTgzMDgsIDE5NDUyLCAyMDU5NywgMjE3NDEsIDIyODg1LCAyNDAzMCwgMjUxNzQsIDI2MzE4LCAyNzQ2MiwgMjg2MDcsIDI5NzUxLCAzMDg5NSwgMzIwNDAsIDMzMTg0LCAzNDMyOCwgMzU0NzNdLCAiZ3QiOiB7InBhdGgiOiAiL3NjcmF0Y2gvamp5ZXVuZy9vcmNoX2NkL2Rvc2VfcG9vbC9vdXQvdDFfZ3QvZ3Qvc2Nhbm5ldHBwdjJfX2Q5MThhZjljNWYubnB6IiwgInNoYTI1NiI6ICIyZGMxYjQ4MTM2NTY5NTBkYmMyNGQ1NzUzMDRlOWU4YjQ0NTJjNDlhZjIwNDJlZmJkZjRmMzE3NmUyMGZmNjg0In0sICJraW5kIjogImhhc2gtdmVyaWZpZWQtbmF0aXZlLWdlb21ldHJ5IiwgImxhYmVsX3J1bGUiOiAibmF0aXZlIE9CQiBib3hfZ3JpZF81Y20sIG1pbmltdW0gb3ZlciBpbnN0YW5jZSBwYWlycyAvIG5hdGl2ZSBjZW50cm9pZCBkaXJlY3Rpb24iLCAibmF0aXZlX2luZGVwZW5kZW50X2xhYmVsIjogMS40MzAyMjE1NDMyNzY0ODQ0LCAic2NlbmVfcmVnaXN0cnkiOiB7InBhdGgiOiAiL3NjcmF0Y2gvamp5ZXVuZy9vcmNoX2NkL2dyb3VuZF9yb3dzL3dvcmsvaW5wdXRzL3JvdXRpbmczNTZfc2NlbmVzLmpzb24ifX0sICJtYXNrX3NvdXJjZSI6ICJndCIsICJuYXRpdmVfaW5kZXBlbmRlbnRfbGFiZWwiOiAxLjQzMDIyMTU0MzI3NjQ4NDQsICJub3Rfc2VlbiI6IGZhbHNlLCAib3B0aW9uX2xldHRlcl9tYXAiOiB7fSwgIm9wdGlvbl9zaHVmZmxlIjogbnVsbCwgIm9wdGlvbnMiOiBbXSwgInByb2dyYW1fYXVkaXQiOiB7ImJveF9wcm92aWRlciI6ICJhbm5vdGF0aW9uX2Z1bGxfYm94X3YxIiwgImluZGVwZW5kZW50X2F1dGhvcml0eSI6IHsiY2Fub25pY2FsIjogInNjYW5uZXRwcC9kOTE4YWY5YzVmIiwgImZyYW1lX2luZGljZXMiOiBbMCwgMTE0NCwgMjI4OCwgMzQzMiwgNDU3NywgNTcyMSwgNjg2NSwgODAxMCwgOTE1NCwgMTAyOTgsIDExNDQyLCAxMjU4NywgMTM3MzEsIDE0ODc1LCAxNjAyMCwgMTcxNjQsIDE4MzA4LCAxOTQ1MiwgMjA1OTcsIDIxNzQxLCAyMjg4NSwgMjQwMzAsIDI1MTc0LCAyNjMxOCwgMjc0NjIsIDI4NjA3LCAyOTc1MSwgMzA4OTUsIDMyMDQwLCAzMzE4NCwgMzQzMjgsIDM1NDczXSwgImd0IjogeyJwYXRoIjogIi9zY3JhdGNoL2pqeWV1bmcvb3JjaF9jZC9kb3NlX3Bvb2wvb3V0L3QxX2d0L2d0L3NjYW5uZXRwcHYyX19kOTE4YWY5YzVmLm5weiIsICJzaGEyNTYiOiAiMmRjMWI0ODEzNjU2OTUwZGJjMjRkNTc1MzA0ZTllOGI0NDUyYzQ5YWYyMDQyZWZiZGY0ZjMxNzZlMjBmZjY4NCJ9LCAia2luZCI6ICJoYXNoLXZlcmlmaWVkLW5hdGl2ZS1nZW9tZXRyeSIsICJsYWJlbF9ydWxlIjogIm5hdGl2ZSBPQkIgYm94X2dyaWRfNWNtLCBtaW5pbXVtIG92ZXIgaW5zdGFuY2UgcGFpcnMgLyBuYXRpdmUgY2VudHJvaWQgZGlyZWN0aW9uIiwgIm5hdGl2ZV9pbmRlcGVuZGVudF9sYWJlbCI6IDEuNDMwMjIxNTQzMjc2NDg0NCwgInNjZW5lX3JlZ2lzdHJ5IjogeyJwYXRoIjogIi9zY3JhdGNoL2pqeWV1bmcvb3JjaF9jZC9ncm91bmRfcm93cy93b3JrL2lucHV0cy9yb3V0aW5nMzU2X3NjZW5lcy5qc29uIn19LCAiaW5kZXBlbmRlbnRfb3JkZXJlZF9ib3hlcyI6IFt7ImF4ZXNMZW5ndGhzIjogWzAuNjYyMjQ2NDcwMTc3MzUwOCwgMC4zOTQ0NTQwMzIxODI2OTM1LCAwLjA4NDc0NzA3Njk3MTM4NDhdLCAiY2VudHJvaWQiOiBbMi44OTc2NzY5ODkwMjIxMDE3LCAzLjgwMjY4NjU2NTQ1MzU1MjQsIDEuMjg1ODY5MjEwOTU4NDgxXSwgImluc3RhbmNlX2lkIjogMTUyLCAibmFtZSI6ICJ0diIsICJub3JtYWxpemVkQXhlcyI6IFstMC45NzgyNDkyNDY4MjkyMzg0LCAwLjIwNzQzMjkwNzQxMzUyNDM4LCA0LjYwNTkzNTc5NzUwODY2MmUtMTcsIDAuMCwgLTIuMjIwNDQ2MDQ5MjUwMzEzZS0xNiwgMS4wLCAwLjIwNzQzMjkwNzQxMzUyNDM4LCAwLjk3ODI0OTI0NjgyOTIzODQsIDIuMTcyMTQ5Njc1MzA0MDc2OGUtMTZdfSwgeyJheGVzTGVuZ3RocyI6IFswLjQ3MDYzMDE1NTcxNDk2NDMsIDAuNDQzNjcyODA2MDI0NTUxNDUsIDAuNDY2NTUxNTgyODU1NDg4Nl0sICJjZW50cm9pZCI6IFszLjg1OTMyODcyMDI2Mzc3MiwgMi4wNjUwMDIzODMwMDQwNzQ1LCAwLjc2MjI3NTkwNDQxNzAzOF0sICJpbnN0YW5jZV9pZCI6IDE1LCAibmFtZSI6ICJzb2ZhIiwgIm5vcm1hbGl6ZWRBeGVzIjogWy0wLjgzMDc5NjUzMzQ3NTUwNjksIDAuNTU2NTc2MjQ4MTE0MzgxLCAxLjIzNTg0NzUzMTIzMjEzOTNlLTE2LCAwLjAsIC0yLjIyMDQ0NjA0OTI1MDMxM2UtMTYsIDEuMCwgMC41NTY1NzYyNDgxMTQzODA5LCAwLjgzMDc5NjUzMzQ3NTUwNywgMS44NDQ3Mzg4ODA0ODY1NDVlLTE2XX1dLCAiaW5kZXBlbmRlbnRfdGFyZ2V0IjogMS40MzAyMjE1NDMyNzY0ODQ0LCAibnVtcHlfdmVyc2lvbiI6ICIyLjIuNiIsICJ0YXJnZXRfZGlzdGFuY2VfcnVsZSI6ICJib3hfZ3JpZF81Y20iLCAidW5yb3VuZGVkX2Rpc2NyZXBhbmN5X20iOiA0LjQ0MDg5MjA5ODUwMDYyNmUtMTYsICJ1bnJvdW5kZWRfcmVwbGF5X20iOiBbMS40MzAyMjE1NDMyNzY0ODQ5XX0sICJwcm92ZW5hbmNlIjogeyJhMF92NCI6IHsiZXZlbnRfdGV4dF9lZGl0cyI6IFtdLCAic291cmNlX2ZpbGVfc2hhMjU2IjogImMxNmM1ZGIzNmUwNGMxZWYzZGQ2NzI5ZjFlYmE3M2Q5MDU3ZTQxNWIxYmZhYzA1ZDRjYjEzZjc3NWExNGRlYTQiLCAic291cmNlX2xpbmUiOiAzMTAsICJzb3VyY2VfcGF0aCI6ICJ3b3JrL3B1bGwvcG9vbC9jMTZjNWRiMzZlMDRjMWVmLmpzb25sLmd6IiwgInNvdXJjZV9xaWQiOiAidnNpNTkwa18xNjkxMzkiLCAic291cmNlX3Jvd19zaGEyNTYiOiAiODQ4MmZkOWRmYzFiNzA4NTYzMDRkNjM4NzIwMDVjNGE5MGZmMjVmYjdhYjZiNjMzYzIxYmVhMTk3ZWYxYjM1YiIsICJzb3VyY2Vfc2V0IjogIlQxSDJfZ2VuX3IyIiwgInN1ZmZpeF90b2tlbnMiOiAic3RhbGU7IHNvdXJjZSBzdXBwbGllcyBhIHRva2VuX2NvdW50IGNhbGxiYWNrIGJ1dCBubyBwaW5uZWQgY291bnRpbmcgcnVsZSIsICJ0ZXh0X2VkaXRzIjogW3siYWZ0ZXIiOiAiVGhlIGJveCBnYXAgaXMgdGhlIHNtYWxsZXN0IGRpc3RhbmNlIGJldHdlZW4gcG9pbnRzIG9uIGEgZ3JpZCBvdmVyIGJvdGggb2JqZWN0cycgZnVsbCBib3hlcywgdGFrZW4gb3ZlciBldmVyeSBwYWlyIG9mIGluc3RhbmNlcy4iLCAiYXV0aG9yaXR5IjogIkJ1aWxkIDUgb3JjaGVzdHJhdG9yIHJ1bGluZyAxIiwgImJlZm9yZSI6ICJUaGUgYm94IGdhcCBpcyB0aGUgc21hbGxlc3QgZGlzdGFuY2UgYmV0d2VlbiBwb2ludHMgb24gYSA1IGNtIGdyaWQgb3ZlciB0aGUgdHdvIG9iamVjdHMnIGZ1bGwgYm94ZXMsIHRha2VuIG92ZXIgZXZlcnkgcGFpciBvZiBpbnN0YW5jZXMuIiwgImtpbmQiOiAibW9kZWxfd3JpdHRlbl90ZXh0IiwgInJlc3BvbnNlc19jaGFuZ2VkIjogZmFsc2UsICJzb3VyY2VfbGluZSI6IDIxfV19fSwgInFpZCI6ICJ2c2k1OTBrXzE2OTEzOSIsICJxdWVzdGlvbiI6ICJNZWFzdXJpbmcgZnJvbSB0aGUgY2xvc2VzdCBwb2ludCBvZiBlYWNoIG9iamVjdCwgd2hhdCBpcyB0aGUgZGlzdGFuY2UgYmV0d2VlbiB0aGUgdHYgYW5kIHRoZSBzb2ZhIChpbiBtZXRlcnMpPyIsICJxdWVzdGlvbl9pZGVudGl0eSI6ICJjYjM1M2U1ZjMxNzJiZWQ0ODYzMjk1MDBjMTNjYTRkOGJhM2NkMWZiMjg5ZTYzODg1MzZiOGQxMDk5NWNlNGI2IiwgInJvbGVzIjogeyJhIjogInR2IiwgImIiOiAic29mYSJ9LCAicm9vbSI6ICJzY2FubmV0cHAvZDkxOGFmOWM1ZiIsICJzY2VuZSI6ICJ2MDQzZGMyMDJlZjk0IiwgInNjZW5lX2d0X3NoYTI1NiI6ICIyZGMxYjQ4MTM2NTY5NTBkYmMyNGQ1NzUzMDRlOWU4YjQ0NTJjNDlhZjIwNDJlZmJkZjRmMzE3NmUyMGZmNjg0IiwgInNlbGVjdGlvbl9yZWZ1c2FsIjogbnVsbCwgInNpbXVsYXRlZF9taXNzZXMiOiBbXSwgInNvdXJjZV9ndF9hbnN3ZXIiOiAiMC45NCIsICJzb3VyY2Vfam9pbiI6IHsiZ3RfYW5zd2VyIjogIjAuOTQiLCAib3B0aW9ucyI6IFtdfSwgInNwZWNfdmVyc2lvbiI6ICIzLjE0IiwgInN1ZmZpeCI6ICI8dGhpbms+XG5JIHdpbGwgZ3JvdW5kIHRoZSBib3hlcyBhbmQgYXNrIHRoZSB0b29sIHRvIG1lYXN1cmUgdGhlaXIgYm94IGRpc3RhbmNlLlxuPGdyb3VuZCBvYmo9XCJ0dlwiIG1vZGU9XCJib3hcIj5cbjx0b29sX3Jlc3BvbnNlPlxudHY6IGZyYW1lcyAxLDcgKGJlc3QgMSlcbkIxOiBmMSBjZW50cmUgKDEuMTcsIC0wLjQ2LCA1LjE0KSBtXG5zaXplIDAuNjYgeCAwLjA4IHggMC4zOSBtXG55YXcgLTEwMCBkZWcgKDAgPSAreDsgcG9zaXRpdmUgK3ggdG93YXJkIC16IGFib3V0ICt5KVxuPC90b29sX3Jlc3BvbnNlPlxuPGdyb3VuZCBvYmo9XCJzb2ZhXCIgbW9kZT1cImJveFwiPlxuPHRvb2xfcmVzcG9uc2U+XG5zb2ZhOiBmcmFtZXMgMSw3LDksMTEsMTMsMzIgKGJlc3QgMTMpXG5CMjogZjEgY2VudHJlICgtMC4wOSwgLTAuOTgsIDMuNjEpIG1cbnNpemUgMC40NyB4IDAuNDcgeCAwLjQ0IG1cbnlhdyAtNzggZGVnICgwID0gK3g7IHBvc2l0aXZlICt4IHRvd2FyZCAteiBhYm91dCAreSlcbjwvdG9vbF9yZXNwb25zZT5cbjxnYXAgYT1cInR2XCIgYj1cInNvZmFcIiBydWxlPVwiYm94X2dyaWRfNWNtXCI+XG48dG9vbF9yZXNwb25zZT5cbmRpc3RhbmNlIDEuNDMgbVxuPC90b29sX3Jlc3BvbnNlPlxuVGhlIGJveCBnYXAgaXMgdGhlIHNtYWxsZXN0IGRpc3RhbmNlIGJldHdlZW4gcG9pbnRzIG9uIGEgZ3JpZCBvdmVyIGJvdGggb2JqZWN0cycgZnVsbCBib3hlcywgdGFrZW4gb3ZlciBldmVyeSBwYWlyIG9mIGluc3RhbmNlcy5cblRoZSBib3ggZGlzdGFuY2UgaXMgMS40MyBtLlxuPC90aGluaz5cbjxhbnN3ZXI+MS40MzwvYW5zd2VyPiIsICJzdWZmaXhfdG9rZW5zIjogMzA5LCAidHJhaW5pbmdfYWRtaXR0ZWQiOiBmYWxzZSwgInR5cGUiOiAib2JqZWN0X2Fic19kaXN0YW5jZSIsICJ2MzExX2Fuc3dlciI6IDEuNTgwMTY4NTgzNDIwMzUyfQ=='
REFERENCE_SHA = 'd484ffc09e8b8db7658604976ebabd5bb78402cb9f65810d64def320f4bff6b8'

def scope_tests(cfg, rows):
    """Use native stored rows and a sealed reference for the absent source class."""
    from student_pilot.extent_receipt import Extents, required
    from student_pilot.p3_provenance import digest
    gate = Extents(cfg.get('extent_receipt'), cfg.get('r1_training', {}).get('extent_pool_sources'))
    examples = {}
    for row in rows:
        if gate.exempt(row, 'routing'):
            examples.setdefault('pool', row)
        elif required(row, 'routing'):
            name = 'slice' if str(row.get('qid', '')).startswith('a0_') else 'other'
            examples.setdefault(name, row)
        if len(examples) == 3:
            break
    origins = {name: 'database' for name in examples}
    if 'other' not in examples:
        import base64
        value = json.loads(base64.b64decode(REFERENCE))
        if digest(value) != REFERENCE_SHA:
            raise ValueError('E99:reference')
        examples['other'] = value
        origins['other'] = 'sealed_reference'
    results = {}
    for name in ('slice', 'pool', 'other'):
        if name not in examples:
            results[name] = dict(status='UNAVAILABLE', reason='E99:row')
            continue
        row = examples[name]
        test = Extents(cfg.get('extent_receipt'), cfg.get('r1_training', {}).get('extent_pool_sources'))
        if name != 'pool':
            # Negative control: remove only this entry in memory, never on disk.
            test.receipt = dict(test.receipt, rows={q:e for q,e in test.receipt['rows'].items()
                                                  if q != row['qid']})
        expected = None if name == 'pool' else 'EXTENT_ROW_UNAUDITED'
        error = None
        try:
            test.check(row, 'routing')
        except Exception as caught:
            error = str(caught)
        results[name] = dict(status='PASS' if error == expected else 'FAIL',
            qid=row['qid'], row_sha256=digest(row), origin=origins[name],
            expected=expected, observed=error, exempted=test.exempted)
    return dict(status='PASS' if all(v['status']=='PASS' for v in results.values()) else 'FAIL',
                cases=results)


def card_rows(cfg, n_rows, p_rows):
    from student_pilot.extent_receipt import Extents
    import re
    gate = Extents(cfg.get('extent_receipt'), cfg.get('r1_training', {}).get('extent_pool_sources'))
    def norm(qid):
        match = re.search(r'[a-z][a-z0-9]*_[0-9]+', qid)
        return match.group() if match else qid
    p_qids = {r['qid'] for r in p_rows if r.get('s1_source', {}).get('name') in gate.pool_sources}
    entries = gate.receipt['rows']
    exact = p_qids & entries.keys()
    normalized = {}; repaired = set(); flagged = set()
    for qid, entry in entries.items():
        key = norm(qid)
        normalized[key] = True
        if entry.get('repair_sha256'):
            repaired.add(key)
        if any(s != 'full' for s in entry.get('box_statuses', [])):
            flagged.add(key)
    counts = Counter(); by_source = Counter()
    for row in n_rows:
        value = {**row, **row['routing']} if isinstance(row.get('routing'), dict) else row
        kind = value.get('question_type', value.get('type'))
        if kind in ('object_abs_distance', 'absolute_distance_object', 'camera_object_abs_distance'):
            counts['distance_rows'] += 1
        if not gate.exempt(row, 'routing'):
            continue
        counts['exempted_rows'] += 1
        source = row['s1_source']; by_source[source['name']] += 1
        canonical = source.get('provenance', {}).get('canonical', '')
        if not canonical:
            counts['missing_canonical_rows'] += 1
        if canonical.startswith(bytes.fromhex('7363616e6e657470702f').decode()):
            counts['v1_rows'] += 1
    return dict(counts=counts, by_source=by_source,
        v1_fraction=counts['v1_rows']/counts['distance_rows'] if counts['distance_rows'] else None,
        p_pool_qids=len(p_qids), exact_matches=len(exact),
        exact_repaired=sum(bool(entries[q].get('repair_sha256')) for q in exact),
        exact_flagged=sum(any(s != 'full' for s in entries[q].get('box_statuses', [])) for q in exact),
        normalized_qid_matches=sum(norm(q) in normalized for q in p_qids),
        normalized_distinct_matches=len({norm(q) for q in p_qids} & normalized.keys()),
        normalized_repaired=sum(norm(q) in repaired for q in p_qids),
        normalized_flagged=sum(norm(q) in flagged for q in p_qids),
        normalization='base numeric identifier; all receipt variants; diagnostic only')


def scope_report(cfg, directory):
    from student_pilot.p3_provenance import sha256
    directory = Path(directory)
    def rows(c):
        for (text,) in c.execute('SELECT row FROM rows ORDER BY i'):
            yield json.loads(text)
    with sqlite3.connect((directory/'selection/rows.sqlite').as_uri()+'?mode=ro', uri=True) as n:
        tests = scope_tests(cfg, rows(n))
        if sha256(directory/'base/rows.sqlite') != DB:
            raise ValueError('E99:base')
        with sqlite3.connect((directory/'base/rows.sqlite').as_uri()+'?mode=ro', uri=True) as p:
            card = card_rows(cfg, rows(n), rows(p))
    return dict(status=tests['status'] if not card['counts']['missing_canonical_rows'] else 'FAIL', tests=tests, card=card)
