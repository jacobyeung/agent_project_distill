"""Use completed real CPU tower outputs with explicit synthetic checkpoint heads."""
from pathlib import Path
import sys
import coverage
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
source=B/'work/rh_042fff7909cc49ea9a785a18ecde4103'
dest=B/(sys.argv[1] if len(sys.argv)>1 else 'work/rh_real');dest.mkdir()
cov=coverage.Coverage(data_file=str(dest/'coverage'),source=[str(B/'code')]);cov.start()
import engine,report
from boundary import Boundary
spec=dict(tree=str(R/'from113/work/tree'),artifact=dict(path='fixture',sha256=digest('fixture')),config=dict(path='fixture',sha256=digest('fixture')),device='cpu')
engine.initialize(spec)
bound=validate_bound(source/'i/BOUND.json')
raw=load(source/'real_raw/RAW.json')
assert not raw.get('synthetic')
original=pin(source/'real_raw/RAW.json')
for value in raw['captures'].values():checked(value)
# Only the rehearsal receipt changes. The original raw arrays and receipt stay intact.
# Production rejects this marker with a real checkpoint boundary.
raw.update(synthetic=True,real_cpu_tower=original,fixture_checkpoint_heads=True)
dump(dest/'RAW_FIXTURE_HEADS.json',raw)
boundary=Boundary()
geometry=engine.prepare_geometry(bound,spec,dest/'RAW_FIXTURE_HEADS.json',dest/'g',boundary)
completion=engine.run(source/'i/BOUND.json',spec,geometry,dest/'j',boundary=boundary)
engine.merge(source/'i/BOUND.json',[dest/'j'],dest/'MERGED.json')
report.build(dest/'MERGED.json',dest,[R/'in/comparators/f17.per_question_scores.jsonl',R/'in/comparators/p1m200.per_question_scores.jsonl'])
cov.stop();cov.save();cov.json_report(outfile=str(dest/'coverage.json'))
dump(dest/'RESULT.json',dict(passed=not completion['missing'],synthetic=True,items=len(completion['keys']),captures=len(raw['captures']),tower='real frozen G3T on CPU; original outputs unchanged',raw=original,checkpoint_prefill='synthetic own depth and gravity; real scale conversion and guard',decode='deterministic logits through the production Row loop',completion=pin(dest/'j/COMPLETE.json'),report=pin(dest/'REPORT.json'),coverage=pin(dest/'coverage.json'),timing=dict(wall_seconds_between_input_and_raw_receipts=(source/'real_raw/RAW.json').stat().st_mtime-(source/'i/BOUND.json').stat().st_mtime,source_paths=[str(source/'i/BOUND.json'),str(source/'real_raw/RAW.json')],scope='file timestamp interval; includes tower loading and validation'),not_checked=['real checkpoint prefill','GPU decode and parity','historical GPU equality','namespace and remote staging']))
