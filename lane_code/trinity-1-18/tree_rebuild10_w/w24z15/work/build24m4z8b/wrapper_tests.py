import ast,base64,hashlib,importlib.util,json,os,re,subprocess,sys,gzip
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b';F=D/'wrapper_fixture';F.mkdir();K=L/'out/kit_qdp'
sys.path[:0]=[str(K/'b'),str(L/'work/tree_r1c'),str(D)]
import z
sp=importlib.util.spec_from_file_location('j7',L/'out/j7.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912')
r=json.loads((S/'k_r.json').read_bytes())['_resolved'];node=F/'n_123';physical=node/'dr';(physical/'p/q/u').mkdir(parents=True)
rules=[]
from common import input_file
for row in r['config']['remove_files']:
 h=row['sha256'];p=input_file(h);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
 (physical/'p/q/u'/h).write_bytes(raw);rules.append(dict(row,path='/tmp/q_22c714e1/p/q/u/'+h))
source=physical/'p/q/n.json';source.write_text(json.dumps(dict(remove_files=rules)))
rd=S/'rdiff.py';sp=importlib.util.spec_from_file_location('rdiff_test',rd);rdiff=importlib.util.module_from_spec(sp);sp.loader.exec_module(rdiff)
from types import SimpleNamespace
args=SimpleNamespace(tree=str(L/'work/tree_r1c'),removal_manifest=str(source),base=str(physical/'p/q'),remove_files=[],defects=[])
try:rdiff.get_removals(args)
except FileNotFoundError as e:before=str(e)
else:raise AssertionError('Expected logical namespace refusal')
normalized=node/'rdm.json';m.remap(source,physical,normalized);args.removal_manifest=str(normalized)
removal,info=rdiff.get_removals(args)
assert len(removal.files)==len(rules)==13
fixed=json.loads(normalized.read_bytes())['remove_files']
assert [p['sha256'] for p in fixed]==[p['sha256'] for p in rules]
assert [p.get('defects') for p in fixed]==[p.get('defects') for p in rules]
# Evidence copies preserve exact bytes, including native filters and offset maps.
for name in ('population','indices','reader_filters','binding','receipt','routing_indices'):
 p=node/'p/q/b'/(name+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(dict(fixture=True,kind=name,rows=list(range(200)))))
(node/'ev').mkdir()
for name in ('routing_selection.json','db_bytes.json','q.log'):(node/'ev'/name).write_bytes((S/name).read_bytes())
target=F/'o/123';record=m.publish(node,target,K,1)
for row in record['files']:
 raw=(target/row['name']).read_bytes()
 if row['name'].endswith('.gz'):raw=gzip.decompress(raw)
 assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes']
assert any(x['source']=='p/q/b/routing_indices.json' for x in record['files'])
assert sum(p.stat().st_size for p in target.rglob('*') if p.is_file())<5_000_000
# Oversize output is refused before any payload reaches the result directory.
large=F/'large';(large/'ev').mkdir(parents=True);(large/'ev/x').write_bytes(os.urandom(3_600_000))
try:m.publish(large,F/'o/124',K,0)
except ValueError as e:assert str(e)=='E95'
else:raise AssertionError('Cap was not enforced')
assert not any((F/'o/124').iterdir())
old=(L/'inputs/jd6.sh').read_text();new=(L/'out/jd7.sh').read_text();pp=(L/'out/pp/pp.sh').read_text()
def heredoc(s):return s.split("<<'PYJ2'\n",1)[1].split('\nPYJ2',1)[0]
assert heredoc(old)==heredoc(new)
assert '--removal-manifest "$N/rdm.json"' in new and '"$X/j7.py" m "$N/dr/p/q/n.json" "$N/dr" "$N/rdm.json"' in new
assert '--bind "$N/ev" "$O"' in new
for s in (new,pp):assert re.search(r'--job-name=a15_cot_ap[0-9a-f]{12}\n',s)
assert '${SLURM_JOB_ID:?}' in pp and '$SLURM_JOB_ID' in pp
assert '--gres' not in pp and '--cpus-per-task=8' in pp and 'CUDA_VISIBLE_DEVICES=""' in pp
assert '/tmp/' in pp and not re.search(r'\bsbatch\b|\bsrun\b|\bssh\b',pp)
for p in (L/'out/jd7.sh',L/'out/pp/pp.sh'):subprocess.run(['bash','-n',str(p)],check=True)
code=base64.b64decode(json.loads((K/'k/j.json').read_bytes())['payload']).decode()
assert '"$Q_KIT/b/a.py" q' in code and '"$Q_KIT/b/a.py" t' not in code
assert '"$Q_KIT/b/e.sh"' not in code and not (K/'b/e.sh').exists()
# No planning helper can invoke the staged hook or the training entry.
probe=ast.parse((L/'out/j7.py').read_text());calls=[ast.unparse(n.func) for n in ast.walk(probe) if isinstance(n,ast.Call)]
assert 'pl.plan_payload' in calls and 'stage' not in calls and not any(x.endswith('.train') for x in calls)
result=dict(status='OK',rdiff_sha256=z.sha(rd),rdiff_before=before,rdiff_after_removal_files=len(removal.files),defects_preserved=True,j2_identical=True,publication_bytes=record['bytes'],cap_refused=True,syntax=True,mode_q_real_path='REAL_PATH_TESTS.json',scope='Real 13 removal files and unchanged native removal reader; publication uses explicit synthetic population fixtures and actual 173912 diagnostics. No scheduler or GPU.')
(D/'WRAPPER_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
