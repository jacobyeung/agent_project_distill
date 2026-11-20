"""Observe the native per-row reader without changing its pins or refusals."""
from contextlib import ExitStack
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

CHECKS = ('wording', 'text', 'extents', 'r1', 'reserve', 'r2')


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def failure(error):
    return type(error).__name__+':'+str(error)


class Observe:
    def __init__(self, reader):
        self.reader = reader
        self.totals = {name: Counter() for name in CHECKS}
        self.rows = Counter()
        self.first = []
        self.depth = 0
        self.enabled = dict(wording=reader.wording_exclusion is not None, text=True, extents=True,
            r1=bool(reader.r1_training), reserve=bool(reader.b7_inputs or reader.r1_training),
            r2=reader.r2_admission is not None)

    def wrap(self, name, function):
        def call(*args):
            # row_check calls the text audit again. Count its outcome under r1,
            # leaving the separately invoked text check as one result per row.
            nested = self.depth > 0
            self.depth += 1
            try:
                result = function(*args)
            except Exception as error:
                if not nested:
                    self.seen[name] = 'FAIL'
                    self.refusal = (name, failure(error))
                raise
            else:
                if not nested:
                    self.seen[name] = 'PASS'
                return result
            finally:
                self.depth -= 1
        return call

    def install(self, stack):
        from student_pilot import r1_coverage, row_text_audit, extent_receipt, r1_training, r0_exclusion, r2_contract
        for name, owner, attribute, function in (
            ('wording', r1_coverage.WordingExclusion, 'check', r1_coverage.WordingExclusion.check),
            ('text', row_text_audit, 'check', row_text_audit.check), ('extents', extent_receipt.Extents, 'check', extent_receipt.Extents.check),
            ('r1', r1_training, 'row_check', r1_training.row_check), ('reserve', r0_exclusion.Reserve, 'check', r0_exclusion.Reserve.check),
            ('r2', r2_contract.Admission, 'check', r2_contract.Admission.check)):
            stack.enter_context(patch.object(owner, attribute, self.wrap(name, function)))

    def row(self, stream, index, key):
        self.seen = {}; self.refusal = None
        try:
            self.reader.row(stream, index)
        except Exception as error:
            self.rows['FAIL'] += 1
            name, text = self.refusal or ('row', failure(error))
            if len(self.first) < 10:
                self.first.append(dict(key=key, check=name, exception=text))
        else:
            self.rows['PASS'] += 1
        for name in CHECKS:
            result = self.seen.get(name, 'NOT_REACHED' if self.enabled[name] else 'UNBOUND')
            self.totals[name][result] += 1

    def result(self):
        return dict(status='FAIL' if self.rows['FAIL'] else 'PASS', count=sum(self.rows.values()),
            rows=dict(self.rows), checks={k:dict(v) for k,v in self.totals.items()},
            first_ten_refusals=self.first, short_circuit=True)


def candidate(database, pin, output):
    """Publish native content bindings; never invent an independent box audit."""
    from student_pilot.extent_receipt import content, required, Extents
    from student_pilot.p3_provenance import digest, load, pinned
    receipt = load(pinned(pin)) if pin else None
    gate = Extents(pin)
    rows = []; counts = Counter(); first = []
    with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True) as connection:
        for i, raw in connection.execute('SELECT i,row FROM rows ORDER BY i'):
            row = json.loads(raw)
            if not (row.get('s1_source') or {}).get('name'):
                continue
            key = ['routing', i, str(row.get('qid', row.get('id', '')))]
            rows.append(dict(key=key, content_sha256=digest(content(row))))
            if required(row, 'routing'):
                counts['required'] += 1
                try: gate.check(row, 'routing')
                except Exception as error:
                    counts['FAIL'] += 1
                    if len(first) < 10: first.append(dict(key=key, check='extents', exception=failure(error)))
                else: counts['PASS'] += 1
            else: counts['NOT_REQUIRED'] += 1
    keys = sorted(r['key'] for r in rows)
    rowset = hashlib.sha256(json.dumps(keys,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    # C'' contains a validator and an aggregator of existing receipts, but no
    # producer that independently audits new content. Bindings are review input,
    # not a full-extent-receipt-v1 or a replacement for the pinned evidence.
    value = dict(status='UNAVAILABLE', reason='E99', pinned_receipt=pin, count=len(rows),
        row_set_sha256=rowset, row_set_encoding='sorted [stream,i,qid] compact UTF-8 JSON',
        coverage=dict(counts), first_ten_refusals=first, native_builder_available=False,
        native_content_function='student_pilot.extent_receipt.content', rows=rows,
        pinned_metadata={k:v for k,v in (receipt or {}).items() if k!='rows'},
        pinned_rows=len((receipt or {}).get('rows',{})), applied=False)
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    with Path(output).open('xb') as stream:
        stream.write(gzip.compress(raw,mtime=0))
    return {k:v for k,v in value.items() if k not in ('rows','pinned_metadata')}


def audit(cfg, database, output):
    from student_pilot.carrier_c1_run import Rows
    from student_pilot.p3_provenance import digest
    # Use the same Rows constructor and all bound gates. Only the source view is
    # unrestricted: every SQL row is requested, before any preparation filtering.
    reader = Rows(dict(cfg, streams={}), None)
    connection = sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)
    reader.connections['routing'] = connection
    observer = Observe(reader)
    try:
        with ExitStack() as stack:
            observer.install(stack)
            for i, raw in connection.execute('SELECT i,row FROM rows ORDER BY i'):
                try:
                    row = json.loads(raw)
                    key = ['routing', i, str(row.get('qid', row.get('id', '')))]
                except Exception:
                    key = ['routing', i, '']
                observer.row('routing', i, key)
        value = observer.result()
    finally:
        reader.close()
    value.update(config_sha256=digest(cfg), extent_receipt=cfg.get('extent_receipt'),
        scope='all stored routing rows before preparation filtering')
    write(output, value)
    return value


def run(kit, root):
    import z
    root = Path(root)
    value = dict(status='FAIL', reason='E99', count=0, checks={}, first_ten_refusals=[])
    try:
        namespace = z.load(Path(kit)/'k/p.json')['namespace']
        tree = Path(namespace)/'p/s'; q = Path(namespace)/'p/q'
        sys.path.insert(0, str(tree))
        from student_pilot.p3_provenance import load, pinned, digest
        from student_pilot.source_seal import inventory
        from student_pilot.r1_persisted import scope
        paths = z.load(root/'pins.json')['paths'].copy()
        paths.update({p.name:str(p) for p in (q/'u').iterdir() if p.is_file() and len(p.name)==64})
        with scope(paths):
            cfg = load(q/'n.json')
            sealed = load(pinned(cfg['code']))
            actual = digest(inventory(tree))
            if actual != sealed['tree_sha256']:
                raise ValueError('E93')
            database = q/'selection/rows.sqlite'
            try:
                value = audit(cfg, database, root/'chain.json')
            except Exception as error:
                value.update(reason=failure(error))
            # Evidence generation remains independent of reader setup/refusals.
            try:
                value['candidate'] = candidate(database, cfg.get('extent_receipt'), root/'cc.json.gz')
            except Exception as error:
                value['candidate'] = dict(status='UNAVAILABLE', reason=failure(error), applied=False)
            value['tree_sha256'] = actual
            value['preparation_full_chain'] = True
            value['other_stream_sampling'] = 'NOT_REQUIRED'
    except Exception as error:
        value.update(status='FAIL', reason=failure(error))
    write(root/'chain.json', value)
    return value
