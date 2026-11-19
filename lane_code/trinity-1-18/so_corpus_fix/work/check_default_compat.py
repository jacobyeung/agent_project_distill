"""Compare immutable-input and patched default outputs on the same fixtures."""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sys

import torch
torch.set_num_threads(8)

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tool'))
import ingest_read as fixed

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

original = load('input_ingest', '/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin/ingest_read.py')
tests = load('fixtures_synthetic', ROOT / 'tool/tests/test_synthetic.py')
review = load('fixtures_review', ROOT / 'tool/tests/test_review2.py')
fixed.SCRATCH = str(ROOT / 'fixtures')
original.SCRATCH = fixed.SCRATCH
os.makedirs(fixed.SCRATCH, exist_ok=True)

cases = []
for kind in ('kit', 'routed', 'offread'):
    fixture = tests.CorpusTests()
    fixture.setUp()
    if kind == 'kit':
        fixture.kit()
    elif kind == 'routed':
        fixture.routed(multi=True)
    else:
        fixture.write('COMPLETE.json', {'items': 1})
        for filename in ('items_a0', 'budget_2048', 'budget_4096'):
            fixture.write('a0/results/0/' + filename + '.jsonl',
                          [dict(id='q', question='Q', answer='A', score=0.5)], True)
    cases.append((kind, pathlib.Path(fixture.root), fixture.source, []))

for kind in ('native', 'kit_bad_alias', 'native_missing_arm', 'native_conflicting_tasks'):
    fixture = review.Review2Tests()
    fixture.setUp()
    if kind == 'kit_bad_alias':
        fixture.kit([dict(id='devrows:q', scores={'answer': 0.25})])
    else:
        fixture.native(scripted=None if kind == 'native_missing_arm' else 'devrows:q')
        if kind == 'native_conflicting_tasks':
            for name, scene in [('a', 'one'), ('b', 'two')]:
                fixture.store.record('native/' + name + '.jsonl', dict(id='q', question='Q', answer='A', scene=scene))
    root, source = fixture.source()
    cases.append((kind, pathlib.Path(root), source, []))
    fixture.doCleanups()

for kind in ('kit_duplicate_exact', 'kit_duplicate_alias', 'native_unlabeled_report',
             'native_row_task_conflict', 'native_missing_input', 'native_empty_inputs'):
    fixture = review.Review2Tests()
    fixture.setUp()
    if kind.startswith('kit_'):
        field, key = ('id', 'q') if kind.endswith('exact') else ('key', 'devrows:q')
        fixture.kit([{field: key, 'scores': {'answer': x}} for x in (0.25, 0.75)])
    else:
        fixture.native()
        if kind == 'native_unlabeled_report':
            for seq, data in list(fixture.store.db.execute("SELECT seq,data FROM records WHERE path='native/R1.json'")):
                row = json.loads(data)
                row.pop('arm')
                fixture.store.db.execute('UPDATE records SET data=? WHERE seq=?', (fixed.dumps(row), seq))
        if kind == 'native_row_task_conflict':
            fixture.store.record('native/tasks.jsonl', dict(id='q', question='Q', room='r1'))
            for seq, data in list(fixture.store.db.execute('SELECT seq,data FROM records WHERE path IN (?,?)',
                    ('native/R1.json', 'native/paired/results/items.jsonl'))):
                row = dict(json.loads(data), room='r2')
                fixture.store.db.execute('UPDATE records SET data=? WHERE seq=?', (fixed.dumps(row), seq))
        if kind == 'native_missing_input':
            fixture.store.record('inputs/tasks.jsonl', dict(id='other', question='Q'))
    root, source = fixture.source()
    flags = []
    if kind in ('native_missing_input', 'native_empty_inputs'):
        inputs = os.path.join(source, 'inputs')
        os.makedirs(inputs, exist_ok=True)
        flags = ['--inputs', inputs]
    cases.append((kind, pathlib.Path(root), source, flags))
    fixture.doCleanups()

for kind, root, source, flags in cases:
    outputs = []
    for name, module in [('input', original), ('fixed_default', fixed)]:
        out = root / name
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = module.main(['ingest', '--source', source, '--read-id', 'compat', '--out', str(out)] + flags)
        assert code == 0, (kind, name, code, err.getvalue())
        outputs.append(out)
    files = sorted(p.relative_to(outputs[0]) for sub in ('reads', 'index')
                   for p in (outputs[0] / sub).iterdir() if p.name.startswith('compat') and not p.name.endswith('.lock'))
    for filename in files:
        a, b = [(out / filename).read_bytes() for out in outputs]
        if str(filename).endswith('.json'):
            a, b = json.loads(a), json.loads(b)
            assert a.pop('tool_version') == original.fingerprint(original.__file__)['sha256']
            assert b.pop('tool_version') == fixed.fingerprint(fixed.__file__)['sha256']
        assert a == b, (kind, str(filename))
    print('%s: identical read/orphan bytes; identical index except tool_version (%d files)' % (kind, len(files)))
print('PASS: %d fixtures; default read/orphan bytes preserved, including review-three branches' % len(cases))
