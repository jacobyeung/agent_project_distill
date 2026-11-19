from pathlib import Path
import ast,datetime,gzip,hashlib,io,json,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
base=J.load(D/'BASELINE.json');tree=inventory(L/'work/tree_r1')
assert tree==base['tree'];tree_sha=digest(tree)
assert tree_sha=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
for n,h in base['packages'].items():assert J.sha(L/'out'/n)==h
kits={n:L/('out/kit_n_go' if n=='n_go' else 'work/build24/kits/'+n) for n in ('q','n','n_go')}
seals={};changes={}
for n,k in kits.items():
 seals[n]=verify(k);current={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
 changes[n]=[f for f in sorted(set(current)|set(base['kits'][n])) if current.get(f)!=base['kits'][n].get(f)]
 assert J.load(k/'k/a.json')['GO']==(n=='n_go')
 assert 'review' not in J.load(k/'k/a.json')
 assert J.load(D/('SCAN_'+n+'.json'))['status']=='PASS'
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
 for cfg in ('k/c.json','k/n.json','k/p.json','k/r.json','k/h.json'):
  assert current[cfg]==base['kits'][n][cfg]
assert changes['q']==[]
expected=['BUILD.json','SHA256SUMS.txt','b/a.py','b/h.py','b/pc.py','b/pc.sh','b/sr.py','b/z.py','job.sh']
assert changes['n']==changes['n_go']==expected
for name in expected[2:]:assert J.sha(kits['n']/name)==J.sha(kits['n_go']/name)
for name in ('identities','export_identity','metadata_closure','receipt600','checkpoint600','bound400','resolve','resolve600'):
 old=ast.parse((L/'attic/build24h/work/build24/kits/n/b/z.py').read_text());new=ast.parse((kits['n']/'b/z.py').read_text())
 node=lambda x:next(n for n in x.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(node(old))==ast.dump(node(new))
for name in ('COPIER_TESTS','COPIER_GO_TESTS','SIGNAL_FINAL_TESTS','RECEIPT_TESTS','SESSION_TESTS','REVIEW_STAGING_TESTS','HOST_CAPTURE_TEST'):
 assert J.load(D/(name+'.json'))['status']=='PASS'
for name in ('LIVE_TESTS','RUNTIME_TESTS'):assert J.load(D/(name+'.json'))['passed']
for name in ('KIT_TESTS','NAMING_TESTS','RESOLVER_TESTS'):assert J.load(D/(name+'.json'))['successful']
for name in ('SUITES','VALIDATION'):assert all(v['returncode']==0 for v in J.load(D/(name+'.json')))
sequence=J.load(D/'SEQUENCE.json');assert set(sequence)=={'q','n'}
for n,v in sequence.items():
 assert v['status']=='BOUNDARY' and v['kit_bytes_unchanged']
 # Only sr.py changed after the full sequence; the final signal tests exercise it.
 assert v['first_refusal'].startswith('ValueError: Missing or changed pinned input: /scratch/fsw/')
up=J.load(L/'out/UPLOADS_24H.json');assert up['total_files']==9
for r in up['files']:assert J.sha(r['local_path'])==r['sha256']
assert not (L/'out/kit_n_go_armed').exists() and not (L/'out/UPLOADS_ARMED.json').exists()
identity=J.load(D/'IDENTITY_COMPARISON.json');assert identity['status']=='BLOCKED_FINAL_IDENTITY'
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=tree_sha,tree_files=len(tree),changed_kit_files=changes,kits=seals,existing_packages_unchanged=True,configs_unchanged=True,resolver_identity_functions_unchanged=True,production_GO=False,production_host_receipt=False,production_review=False,production_admission='BLOCKED',excluded_rehearsal_paths_untouched=True,tests_use_synthetic_receipts_only=True))
# Retain the superseded operator card exactly once.
p=L/'out/N_CARD_KIT_ROWS.md';text=p.read_text()
old=L/'attic/build24h/out/N_CARD_KIT_ROWS.md';old.parent.mkdir(parents=True,exist_ok=True)
if not old.exists():p.rename(old)
else:text=old.read_text()
for n in ('q','n','n_go'):text=text.replace(J.load(L/'out/DELIVERY_24G.json')['kits'][n],seals[n])
text=text.replace('Vehicle N uses MINIMAL. Normal kits have GO=false; only out/kit_n_go is armed and it is not uploaded.','Vehicle N uses MINIMAL. Production launch is BLOCKED; normal kits have GO=false. The GO template has no review and is not uploaded.')
text=text.replace('work/build24g/INVARIANTS.json and out/UPLOADS_24G_GO.json','work/build24h/INVARIANTS.json and out/UPLOADS_24H_GO.json')
text=text.replace('The batch shell copies log tails, metrics, attempt/run metadata, marker hashes and .steps every 600 seconds and at EXIT/TERM/USR1.','After kit verification, the batch shell copies log tails, metrics, attempt/run metadata, marker hashes and .steps every 600 seconds and at exit.')
text=text.replace('--sessions PATH explicitly overrides it.','--sessions PATH may select another filename only inside n_root/n_s. Live, claims, n_ck and sessions paths inside either kit copy or outside their expected subtrees refuse.')
text=text.replace('A separate worker checks export artifact markers every 10 seconds and sends immutable export tars through four GCS parts when sessions exist.','A separate worker checks export artifact markers every 10 seconds and sends immutable export tars through four GCS parts when sessions exist. A broken export records its status without blocking later exports.')
text += 'TERM/USR1 signals only torchrun workers with an installed USR1 handler, waits up to 420 seconds, then runs final publication; the trainer exit code is preserved.\n'
text += 'The 585-second cleanup budget reserves 15 seconds of the 600-second warning and assumes no KillWait grace. A wait timeout copies small evidence only; large-copy completion is not guaranteed.\n'
text += 'h.py requires a real host result at Q_NS/p/host.json and a sha256-pinned independent review of the final config; each invalid receipt refuses before t.py.\n'
text += 'The sealed mode-q path produces no frame_host result. The hidden-view input identity is not a verified final training identity; see out/PRODUCTION_BLOCKERS.md.\n'
text += 'n_review1 must supply the review. out/arm_go.py stages it and writes UPLOADS_ARMED only when called; no armed production kit or review is supplied.\n'
assert len(text.splitlines())<40;p.write_text(text)
report=[
'BUILD24H PACKAGED WITH PRODUCTION ADMISSION BLOCKED. No upload or launch occurred.',
'Tree '+tree_sha+' is byte-identical across '+str(len(tree))+' files; existing packages are unchanged (work/build24h/INVARIANTS.json).',
'Kit n: '+seals['n']+'; kit q: '+seals['q']+'.',
'GO template: '+seals['n_go']+'; it has no review pin. Normal kits remain GO=false.',
'Kit n and the GO template start copiers after verification and reject kit-contained or unexpected destinations before writing.',
'TERM/USR1 targets torchrun workers after their handler is installed; cleanup awaits the workload and preserves its exit status.',
'The budget is 420 seconds for training, 10 for copier shutdown and 155 for publication, leaving 15 of the 600-second warning; no KillWait grace is assumed.',
'A trainer timeout returns 124 and copies small evidence only. Production-sized transfers were not timed; final publication is bounded.',
'Per-export failures record pending status and do not block later exports. Kit q has no copier and retains identical bytes.',
'Copier A/B/C failing-before and passing-after tests cover both kits; delayed-handler signal tests copy the final export and preserve exit 7 (COPIER_TESTS, COPIER_GO_TESTS, SIGNAL_FINAL_TESTS.json).',
'h.py checks host status, exact identity, assertions and loader completion, then pins host and review snapshots before writing v.json.',
'Nine invalid receipt cases refuse by name before t.py; a fixture review armed through arm_go.py produces a config accepted by native admit() (RECEIPT_TESTS.json).',
'The resolver authenticates and localises the review staged in u/<sha256>; missing and changed bytes refuse (REVIEW_STAGING_TESTS.json).',
'out/arm_go.py performs CPU-only arming, resealing and decoded scanning; it emits the four-file armed delta only when called with a review.',
'out/identity.py computed '+identity['localised_input_identity']+' in the hidden view and wrote N_PRODUCTION_CONFIG.json and N_IDENTITY.txt.',
'BLOCKER: a.py q calls production_proof.run(), which never calls frame_host(). Only mode p calls it; k/h.json has three missing host-proof pins.',
'The adapter records actual frame_host returns at Q_NS/p/host.json, but cannot supply a production q receipt. No synthetic production PASS is created.',
'BLOCKER: preparation creates identity-bearing fields. The hidden canary has no final config; input/final equality is unproven and unsafe to assume (IDENTITY_COMPARISON.json).',
'Both hidden look-aheads pass room audit and reach the production-store boundary; h.py/t.py/u.py remain unreached in that view (SEQUENCE.json).',
'Decoded q/n/GO scans, kit/naming/resolver/guard suites, live/runtime suites and 13 session tests pass; sessions do not leak (SCAN_*, VALIDATION, SESSION_TESTS.json).',
'UPLOADS_24H contains '+str(up['total_files'])+' files and '+str(up['total_bytes'])+' bytes; stream root work/build24h/upload. UPLOADS_24H_GO remains unauthorized.',
'REVIEW_SCHEMA.md specifies the two admission fields and ignored evidence object. n_review1 must write the production review; launch GO remains separate.',
'The supplied A-C findings were checked against 24g. The reviewer file was not opened: its exact filename was not provided, and /home discovery is forbidden.',
'No excluded rehearsal path was modified. No GPU, network, SSH, scheduler, Git, other agent or production arming was used.',
'Evidence names without a prefix are under work/build24h. out/DELIVERY_24H.json records the package hash and member verification.'
]
assert len(report)<30;(L/'out/BUILD24H_REPORT.md').write_text('\n'.join(report)+'\n')
selected={}
def add(p):
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for n in tree:add(L/'work/tree_r1'/n)
for k in kits.values():
 for p in k.rglob('*'):add(p)
for root in (D/'upload',D/'scanners'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and p.suffix in ('.py','.sh','.json','.log') and p.name not in ('PACKAGE_MANIFEST.json','package.log'):add(p)
for folder in ('guard_q','guard_n'):
 for p in (D/folder).glob('*.json'):add(p)
for n in ('identity.py','arm_go.py','N_PRODUCTION_CONFIG.json','N_IDENTITY.txt','REVIEW_SCHEMA.md','PRODUCTION_BLOCKERS.md','UPLOADS_24H.json','UPLOADS_24H.list','UPLOADS_24H_GO.json','BUILD24H_REPORT.md','N_CARD_KIT_ROWS.md','SESSION_NAMES_24F.json','DELIVERY_24G.json','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/n)
for n in ('work/build24/joblib.py','work/build21/environment21f.py'):add(L/n)
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
base_delivery=J.load(L/'out/DELIVERY_24G.json')
record=dict(schema='build24h-overlay-v1',package_seal=seal,base=dict(path=base_delivery['package'],sha256=base_delivery['sha256']),files=manifest,tree_sha256=tree_sha,kits=seals,production_admission='BLOCKED')
J.write(D/'PACKAGE_MANIFEST.json',record);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24h_'+seal[:8]+'.tar');seen={}
with target.open('xb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w|') as t:
 for n,p in sorted(selected.items()):
  raw=p.read_bytes();info=tarfile.TarInfo(n);info.mode=0o755 if p.stat().st_mode & 0o111 else 0o644
  h=hashlib.sha256(raw).hexdigest()
  if h in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[h];t.addfile(info)
  else:seen[h]=n;info.size=len(raw);t.addfile(info,io.BytesIO(raw))
expected={n:J.sha(p) for n,p in selected.items()}
with tarfile.open(target) as t:assert {m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}==expected
J.write(L/'out/DELIVERY_24H.json',dict(status='PACKAGED_BLOCKED',package=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=J.sha(target),package_seal=seal,verified_members=len(selected),base=record['base'],tree=dict(tree_sha256=tree_sha,files=len(tree)),kits=seals,GO=False,production_host_receipt=False,production_review=False,production_admission='BLOCKED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),uploads=dict(files=up['total_files'],bytes=up['total_bytes']),checks='PASS',rehearsal='UNTOUCHED'))
print(json.dumps(J.load(L/'out/DELIVERY_24H.json'),indent=2))
