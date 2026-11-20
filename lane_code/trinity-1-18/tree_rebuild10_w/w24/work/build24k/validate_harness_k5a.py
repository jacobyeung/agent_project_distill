"""Check fixture construction and wiring without executing another rehearsal stage."""
from pathlib import Path
from contextlib import closing
import ast
import hashlib
import json
import os
import sqlite3
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rehearsal_population_k5 import bound_population
D = Path(__file__).resolve().parent
R = D/'rehearsal_k5'
V = R/'harness_validation'
V.mkdir()
(V/'source').symlink_to(R/'source', target_is_directory=True)

class J:
    @staticmethod
    def sha(path):
        digest = hashlib.sha256()
        with Path(path).open('rb') as handle:
            for block in iter(lambda: handle.read(1 << 20), b''): digest.update(block)
        return digest.hexdigest()
    @staticmethod
    def load(path): return json.loads(Path(path).read_text())
    @staticmethod
    def write(path, value):
        with Path(path).open('x') as handle: json.dump(value, handle, indent=2); handle.write('\n')
        return dict(path=str(path), sha256=J.sha(path))

cfg = J.load(R/'seed.json')
bound_population(V, D.parent/'build24/proofs/capacity', cfg, J)
sys.path.insert(0, str(R/'source'))
from student_pilot.r2_scene_bindings import rows
population = J.load(V/'BOUNDED_POPULATION.json')
counts = {}
for record in population['records']:
    # This calls the unchanged native reader on the actual Trinity hostname.
    count = sum(1 for row in rows(record['database']))
    assert count == record['count'] == 2000
    counts[record['source']] = count
    with closing(sqlite3.connect(Path(record['original_database']['path']).as_uri()+'?mode=ro&immutable=1', uri=True)) as original, \
         closing(sqlite3.connect(Path(record['database']['path']).as_uri()+'?mode=ro&immutable=1', uri=True)) as bounded:
        assert original.execute('SELECT i,row,target FROM rows ORDER BY i LIMIT 2000').fetchall() == bounded.execute('SELECT i,row,target FROM rows ORDER BY i').fetchall()
J.write(V/'fixture_config.json', cfg)
builder = ast.parse((D/'make_rehearsal_k5a.py').read_text())
calls = [(node.lineno, node.func.id) for node in ast.walk(builder)
         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
         and node.func.id in ('bound_population', 'prepare', 'inventory')]
assert [name for _, name in sorted(calls)] == ['bound_population', 'prepare', 'inventory'], calls
assert "request['routing_base']=cfg['streams']['routing']" in (D/'make_rehearsal_k5a.py').read_text()
assert "root/'fixture'" in (D/'rehearsal_inputs_k5a.py').read_text()
assert "root/'fixture'" in (D/'rehearsal_closure_k5a.py').read_text()
assert "if v.get('borrowed', True)" in (D/'rehearsal_inputs_k5a.py').read_text()
for path in D.glob('*k5a.py'): ast.parse(path.read_text(), filename=str(path))
J.write(V/'RESULT.json', dict(status='PASS', host=os.uname().nodename, native_reader_counts=counts,
       bounded_rows_preserve_original_bytes=True, builder_call_order=calls,
       native_scene_rebuild_rerun=False, planner_closure_rerun=False, training_run=False,
       launcher=str(D/'go_rehearsal_k5a.sh'), scope='Fixture construction/native reads and static wiring only.'))
print(json.dumps(J.load(V/'RESULT.json')))
