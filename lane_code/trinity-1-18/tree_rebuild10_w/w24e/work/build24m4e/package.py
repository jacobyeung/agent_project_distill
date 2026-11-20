from common import *
import io,tarfile,lzma,datetime
iv=J.load(D/'INVARIANTS.json');validation=J.load(D/'VALIDATION.json');up=J.load(L/'out/UPLOADS_24M4E.json')
assert validation['status']=='PASS'
def growth():
 known=J.load(D/'DISK_BASELINE.json');seen=set();size=0
 for root,dirs,names in os.walk(L):
  dirs[:]=[x for x in dirs if not Path(root,x).is_symlink()]
  for n in dirs+names:
   s=Path(root,n).lstat();key=f'{s.st_dev}:{s.st_ino}'
   if key not in seen:size+=max(0,s.st_blocks-known.get(key,0))*512;seen.add(key)
 return size
selected={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for root in (T,*(kit(n) for n in ('q','n','n_go','qd')),D/'upload',D/'inputs',D/'scanners'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.suffix in ('.py','.sh','.json','.log','.gz') and p.name not in ('PACKAGE_MANIFEST.json','PACKAGE_CHECK.json','STORAGE_FINAL.json','package.log'):add(p)
# Include the unchanged arming helper and all its package-local dependencies.
old=L/'work/build24m4d'
for p in old.iterdir():
 if p.suffix in ('.py','.sh'):add(p)
for root in (old/'scanners',old/'inputs'):
 for p in root.rglob('*'):add(p)
for rel in ('BUILD24M4E_REPORT.md','DELIVERY_24M4D.json','BUILD24M4D_REPORT.md','UPLOADS_24M4E.json','UPLOADS_24M4E.list','UPLOADS_24M4E_GO.json','N_CARD_KIT_ROWS_24M4E.md','ORCHARD_COPIES_24M4E.json','STILL_MISSING_24M4E.md','UPLOADS_24M3.json','UPLOADS_24M4D.json','arm_routing.py','ARM_ROUTING_USAGE.md','jd.sh','dbb2.py','bind_protected.py','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/rel)
for rel in ('work/build24m3/BASELINE.json','work/build24m4c/TREE24L4_SEAL.json','work/build24m4d/ORCHARD_24M3_BASELINE.json','work/build24m4d/PACKAGE_MANIFEST.json'):add(L/rel)
for original in iv['preserved_originals'].values():add(L/original)
for n in ('q','n'):
 for p in (D/('guard_'+n)).glob('*.json'):add(p)
for root in (D/'resolver',D/'proofs/resolver600_v2',D/'proofs/resolver23'):
 for p in root.glob('*.json'):add(p)
for rel in ('hidden/run.py','hidden/resolved.json','hidden/boundary.json','hidden/selection.json','arming_final/base.json','arming_final/db_bytes.json','arming_final/routing_selection.json','arming_final/workspace/out/armed/UPLOADS_ROUTING_ARMED.json','arming_final/workspace/out/armed/PLANNER_CLOSURE.json'):add(D/rel)
# Every current production byte and mode is sealed; fixture payload bodies are
# intentionally omitted, with read-only dependencies recorded in VALIDATION.
rawfiles={n:(p.read_bytes(),p.stat().st_mode&511) for n,p in sorted(selected.items())}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,'04o')) for n,(raw,mode) in rawfiles.items()}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest();target=L/'out'/('tree_rebuild_b24m4e_'+seal[:8]+'.tar')
assert not target.exists()
base=J.load(L/'out/DELIVERY_24M4D.json');hidden=J.load(D/'HIDDEN_PATH_TESTS.json')
inner=dict(schema='build24m4e-delivery-v1',status='PASS',package=str(target.relative_to(L)),package_seal=seal,tree_sha256=iv['tree_sha256'],tree_files=iv['tree_files'],kits=iv['kits'],
 base=dict(build='24m4d',package=base['package'],package_seal=base['package_seal'],base_archive_in_fresh_untar=False,embedded_delivery_sha256=J.sha(L/'out/DELIVERY_24M4D.json')),
 catalog=J.load(D/'PINS.json')['pins'][0],additional_orchard_copies=[],orchard_copies_manifest='out/ORCHARD_COPIES_24M4E.json',still_missing_manifest='out/STILL_MISSING_24M4E.md',
 next_mode_r_fixture_refusal=hidden['records'][0]['refusal'],next_boundary=hidden['next_boundary'],
 uploaded_diff_base=up['baseline'],uploaded=False,launched=False,uploads=dict(manifest='out/UPLOADS_24M4E.json',list='out/UPLOADS_24M4E.list',GO_manifest='out/UPLOADS_24M4E_GO.json',stream_root=up['stream_root'],files=up['total_files'],bytes=up['total_bytes'],already_present=up['already_present']),
 checks='PASS',validation='work/build24m4e/VALIDATION.json',fixture_boundaries=validation['fixture_boundaries'],inherited_only=validation['inherited_only'],unchanged=iv['unchanged'],
 GO=False,GO_template='out/kit_n_go',GO_template_upload_authorized=False,armed_copies_GO=False,production_admission='NOT_RUN',production_body_availability='NOT_VERIFIED',
 original_files_verified=iv['original_files_verified'],original_kit_bytes_and_modes_preserved=True,no_deletions=True,disk_cap_bytes=150000000,archive_compression='xz; tar auto-detects compression despite .tar suffix',
 archive_hash_record='External delivery adds archive SHA256, byte count and verified member count; embedded delivery precedes archive hashing')
record=dict(schema='build24m4e-manifest-v1',package_seal=seal,files=manifest,seal_domain='files only; package manifest and delivery excluded')
rawfiles['work/build24m4e/PACKAGE_MANIFEST.json']=((json.dumps(record,sort_keys=True,indent=2)+'\n').encode(),0o644)
rawfiles['out/DELIVERY_24M4E.json']=((json.dumps(inner,sort_keys=True,indent=2)+'\n').encode(),0o644)
buf=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(buf,'wb',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as tar:
 for n,(raw,mode) in sorted(rawfiles.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(n);info.mode=mode;key=(h,mode);expected[n]=dict(sha256=h,mode=mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];tar.addfile(info)
  else:seen[key]=n;info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
packed=buf.getvalue();before=growth();print('Disk before package',before,'package bytes',len(packed),flush=True)
assert before+len(packed)+1_000_000<150000000,(before,len(packed))
with tarfile.open(fileobj=io.BytesIO(packed)) as tar:
 actual={m.name:dict(sha256=hashlib.sha256(tar.extractfile(m).read()).hexdigest(),mode=m.mode) for m in tar}
assert actual==expected
for n,h in iv['kits'].items():assert J.seal(kit(n))==h
with target.open('xb') as f:f.write(packed)
J.write(D/'PACKAGE_MANIFEST.json',record)
storage=dict(new_allocated_bytes=growth(),conservative_upper_bound_bytes=growth()+500000,cap_bytes=150000000,cap_met=True,transient_cap_met=True)
assert storage['conservative_upper_bound_bytes']<150000000
J.write(D/'STORAGE_FINAL.json',storage)
delivery=dict(inner,sha256=hashlib.sha256(packed).hexdigest(),bytes=len(packed),verified_members=len(expected),storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/'out/DELIVERY_24M4E.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',members=len(expected),all_member_bytes_and_modes_verified=True,delivery_embedded=True,sha256=delivery['sha256'],bytes=len(packed),kit_seals=iv['kits']))
print(json.dumps(dict(package=delivery['package'],sha256=delivery['sha256'],bytes=len(packed),members=len(expected),storage=storage),indent=2),flush=True)
