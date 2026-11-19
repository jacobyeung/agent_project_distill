"""Verify current receipts, archived members and the exact source-change scope."""
from pathlib import Path
import sys,tarfile,hashlib,csv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
O=ROOT/'out';pins=code_pins();code=digest(pins)
for name in ('CODE_SHA256.json','DRYRUN.json','GPU_NEED.json','PACKAGE.json','FIX4_DIFF.json'):
    assert read_json(O/name)['code_sha256']==code,name
tests=read_json(O/'TESTS.json')
assert tests['status']=='PASS' and tests['tests']==68 and tests['errors']==tests['failures']==0
for name in ('TESTS.json','DRYRUN.json'):
    data=read_json(O/name)
    for rel,h in pins.items():assert data['input_sha256'][str(ROOT/rel)]==h,(name,rel)
for path,h in read_json(ROOT/'work/fix4_archive_inputs.json')['input_sha256'].items():assert sha(path)==h,path
stage=read_json(O/'STAGE_TOTALS.json')
assert sha(O/'STAGE_LIST.tsv')==stage['input_sha256'][str(O/'STAGE_LIST.tsv')]
with (O/'STAGE_LIST.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
for part in (*'ABCH','union'):
    assert sum(int(r['bytes']) for r in rows if r['bytes'] and (part=='union' or part in r['parts'].split(',')))==stage['totals'][part]['bytes']
for row in rows:
    if row['kind']=='dir':
        path=ROOT/row['hash_source'].split('manifest:',1)[1].split(' (',1)[0]
        assert sha(path)==row['sha256'],path
    elif row['kind']=='file' and row['path'].startswith(str(ROOT)):
        assert sha(row['path'])==row['sha256'],row['path']
assert all(not v['unlisted'] for v in stage['trace_check'].values())
a0=read_json(O/'fix_validation/a0_rerun_summary.json')
assert a0['rows']==a0['equal']==1037 and a0['captures']==a0['set_equal']==209 and not a0['fail_rows']
subset=a0['subset_1012']
assert subset['rows']==subset['equal']==1012 and subset['captures']==subset['set_equal']==204
sha(O/'fix_validation/a0_rerun.jsonl')
replay=[json.loads(line) for line in (O/'fix_validation/a0_rerun.jsonl').read_text().splitlines()]
assert len(replay)==209 and all(r['status']=='PASS' and r['row_set_equal'] and r['input_sha256'] for r in replay)
assert sum(r['n'] for r in replay)==sum(r['n_equal'] for r in replay)==1037
assert not (O/'looks/HELDOUT_once.json').exists()
probes=read_json(O/'FIX3_PROBES.json')
assert probes['status']=='PASS' and all(p['status']=='REFUSED' for p in probes['probes'].values())
plant=read_json(O/'FIX4_plant.json');plant2=read_json(O/'FIX4_plant2.json')
assert plant['status']==plant2['status']=='PASS'
assert plant['summary']['planted_files_refused']==8
assert plant2['summary']['planted_files_refused']==30
assert all(r['returncode']!=0 and r['ok'] and not r['written'] for r in plant2['results'] if r.get('expect')=='refuse')
seen=set();incremental={}
for part in 'ABCH':
    selected={r['path']:int(r['bytes']) for r in rows if r['bytes'] and part in r['parts'].split(',')}
    incremental[part]=sum(n for p,n in selected.items() if p not in seen);seen.update(selected)
assert read_json(O/'STAGE_INCREMENTAL.json')['bytes']==incremental
members=read_json(O/'FIX4_MEMBERS.json')['files'];archive=O/'sb_ktfix4.tar'
h=sha(archive)
assert (O/'sb_ktfix4.tar.sha256').read_text().split()[0]==h
assert read_json(O/'PACKAGE.json')['sha256']==h
expected={'code/evaluate_v2.py','code/process_guard.py','code/test_kit.py','code/test_fix3.py','scripts/gpu_environment.sh'}
with tarfile.open(archive) as tar,tarfile.open(O/'sb_ktfix3.tar') as old:
    assert len(tar.getnames())==len(set(tar.getnames()))==len(members)+1
    assert set(tar.getnames())==set(members)|{'out/FIX4_MEMBERS.json'}
    for m in tar:
        assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts,m.name
    for rel,pin in members.items():assert hashlib.sha256(tar.extractfile(rel).read()).hexdigest()==pin,rel
    for rel,pin in pins.items():assert members[rel]==pin,rel
    changed=[]
    for m in old:
        if m.isfile() and m.name.startswith(('code/','scripts/','configs/','inputs/')):
            if old.extractfile(m).read()!=tar.extractfile(m.name).read():changed.append(m.name)
    assert set(changed)==expected,changed
    for name in expected-{'code/test_fix3.py'}:
        assert tar.extractfile(name).read()==(ROOT/'work/fix4_expected'/name).read_bytes(),name
    assert tar.extractfile('out/FIX4_MEMBERS.json').read()==(O/'FIX4_MEMBERS.json').read_bytes()
assert len((O/'FIX4_REPORT.md').read_text().splitlines())<=25
write_json(O/'FIX4_DELIVERY_CHECK.json',dict(status='PASS',code_sha256=code,archive_sha256=h,archive_members=len(members)+1,tests=68,plants_refused=30,a0_rows=1037,decision_rows=1012,reviewed_archives_unchanged=True,source_changes=sorted(changed),command='bash scripts/cpu.sh work/verify_fix4.py'))
print(json.dumps(dict(status='PASS',code_sha256=code,archive_sha256=h,members=len(members)+1)))
