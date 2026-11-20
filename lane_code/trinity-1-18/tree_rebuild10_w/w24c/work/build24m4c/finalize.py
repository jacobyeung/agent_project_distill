from common import *
from copy import deepcopy
from student_pilot.source_seal import inventory, check_archive
from student_pilot.p3_provenance import digest, file_pin
from student_pilot.r1_launch22 import validate_removals, REMOVAL_ORDER, POINTING_K1_REMOVE, NAMING_REMOVE
from student_pilot.r1_persisted import scope
from launch_r1.build import verify

B=L.parent/'w24'
files=inventory(T);tree=digest(files)
assert tree=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
assert files==J.load(D/'TREE24L4_SEAL.json')['files']
ledger=J.load(D/'UNCHANGED24L4.json')
for n,v in ledger['files'].items():assert files.get(n)==v['after'],n
seals={name:verify(kit(name)) for name in ('q','n','n_go','qd')}
paths={v['sha256']:v['local_path'] for v in J.load(B/'work/build24m2c/UPLOADS_q.json')['files']}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
config_checks=[]
for name in seals:
 k=kit(name);control=J.load(k/'k/a.json')
 assert control['GO']==(name=='n_go')==J.load(k/'BUILD.json')['GO']
 assert control['source']['tree_sha256']==tree
 check_archive(file_pin(k/control['source']['path']),files)
 assert J.load(k/'k/7.json')['files']==files
 code=J.load(k/'k/c0.json');assert code['files']==files
 spec=J.load(k/'k/p.json');assert J.sha(D/'u'/spec['code_sha256'])==spec['code_sha256']
 for rel in ('k/c.json','k/n.json'):
  cfg=J.load(k/rel);old=J.load(L/'attic/build24m4c'/k.relative_to(L)/rel)
  assert tuple(p['sha256'] for p in cfg['remove_files'])==REMOVAL_ORDER[:-1]+(POINTING_K1_REMOVE,NAMING_REMOVE)
  assert all('role' not in p and 'stream' not in p for p in cfg['remove_files'])
  with scope(paths):validate_removals(cfg)
  a=deepcopy(cfg);b=deepcopy(old)
  for c in (a,b):
   c.pop('code',None)
   for p in c['remove_files']:p.pop('role',None);p.pop('stream',None)
  assert a==b,(name,rel)
  config_checks.append(dict(kit=name,capsule=rel,native_validator='PASS'))
 scan=J.load(D/('SCAN_'+name+'.json'));assert scan['status']=='PASS' and scan['kit_seal']==seals[name]
 assert 'check_protected_rooms' not in (k/'b/cs.py').read_text()
 assert 'def preflight' not in (k/'b/cs.py').read_text()
 for rel in ('b/h.py','b/rv.py'):assert "if cfg.get('remove_files'):" in (k/rel).read_text()

# Every original byte remains either at its original location or in the attic.
original=J.load(D/'ORIGINAL.json');preserved={}
for rel,h in original.items():
 p=L/rel
 if p.is_file() and J.sha(p)==h:preserved[rel]=rel;continue
 p=L/'attic/build24m4c'/rel
 assert p.is_file() and J.sha(p)==h,rel
 preserved[rel]=str(p.relative_to(L))
J.write(D/'PRESERVED_ORIGINALS.json',dict(status='PASS',files=len(preserved),locations=preserved))
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=tree,tree_files=944,kits=seals,configs=config_checks,
 tree_files_match_seal_and_ledger=True,original_files_preserved=True,config_changes='Only code pins and removal role/stream metadata; constant order unchanged',
 admission_legality_opener_step544_resolver_DEFERRED_unchanged=True,GO='false except unuploaded n_go'))

checks={}
for rel in ('TREE_AND_CONFIG_TESTS.json','KIT_TESTS.json','NAMING_TESTS.json','RESOLVER_TESTS.json','LIVE_TESTS.json','REVIEW_TESTS.json','SECURITY_TESTS.json','ROUTING_TESTS.json','NATIVE_HOST_TESTS.json','CENSUS_BYTE_TESTS.json','CLASSIFIER_TESTS.json','DISCOVERY_CENSUS_SHELL_TESTS.json','RV_AND_DELTA_TESTS.json','HIDDEN_PATH_TESTS.json'):
 p=D/rel;v=J.load(p)
 assert v.get('status')=='PASS' or v.get('successful') is True or v.get('passed') is True,(rel,v)
 checks[rel]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status='PASS',tests=v.get('tests'))
for rel in ('work/build24/RESOLVER_TESTS.json','work/build24m4c/proofs/resolver23/RESOLVER_TESTS.json'):
 p=L/rel;v=J.load(p);assert v['successful'];checks[rel]=dict(path=rel,sha256=J.sha(p),status='PASS',tests=v['tests'])
for n in ('q','n'):
 for rel in ('GUARD_TESTS.json','LEGACY_GUARD_TESTS.json'):
  p=D/('guard_'+n)/rel;v=J.load(p);assert v['successful'];checks[str(p.relative_to(D))]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status='PASS',tests=v['tests'])
J.write(D/'VALIDATION.json',dict(status='PASS',checks=checks,kits=seals,production_admission='NOT_RUN',
 boundaries=['Synthetic source and admitted SQLite stores with authentic room-authority and 320-key list bytes',
 'Native VQA Binding.room tested with synthetic source/twin binding pins; both pointing canonical resolutions tested',
 'Actual census, h.py and rv.py execute; host and preparation boundaries in the discovery shell fixture are synthetic',
 'Native routing rebuild and selection verification use tiny retained synthetic rows',
 'Hidden-path tests retain real metadata receipt bytes; unavailable production payload bodies use declared inventory boundaries',
 'GPU guards use query stubs; no GPU, production training, network or scheduler run'],
 operational_exceptions=['Disk growth exceeded 150 MB during fixture expansion; observed growth was at least 367820800 bytes. Final retained size is recorded separately.',
 'A legacy test-helper import attempted a write to read-only w24; the filesystem rejected it. Final tests use isolated helpers.']))

# The uploaded base is 24m2d. The source workspace base is 24m3.
base=J.load(L/'work/build24m3/BASELINE.json');upload=D/'upload';upload.mkdir()
records=[]
def record(p,name,action):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action=action)
for name in ('q','n','qd'):
 for p in sorted(kit(name).rglob('*')):
  if not p.is_file():continue
  rel=str(p.relative_to(kit(name)));old=base[name].get(rel)
  if old and J.sha(p)==old['sha256'] and p.stat().st_mode&511==old['mode']:continue
  dst=upload/name/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.link(p,dst)
  records.append(record(dst,name+'/'+rel,'replace' if old else 'add'))
for p in sorted((D/'u').iterdir()):
 dst=upload/'u'/p.name;dst.parent.mkdir(exist_ok=True);os.link(p,dst);records.append(record(dst,'u/'+p.name,'add'))
outside=[]
for n in ('jd.sh','dbb2.py'):
 r=record(L/'out'/n,n,'replace' if n=='jd.sh' else 'add');r['destination']='/project/community/jjyeung/okh7/x_22c714e1/'+n;outside.append(r)
up=dict(schema='build24m4c-upload-diff-v1',baseline='24m2d (uploaded base)',workspace_base='24m3',
 baseline_inventory='work/build24m3/BASELINE.json',baseline_inventory_sha256=J.sha(L/'work/build24m3/BASELINE.json'),
 baseline_delivery_sha256=J.sha(B/'out/DELIVERY_24M2D.json'),stream_root=str(upload),top_directories=['q','n','qd','u'],
 files=records,total_files=len(records),total_bytes=sum(r['bytes'] for r in records),kits={n:seals[n] for n in ('q','n','qd')},GO=False,n_go_upload_authorized=False,outside_kit_files=outside)
J.write(L/'out/UPLOADS_24M4C.json',up);(L/'out/UPLOADS_24M4C.list').write_text(''.join(r['name']+'\n' for r in records))
go=[]
for p in sorted(kit('n_go').rglob('*')):
 if p.is_file():
  rel=p.relative_to(kit('n_go'))
  if J.sha(p)!=J.sha(kit('n')/rel):go.append(record(p,'n/'+str(rel),'replace'))
assert {r['name'] for r in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4C_GO.json',dict(schema='build24m4c-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(r['bytes'] for r in go),upload_authorized=False))
card=f'''Vehicle N uses MINIMAL. q, n and qd have GO=false; only the unuploaded n_go template has GO=true.
Tree C is {tree}, with 944 files matching TREE24L4_SEAL.json and UNCHANGED24L4.json.
Kit q: {seals['q']}; kit n: {seals['n']}.
Kit n_go: {seals['n_go']}; kit qd: {seals['qd']}.
UPLOADS_24M4C.json diffs against uploaded 24m2d; the workspace base is 24m3. It contains {len(records)} files and {up['total_bytes']} bytes under q/, n/, qd/ and u/ at {upload}.
UPLOADS_24M4C_GO.json is the separate three-file n-to-n_go delta and is not authorized for upload. jd.sh and dbb2.py destinations appear in outside_kit_files.
The pointing hash {POINTING_K1_REMOVE} binds 320 keys as a plain constant pin at entry 12, after the first 11 pins and before NAMING_REMOVE, making 13 lists. remove_files and launch22.removal_order agree; all eight capsules pass tree C's native validator.
Supplied production expectations are 25,020 pointing source rows, 320 removed keys, 6,584 scene exclusions, 18,116 admissions before target-shape filtering and zero K1 held-out admissions. Production counts were not scanned.
P's step-400 export initializes a fresh optimizer and counter. routing_opener_init=keep, step-544 lineage, MINIMAL routing, two NOT_PRESENT slots and seven DEFERRED slots remain pinned. No tower-scale freeze is added.
The planner authenticates inputs by SHA256. Mode r reconstructs P's routing database; mode q uses the authenticated selected base, with native substitution recorded in host.json.
Missing runtime catalog eac5f9f0 refuses R1_STAGED_PIN_MISSING before preparation. The hidden-path fixtures reach that named boundary in r and q for all four kits; production catalog availability is unproven.
Native in-job functions regenerate pool, room-audit, scene-rebuild, target-filter and preparation receipts. The scene step calls r2_scene_bindings.rebuild and native verify unchanged, publishing live/s0.json and s1.json.
The final census reads every native admitted Rows selection, including indexed streams and pose mixtures. It uses Rooms.status/room, the native VQA Binding.room fallback and Withheld; no kit function filters rows.
Per stream it counts benchmark, dev, R0, withheld-80, K1 held-out, official, admitted and unresolved rows. Pointing checks both canonical resolutions. live/c0.json through c3.json hold every protected row's sorted native keys.
live/c4.json binds counts, config identity, authenticated source/store pins and sorted-key hashes. h.py pins it into live/h0.json; rv.py rechecks both publications and refuses missing, stale or mismatched evidence.
q, n and n_go refuse R1_CENSUS_PROTECTED_ADMITTED:<stream> on admitted protected rows. qd records WOULD_REFUSE and reaches WAITING_REVIEW through actual h.py and rv.py without training or claiming admission.
Tree C accepts constants only. bind_protected.py refuses role-list deltas with R1_ROLE_LIST_REQUIRES_TREE_DELTA before changing a kit; pose or routing lists require an authorized tree delta. The tool's role-list implementation remains for tree R.
The discovery wrapper preserves the 60-second dbb2.py retry loop, capped at 180 attempts. qd requests preempt, one GPU, 48 CPUs, 800G, four hours and no requeue; N requests advanced, four GPUs/ranks, 48 CPUs, 800G and 24 hours.
Independent review retains the 7,200-second bound, 30-second polling and strict identity, ownership and mode checks. Nothing was uploaded or launched.
All four decoded scans and the kit, naming, resolver, guard, live, routing and review-wait suites pass. VALIDATION.json records fixture boundaries; production preparation and admission remain unverified.
'''
(L/'out/N_CARD_KIT_ROWS_24M4C.md').write_text(card)
report=f'''Tree {tree}; q {seals['q']}; n {seals['n']}; n_go {seals['n_go']}; qd {seals['qd']}.
All 944 tree files match the supplied C seal and ledger; archives, inventories, capsules and dependent seals agree.
The 320-key pointing pin binds as a constant before NAMING_REMOVE; all eight config capsules pass C's native validator.
The final census uses native room functions and actual native admitted selections; the kit does not filter rows.
q/n/n_go refuse R1_CENSUS_PROTECTED_ADMITTED:<stream>; qd records WOULD_REFUSE and reaches WAITING_REVIEW in the decoded shell fixture.
h.py and rv.py bind config identity, source/store pins, counts and sorted-key hashes, and reject missing, stale or mismatched evidence.
Native in-job receipt regeneration remains installed; additional pose/routing role lists refuse and require a tree delta.
Four decoded scans, required regression suites, 56 native host tests, 24 census/host cases and hidden-path r/q checks pass; VALIDATION.json records scope.
Expected production boundary: R1_STAGED_PIN_MISSING:eac5f9f0 if the runtime catalog is absent; production admission was not run.
UPLOADS_24M4C.json/.list contain {len(records)} files ({up['total_bytes']} bytes), diffed against uploaded 24m2d; workspace base is 24m3. GO stays false except unuploaded n_go.
Every original file remains byte-identical in place or in attic; no deletion, upload, launch, tree edit or resolver-identity change occurred.
Operational exception: fixture allocation exceeded 150 MB (at least 367,820,800 bytes observed); final retained size appears in DELIVERY_24M4C.json. Completed fixtures are retained losslessly.
'''
(L/'out/BUILD24M4C_REPORT.md').write_text(report)
assert len(report.splitlines())<15
print('Final invariants, validation, card and upload diff PASS',len(records),up['total_bytes'])
