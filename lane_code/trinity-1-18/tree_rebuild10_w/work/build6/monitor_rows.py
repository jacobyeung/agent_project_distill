"""Run the real-row proof with the existing exact-code statement monitor."""
import hashlib,json,runpy,sys,types
from pathlib import Path
L=Path(__file__).resolve().parents[2];tree=L/'work/tree_r1';output=L/'work/build6/proofs/rows/coverage'
source=(L/'work/build6/test_runner.py').read_text();start=source.index('def code_digest(code):');end=source.index('denied = []')
hits={}
exec(compile(source[start:end],str(L/'work/build6/test_runner.py'),'exec'))
mon.set_events(4,mon.events.PY_START)
runpy.run_path(str(L/'work/build6/rows.py'),run_name='__main__')
mon.set_events(4,0)
output.mkdir(parents=True,exist_ok=True)
(output/'source_hashes.json').write_text(json.dumps(snapshots))
(output/'hits.json').write_text(json.dumps({str(Path(k).relative_to(tree)):sorted(v) for k,v in hits.items()}))
(output/'results.json').write_text(json.dumps(dict(coverage_code_filter='compiled-source fingerprint')))
