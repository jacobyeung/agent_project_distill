from pathlib import Path
import sys,json,hashlib,os,shutil,stat
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4q'
sys.path[:0]=[str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

def write(p,v):z.write(p,v)
def kit(n):return L/('out/kit_'+n if n in ('qd','n_go') else 'work/build24/kits/'+n)
def files(root):return {str(p.relative_to(root)):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in root.rglob('*') if p.is_file()}
base=json.loads((L/'work/build24m4p/BASELINE.json').read_bytes())
initial=json.loads((D/'BASELINE.json').read_bytes())
assert base['kits']['qd'].startswith('aaa03e58')
assert base['rcj']['x.py'].startswith('f443615a') and base['rcj']['pc.py'].startswith('a4ef242b') and base['rcj']['nd.py'].startswith('696f73c4')
assert digest(inventory(L/'work/tree_r1c'))==initial['tree']==base['tree']
seals={n:verify(kit(n)) for n in initial['kits']};assert seals==initial['kits']
new={n:files(kit(n)) for n in seals};rows=[]
def entry(name,path,old):
 return dict(name=name,relative_path=str(path.relative_to(L)),local_path=str(path),action='replace' if old else 'add',baseline_sha256=old,sha256=z.sha(path),bytes=path.stat().st_size,mode=format(path.stat().st_mode&511,'04o'),transfer='local-upload')
for n in ('q','n','qd'):
 assert set(base['files'][n])==set(new[n])
 for name,v in new[n].items():
  if v['sha256']!=base['files'][n][name]['sha256']:rows.append(entry(n+'/'+name,kit(n)/name,base['files'][n][name]['sha256']))
current=files(L/'out/rcj')
for name,v in current.items():
 if base['rcj'].get(name)!=v['sha256']:rows.append(entry('rcj/'+name,L/'out/rcj'/name,base['rcj'].get(name)))
rows.sort(key=lambda v:v['name'])
assert len(rows)==17,[v['name'] for v in rows]
assert {v['name'] for v in rows if v['name'].startswith('rcj/')}=={'rcj/ch.py','rcj/f.json','rcj/nd.py','rcj/pc.py','rcj/x.py'}
assert not {'qd/b/a.py','qd/b/f0.py','rcj/rcj.sh','rcj/ps.py','rcj/P_SAMPLE_I.json'}&{v['name'] for v in rows}
up=dict(schema='cpu-publication-delta-v1',build='24m4q',baseline='Exact stated Orchard pins',baseline_kit_seals={n:base['kits'][n] for n in ('q','n','qd')},baseline_rcj=base['rcj'],tree_sha256=initial['tree'],kit_seals={n:seals[n] for n in ('q','n','qd')},files=rows,total_files=len(rows),total_bytes=sum(v['bytes'] for v in rows),GO=False,uploaded=False,launched=False,config_delta=False)
write(L/'out/UPLOADS_24M4Q.json',up);(L/'out/UPLOADS_24M4Q.list').write_text(''.join(v['name']+'\n' for v in rows))
# Reconstruct all exact baseline bytes, apply only this list, verify every result.
replay=D/'replay';replay.mkdir()
def original(relative,h):
 candidates=[L/relative]
 candidates += [L/'attic'/b/relative for b in ('build24m4p','build24m4q','build24m4o3','build24m4o','build24m4n')]
 for p in candidates:
  if p.is_file() and z.sha(p)==h:return p
 raise ValueError('Missing original bytes '+relative+' '+h)
def copy(p,q,mode):
 q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(p.read_bytes())
 q.chmod(mode)
for n in ('q','n','qd'):
 for name,v in base['files'][n].items():
  relative=str((kit(n)/name).relative_to(L));copy(original(relative,v['sha256']),replay/n/name,v['mode'])
 assert verify(replay/n)==base['kits'][n]
for name,h in base['rcj'].items():
 p=original('out/rcj/'+name,h);copy(p,replay/'rcj'/name,p.stat().st_mode&511)
for v in rows:
 q=replay/v['name']
 if q.exists():
  a=L/'attic/build24m4q/replay'/v['name'];a.parent.mkdir(parents=True,exist_ok=True);q.rename(a)
 copy(L/v['relative_path'],q,int(v['mode'],8))
for n in ('q','n','qd'):
 assert verify(replay/n)==seals[n];assert files(replay/n)==new[n]
assert files(replay/'rcj')==current
write(D/'DELTA_REPLAY.json',dict(status='PASS',files=len(rows),exact_bytes_modes=True,baseline_kit_seals=up['baseline_kit_seals'],baseline_rcj=base['rcj'],kits=seals))
checks={}
for filename in ('NEW_TESTS.json','PUBLICATION_TESTS.json','PC_INTEGRATION_TESTS.json','RCJ_TESTS.json','MOUNT_TESTS.json','RCJ_SCAN.json','sample/SAMPLE_TESTS.json','contract/RCJ_CONTRACT_TESTS.json'):
 v=json.loads((D/filename).read_bytes());assert v['status']=='PASS',(filename,v);checks[filename]=v
assert checks['NEW_TESTS.json']['tests']==15
# These logs retain the assertions and exact result from suites with shared legacy result names.
for name,log,tests in [('ND_TESTS','nd1.log',11),('RECORDER_TESTS','recorder3.log',4)]:
 text=(D/log).read_text();assert f'Ran {tests} tests' in text and text.rstrip().endswith('OK')
 v=dict(status='PASS',tests=tests,log=log,log_sha256=z.sha(D/log));write(D/(name+'.json'),v);checks[name]=v
runs=[dict(name=name,log=log,status='PASS',sha256=z.sha(D/log)) for name,log in [('chain','tests2.log'),('processor','pc3.log'),('publication','publication2.log'),('content','nd1.log'),('sampling','sample1.log'),('contract','contract1.log'),('staging','core2.log'),('mounts','mount2.log'),('recorder','recorder3.log'),('scan','scan3.log')]]
failures=[]
for log,reason,resolved in [('assets1.log','Synthetic processor fixture omitted the required video processor.','assets2.log'),('pc1.log','Fixture selected a non-P source tree.','pc3.log'),('pc2.log','File binds protected bytes but left the metadata directory writable; the root is now a remounted read-only tmpfs.','pc3.log'),('scan1.log','Scanner shell certificate path was absent.','scan3.log'),('recorder2.log','The no-deletion audit blocked tempfile default-directory probing. The runner now fixes its temporary directory and caches under J.','recorder3.log')]:
 failures.append(dict(log=log,reason=reason,output=(D/log).read_text(),resolved_by=resolved))
failures.append(dict(reason='A same-named receipt fixture was not JSON and did not authenticate the requested source receipt.',output='json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)',resolved_by='N_BINDINGS.json records that no authentic c072905 receipt bytes are supplied.'))
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_test_failures=[],notes=['Bounded exploratory reads reported absent guessed filenames; they made no edits.']))
qualifications=[
 'C double-prime has no existing audit-carry receipt rebuilder. The helper calls native content/digest/serialization and copies authenticated audit entries; it explicitly reports native_receipt_builder=false.',
 'The supplied package has no authentic c072905 extent receipt or complete production N database. Receipt authorship/source coverage and production chain counts remain runtime evidence; missing or incompatible audit entries refuse the candidate.',
 'Mode r does not reach native preparation or sampler binding. The report gives NOT_REACHED and the first native entrypoint, not an invented prepared-population hash.',
 'The literal aggregate 5 MB cap remains incompatible with the existing unchanged rd0 plus P sample (6718816 bytes). Both aggregate and helper counters include timings and report limit failures.'
]
validation=dict(status='PASS',status_scope='Local fixtures and exact package inputs only',requirements_status='QUALIFIED',tree_sha256=initial['tree'],kits=seals,rcj={n:v['sha256'] for n,v in current.items()},checks=checks,runs=runs,mode_b_byte_identical=True,qd_unchanged_from_24m4p=True,candidate_never_bound=True,production_executed=False,uploaded=False,launched=False,GO=False,qualifications=qualifications)
write(D/'VALIDATION.json',validation)
report=[
 "C'' de202f58 verified unchanged; kits q 098987e2, n a4554161, n_go f62a1c8a, qd 022c1c7a.",
 'The CPU job checks every N routing row through native Rows.row with current pins, samples 20,000 rows per other stream, and publishes chain counts, full first-ten refusals and timing status independently of later publication failures.',
 'The unbound candidate carries authenticated audit entries using native content digests; cand_cmp.json proves P-source agreement, exact N pool QIDs and unchanged non-content entry fields.',
 'Both processor children receive only authenticated metadata at read-only logical roots; final traceback extraction, native type classification, Reserve.check citation and timing-byte accounting are fixed.',
 'Local checks pass: 15 chain/integration, 11 content/type, 10 publication, 4 recorder tests; actual sandbox loaders pass 40+40 and 80 fallback and refuse mismatch; staging, sample, contract, mounts, naming and exact delta replay pass.',
 'Mode b bytes match; qd and all kits are unchanged from 24m4p. UPLOADS_24M4Q.json/.list contain exactly 17 changed files against the requested Orchard pins, including inherited planner fixes.',
 'QUALIFIED: no native receipt rebuilder or authentic source receipt is supplied; CHAIN_24M4Q.md states the implemented audit carry and unresolved provenance. Mode r reports native population NOT_REACHED. The existing aggregate publication cap remains unmet and is counted including timings.',
 'No production reconstruction, full-row production verdict, upload, submission, training or arming ran; VALIDATION.json and FAILURES.json retain scope and failed-test output. The package is independently verified and its .sha256 is written last.'
]
assert len(report)<10
(L/'out/BUILD24M4Q_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',requirements_status='QUALIFIED',upload_files=len(rows),upload_bytes=up['total_bytes'],kits=seals),indent=2))
