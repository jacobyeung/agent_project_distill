from common import *
from storage import growth
import io,tarfile,lzma,gzip,datetime
iv=J.load(D/'INVARIANTS.json');validation=J.load(D/'VALIDATION.json');assert validation['status']=='PASS'
selected={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in ('q','n','n_go','qd'):
 for p in kit(name).rglob('*'):add(p)
for p in (D/'upload').rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and (p.suffix in ('.py','.json','.log','.patch','.md','.sh','.gz') or p.name.startswith('t_')):
  if p.name not in ('DISK_BASELINE.json.gz','PACKAGE_MANIFEST.json','PACKAGE_CHECK.json','STORAGE_FINAL.json'):add(p)
for name in ('q','n','n_go','qd'):
 add(D/'scanners'/name/'environment_shell21g.json')
 raw=gzip.decompress((D/('SCAN_'+name+'.json.gz')).read_bytes());v=J.load(D/('SCAN_'+name+'.json'))
 assert hashlib.sha256(raw).hexdigest()==v['uncompressed_sha256'] and json.loads(raw)['kit_seal']==iv['kits'][name]
for folder in ('guard_q','guard_n'):
 for p in (D/folder).glob('*.json'):add(p)
for filename in ('RETENTION.json','RETENTION_REPORTS.json','RETENTION_COMPLETE.json','RETENTION_ATTIC.json'):
 for row in J.load(D/filename)['records']:
  retained=L/row['retained'];raw=retained.read_bytes();encoding=row.get('encoding','gzip')
  if encoding=='sha256-reference':
   ref=json.loads(raw);target=L/ref['path'];decoded=target.read_bytes();assert J.sha(target)==ref['sha256'];add(target)
  else:decoded=lzma.decompress(raw) if encoding=='xz' else gzip.decompress(raw)
  assert hashlib.sha256(decoded).hexdigest()==row['original_sha256'] and len(decoded)==row['bytes']
  add(retained)
for name in ('UPLOADS_24M4.json','UPLOADS_24M4.list','UPLOADS_24M4_GO.json','BUILD24M4_REPORT.md','N_CARD_KIT_ROWS.md','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/name)
files={n:(p.read_bytes(),p.stat().st_mode&511) for n,p in sorted(selected.items())}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,'04o')) for n,(raw,mode) in files.items()}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=L/'out'/('tree_rebuild_b24m4_'+seal[:8]+'.tar');assert not target.exists()
base=J.load(L/'out/DELIVERY_24M3.json');up=J.load(L/'out/UPLOADS_24M4.json')
inner=dict(schema='build24m4-overlay-v1',status='PACKAGED_WITH_STORAGE_LIMIT_BREACH',package=str(target.relative_to(L)),package_seal=seal,
 base=dict(path=base['package'],sha256=base['sha256']),tree_sha256=iv['tree_sha256'],tree_files=iv['tree_files'],kits=iv['kits'],checks='PASS',GO=False,GO_template_upload_authorized=False,production_admission='NOT_RUN',
 changes='Exact 24l4r to 24l4t tree patch, source archives/inventories, code capsules and dependent seals only; runtime helpers and config semantics unchanged.',
 census=dict(cases=40,noncanonical_pointing='R1_PROTECTED_ROOM_ROWS:pointing',unresolved_pointing='R1_PROTECTED_ROOM_UNRESOLVED:pointing',qd='WOULD_REFUSE; both cases reach WAITING_REVIEW through actual h.py/rv.py',vqa='Native Binding.room constructor and aliases exercised through all four kits',input_extension_required=False),
 expected_first_discovery_refusal=base['expected_first_discovery_refusal'],scene_rebuild=base['scene_rebuild'],receipts=base['receipts'],pointing=base['pointing'],discovery=base['discovery'],
 pose_cleanup=dict(status='BLOCKED_IF_PROTECTED_POSE_ROWS_REMAIN',blocker='out/REMOVAL_RECEIPTS_BLOCKER.md',reason='The tree supplies no native arbitrary protected-pose materialization producer.'),
 uploads=dict(files=up['total_files'],bytes=up['total_bytes'],stream_root=up['stream_root'],manifest='out/UPLOADS_24M4.json',list='out/UPLOADS_24M4.list',GO_manifest='out/UPLOADS_24M4_GO.json',outside_kit_files=[]),
 prior_packages_unchanged=True,prior_package_count=iv['prior_package_count'],storage=dict(cap_bytes=100000000,compliance='FAIL',observed_growth_bytes_at_least=141709312,peak_continuously_measured=False,reason='Resolver fixture archive copies exceeded the cap. Completed evidence was subsequently compacted losslessly.',final_record='work/build24m4/STORAGE_FINAL.json'),
 archive_compression='xz; tarfile auto-detects it despite the .tar suffix',archive_sha256_record='External delivery adds final archive hash and bytes; embedded delivery precedes archive hashing.',
 retained_fixture_evidence='Verified gzip/xz files or exact-SHA references, with RETENTION manifests; original bytes reconstruct without loss. No file-deletion command ran.',
 fixture_boundaries=validation['boundaries'],validation='work/build24m4/VALIDATION.json')
record=dict(schema='build24m4-manifest-v1',package_seal=seal,files=manifest,manifest_seal_domain='files only; embedded manifest and delivery excluded',base=inner['base'])
files['work/build24m4/PACKAGE_MANIFEST.json']=((json.dumps(record,sort_keys=True,indent=2)+'\n').encode(),0o644)
files['out/DELIVERY_24M4.json']=((json.dumps(inner,sort_keys=True,indent=2)+'\n').encode(),0o644)
buffer=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(buffer,mode='wb',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
 for name,(raw,mode) in sorted(files.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(name);info.mode=mode;expected[name]=dict(sha256=h,mode=mode);key=(h,mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];archive.addfile(info)
  else:seen[key]=name;info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
raw=buffer.getvalue();before=growth();print('Archive bytes',len(raw),'retained growth before write',before,flush=True)
assert before+len(raw)+1048576<100000000,(before,len(raw))
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
 actual={m.name:dict(sha256=hashlib.sha256(archive.extractfile(m).read()).hexdigest(),mode=m.mode) for m in archive}
assert actual==expected
for p,h in J.load(D/'PRIOR_PACKAGES.json').items():assert J.sha(p)==h
for name,h in iv['kits'].items():assert J.seal(kit(name))==h
for rec in up['files']:assert J.sha(rec['local_path'])==rec['sha256']
target.write_bytes(raw)
J.write(D/'PACKAGE_MANIFEST.json',record)
final=growth()+1048576;assert final<100000000
J.write(D/'STORAGE_FINAL.json',dict(status='FINAL_BELOW_CAP_BUT_BUILD_BREACHED',final_allocated_upper_bound_bytes=final,cap_bytes=100000000,observed_growth_bytes_at_least=141709312,compliance='FAIL',early_setup_and_final_metadata_allowance_bytes=1048576,no_file_deletion=True))
external=dict(inner,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),verified_members=len(actual),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),final_retained_allocated_upper_bound_bytes=final)
J.write(L/'out/DELIVERY_24M4.json',external)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',members=len(actual),package_sha256=external['sha256'],package_seal=seal,prior_packages_unchanged=True,final_growth_upper_bound=final))
print(json.dumps(dict(package=str(target.relative_to(L)),sha256=external['sha256'],bytes=len(raw),members=len(actual),final_growth_upper_bound=final),indent=2),flush=True)
