"""Reuse the bounded standard-library statement tracer and per-test storage guard."""
import os
import hashlib
import json
from pathlib import Path
import runpy
import sys
import importlib.util
L = Path(__file__).resolve().parents[2]
os.environ['B2_PREFIX'] = os.environ.get('B3_PREFIX', 'B3_')
if sys.argv[1:] == ['all']:
    sys.argv[1:] = json.loads((L/'work/build3/suite.json').read_text()) + [
        'tests.test_r2_build3_edges', 'tests.test_r2_build3.EvaluationEntrypoints',
        'tests.test_r2_build3.Build3.test_opener_export_keep_and_reset',
        'tests.test_r2_build3.Build3.test_four_stream_record_identity',
        'tests.test_r2_build3.Build3.test_cpu_resource_mutations',
        'tests.test_r2_build3.Build3.test_init_delivered_archive_mapping',
        'tests.test_r2_build3.Build3.test_native_prepare_and_every_rank_encode']
snapshot = L/'work/build3/snapshots'/os.environ['B2_PREFIX']
snapshot.mkdir(parents=True,exist_ok=True)
(snapshot/'entries.json').write_bytes((L/'out/B3_BANK_ENTRYPOINTS.json').read_bytes())
inventory = {}
for path in (L/'work/tree_r1').rglob('*.py'):
    name = str(path.relative_to(L/'work/tree_r1'))
    base = L/'work/base/tree_b01ce449'/name
    raw = path.read_bytes()
    if base.exists() and base.read_bytes() == raw:
        continue
    h = hashlib.sha256(raw).hexdigest()
    (snapshot/(h+'.dat')).write_bytes(raw)
    inventory[name] = h
(snapshot/'0.json').write_text(json.dumps(inventory))
sys.path.insert(0,str(L/'work/tree_r1'))
for name in ('build3_loader', 'build3_estimator', 'build3_trace'):
    if name in sys.argv:
        path=L/'work/build3'/('test_'+name.removeprefix('build3_')+'.py')
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
runpy.run_path(str(L/'work/build3b/shared_runner.py'), run_name='__main__')
