"""Check the delivered code, validation receipts, staging inventory and archive."""
from pathlib import Path
import csv,hashlib,json,sys,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
O=ROOT/'out';pins=code_pins();code=digest(pins)
for name in ('CODE_SHA256.json','DRYRUN.json','GPU_NEED.json','PACKAGE.json'):
 d=read_json(O/name);assert d['code_sha256']==code,name
tests=read_json(O/'TESTS.json');assert tests['status']=='PASS' and tests['tests']==42
for name in ('TESTS.json','DRYRUN.json'):
 d=read_json(O/name)
 for rel,h in pins.items():assert d['input_sha256'][str(ROOT/rel)]==h,(name,rel)
stage=read_json(O/'STAGE_TOTALS.json')
assert sha(O/'STAGE_LIST.tsv')==stage['input_sha256'][str(O/'STAGE_LIST.tsv')]
with (O/'STAGE_LIST.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
for part in (*'ABCH','union'):
 total=sum(int(r['bytes']) for r in rows if r['bytes'] and (part=='union' or part in r['parts'].split(',')))
 assert total==stage['totals'][part]['bytes'],part
for row in rows:
 if row['kind']=='dir':
  path=ROOT/row['hash_source'].split('manifest:',1)[1].split(' (',1)[0]
  assert sha(path)==row['sha256'],path
assert all(not c['unlisted'] for c in stage['trace_check'].values())
ex=read_json(O/'EXCLUSIONS.json');assert ex['decision_rows']==1012 and ex['full_rows']==1037
assert len(ex['planted_rows'])==5 and len(ex['excluded'])==6
a0=read_json(O/'fix_validation/a0_rerun_summary.json')
assert a0['rows']==a0['equal']==1037 and a0['captures']==a0['set_equal']==209 and not a0['fail_rows']
subset=a0['subset_1012'];assert subset['rows']==subset['equal']==1012 and subset['captures']==subset['set_equal']==204
sha(O/'fix_validation/a0_rerun.jsonl')
replay=[json.loads(line) for line in (O/'fix_validation/a0_rerun.jsonl').read_text().splitlines()]
assert len(replay)==209 and all(r['status']=='PASS' and r['row_set_equal'] for r in replay)
assert sum(r['n'] for r in replay)==sum(r['n_equal'] for r in replay)==1037
assert not (O/'looks/HELDOUT_once.json').exists()
assert not (O/'tower_frames/PER_ITEM.jsonl').exists()
members=read_json(O/'FIX2_MEMBERS.json')['files'];archive=O/'sb_ktfix2.tar'
archive_sha=sha(archive);assert (O/'sb_ktfix2.tar.sha256').read_text().split()[0]==archive_sha
with tarfile.open(archive) as t:
 assert len(t.getnames())==len(members)+1
 for rel,h in members.items():assert hashlib.sha256(t.extractfile(rel).read()).hexdigest()==h,rel
 for rel,h in pins.items():assert members[rel]==h,rel
 for rel in ('scripts/run_H.sh','code/process_guard.py','out/FIX2_REPORT.md','work/refresh_stage.py'):
  assert rel in members,rel
report=O/'FIX2_REPORT.md';assert len(report.read_text().splitlines())<=45
write_json(O/'FIX2_DELIVERY_CHECK.json',dict(status='PASS',code_sha256=code,archive_sha256=archive_sha,
 tests=42,a0_rows=1037,decision_rows=1012,stage_totals=stage['totals'],archive_members=len(members)+1,
 command='bash scripts/cpu.sh work/verify_fix2.py'))
print(json.dumps(dict(status='PASS',code_sha256=code,archive_sha256=archive_sha,members=len(members)+1)))
