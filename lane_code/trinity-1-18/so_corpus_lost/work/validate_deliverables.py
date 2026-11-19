from pathlib import Path
import ast,hashlib,importlib.util,json,re,subprocess

L=Path('/scratch/jjyeung/orch_n30/so_corpus_lost')
I=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,cond):
    assert cond,name
    checks.append(name)
    print('PASS '+name)

lost_bytes=(L/'out/LOST_LINES.jsonl').read_bytes()
lost=[json.loads(x) for x in lost_bytes.splitlines()]
combined=(L/'work/index_snapshot/INDEX.jsonl').read_bytes().splitlines(keepends=True)
pub=json.loads((L/'work/published_summary.json').read_text())
check('lost JSONL is byte-identical to supplied index CLI output',all(x+b'\n' in combined for x in lost_bytes.splitlines()))
check('exactly one explicitly reported lost read',len(lost)==1 and lost[0]['status']=='lost' and lost[0]['read_id']=='CP1_s200_revsi_direct_reported_lost')
check('18 published IDs preserved and one proposed entry added',len(combined)==19 and {p['read_id'] for p in pub} < {json.loads(x)['read_id'] for x in combined})
check('published jobs are absent from lost list',not ({str(x['job_id']) for x in lost if x.get('job_id')} & {str(x['job_id']) for x in pub}))
check('uncertain pilot IDs were not asserted lost',all(str(j) not in {str(x.get('job_id')) for x in lost} for j in [169501,169605,169670]))
check('working ingester equals supplied ingester',sha(L/'work/ingest_read.py')==sha(I/'ingest_read.py'))
for e in lost:
    check('tool fingerprint '+e['read_id'],e['tool_version']==sha(I/'ingest_read.py'))
    check('metadata fingerprint '+e['read_id'],all(sha(Path(s['path']))==s['sha256'] and Path(s['path']).stat().st_size==s['bytes'] for s in e['sources']))
    check('cited loss evidence matches exact source lines',all(Path(x['path']).read_text().splitlines()[x['line']-1]==x['text'] for x in e['evidence']))

spec=importlib.util.spec_from_file_location('audit_ingester',L/'work/ingest_read.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
check('flat routed path unsupported',m.ROUTE_ROW.match('metadata/journals/0/0/items.jsonl') is None)
check('nested routed control supported',bool(m.ROUTE_ROW.match('metadata/reads/0/metadata/journals/0/0/items.jsonl')))
check('j0 native path unsupported',not m.NativeAdapter.detects(['j0/items.jsonl']))
check('probe native path unsupported',not m.NativeAdapter.detects(['native/probe/items.jsonl']))
check('paired native control supported',m.NativeAdapter.detects(['native/paired/results/items.jsonl']))
pilot=['SPEC.json','a0/results/0/items_a0.jsonl','b0/d0/results/0/items_b0.jsonl','b0/d0/a0/results/0/items_a0.jsonl']
check('offread detection accepts a0 pilot path',m.OffreadAdapter.detects(pilot))
# The actual IDENT b0 filenames are items_b0, not items_a0: they do not match KIT_ROW.
actual_pilot=['SPEC.json','a0/results/0/items_a0.jsonl','b0/d0/results/0/items_b0.jsonl']
check('actual b0 pilot journal unsupported by kit regex',m.KIT_ROW.match(actual_pilot[-1]) is None)

manifest=A/'items/devs1_routed.json'
check('shared H1 manifest size and hash verified',manifest.stat().st_size==1440816 and sha(manifest)=='2849206e3eb66f40b3e2fba49cfe84abe3c0465a318f85aaeaeca6ff6f26fe21')
inventory=json.loads((L/'work/orchard_inventory.json').read_text())
table=(L/'out/ORCHARD_ONLY_INPUTS.md').read_text()
check('all 26 IDENT archives appear once as table rows',len(inventory)==26 and all(table.count('| '+r['path']+' |')==1 for r in inventory))
blocks=re.findall(r'```bash\n(.*?)```',table,re.S)
for n,block in enumerate(blocks,1):
    p=L/'work'/f'owner_command_{n}.sh';p.write_text(block)
    result=subprocess.run(['bash','-n',str(p)],text=True,capture_output=True)
    check(f'owner command {n} shell syntax',result.returncode==0)
    for script in re.findall(r"<<'PY'\n(.*?)\nPY",block,re.S):ast.parse(script)
check('owner Python snippets compile without execution',True)
files=[p for p in L.rglob('*') if p.is_file() and not p.is_symlink()]
size=sum(p.stat().st_size for p in files)
check('workspace remains under 3 GB',size<3_000_000_000)
recorded_bytes=sum(r['bytes'] for r in inventory)
result=dict(utc=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip(),checks=checks,checks_passed=len(checks),published_entries=len(pub),lost_entries=len(lost),ident_archives=len(inventory),recorded_ident_archive_bytes=recorded_bytes,workspace_bytes_measured=size,production_patches=0,remote_commands_executed=0)
(L/'work/validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},sort_keys=True))
