from common import *
from storage import growth
import io,tarfile,lzma,gzip,datetime

iv=J.load(D/'INVARIANTS.json');validation=J.load(D/'VALIDATION.json');assert validation['status']=='PASS'
selected={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for root in [T,D/'upload',*(kit(n) for n in ('q','n','n_go','qd'))]:
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.suffix in ('.py','.sh','.json','.log','.gz') and p.name not in ('PACKAGE_MANIFEST.json','PACKAGE_CHECK.json','STORAGE_FINAL.json','package_run.log','package_final.log'):add(p)
for check in validation['checks'].values():add(L/check['path'])
for name in ('q','n','n_go','qd'):
 add(D/'scanners'/name/'environment_shell21g.json')
 scan=J.load(D/('SCAN_'+name+'.json'));raw=gzip.decompress((D/('SCAN_'+name+'.json.gz')).read_bytes())
 assert hashlib.sha256(raw).hexdigest()==scan['uncompressed_sha256'] and scan['kit_seal']==iv['kits'][name]
for name in ('UPLOADS_24M4C.json','UPLOADS_24M4C.list','UPLOADS_24M4C_GO.json','N_CARD_KIT_ROWS_24M4C.md','BUILD24M4C_REPORT.md','bind_protected.py','jd.sh','dbb2.py','TREE_SEAL.json','TREE_FILES.sha256','DELIVERY_24M3.json','BUILD24M3_REPORT.md','MISSING_STAGED_PINS.md','SCENE_REBUILD_INPUTS.md'):
 add(L/'out'/name)
add(L/'work/build24m3/BASELINE.json')
retention=J.load(D/'RETENTION_STORE.json')
assert J.sha(L/retention['container'])==retention['container_sha256']
with tarfile.open(L/retention['container']) as retained:
 assert hashlib.sha256(retained.extractfile(retention['archive']).read()).hexdigest()==retention['archive_sha256']
files={n:(p.read_bytes(),p.stat().st_mode&511) for n,p in sorted(selected.items())}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,'04o')) for n,(raw,mode) in files.items()}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=L/'out'/('tree_rebuild_b24m4c_'+seal[:8]+'.tar')
up=J.load(L/'out/UPLOADS_24M4C.json');base=J.load(L/'out/DELIVERY_24M3.json')
inner=dict(schema='build24m4c-delivery-v1',status='PACKAGED_WITH_OPERATIONAL_EXCEPTIONS',checks='PASS',package=str(target.relative_to(L)),package_seal=seal,
 tree_sha256=iv['tree_sha256'],tree_files=944,kits=iv['kits'],GO=False,GO_template_upload_authorized=False,
 workspace_base=dict(build='24m3',package=base['package'],sha256=base.get('sha256'),delivery_sha256=J.sha(L/'out/DELIVERY_24M3.json')),
 uploaded_diff_base='24m2d',uploads=dict(manifest='out/UPLOADS_24M4C.json',list='out/UPLOADS_24M4C.list',GO_manifest='out/UPLOADS_24M4C_GO.json',stream_root=up['stream_root'],files=up['total_files'],bytes=up['total_bytes'],outside_kit_files=up['outside_kit_files']),
 pointing=dict(sha256='d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1',keys=320,binding='constant',entry=12,total_lists=13,order='REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE)',native_validator='PASS for eight capsules'),
 census=dict(native_functions=['r1_rooms.Rooms.status','r1_rooms.Rooms.room','r1_direction_twins.Binding.room','r2_withheld.Withheld'],population='Actual native admitted Rows selections; no kit filtering',receipt='live/c4.json',protected_keys=['live/c0.json','live/c1.json','live/c2.json','live/c3.json'],host='live/h0.json',refusal='R1_CENSUS_PROTECTED_ADMITTED:<stream>',qd='WOULD_REFUSE then WAITING_REVIEW',config_identity_source_store_counts_and_key_hashes_bound=True),
 native_receipt_regeneration='In-job pool, room audit, scene rebuild, target filter and preparation functions unchanged',
 role_delta=dict(status='REFUSED_ON_TREE_C',tool='out/bind_protected.py',refusal='R1_ROLE_LIST_REQUIRES_TREE_DELTA',requirement='Additional pose/routing constants require an authorized tree delta; role tool is for tree R'),
 expected_first_production_refusal='R1_STAGED_PIN_MISSING:eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9 if the authenticated runtime catalog is absent',
 production_admission='NOT_RUN',fixture_boundaries=validation['boundaries'],operational_exceptions=validation['operational_exceptions'],
 disk_cap_bytes=150000000,transient_disk_cap_met=False,observed_growth_at_least_bytes=367820800,original_files_preserved=True,no_deletions=True,
 fixture_retention=dict(manifest='work/build24m4c/RETENTION_STORE.json',container=retention['container'],container_sha256=retention['container_sha256'],member=retention['archive'],sha256=retention['archive_sha256'],lossless=True,embedded_in_final_package=False),
 archive_compression='xz; tar readers auto-detect compression despite .tar suffix',archive_sha256_record='External delivery adds final archive hash, byte count and final allocation; embedded delivery precedes hashing')
record=dict(schema='build24m4c-manifest-v1',package_seal=seal,files=manifest,seal_domain='files only; manifest and delivery excluded')
files['work/build24m4c/PACKAGE_MANIFEST.json']=((json.dumps(record,sort_keys=True,indent=2)+'\n').encode(),0o644)
files['out/DELIVERY_24M4C.json']=((json.dumps(inner,sort_keys=True,indent=2)+'\n').encode(),0o644)
buffer=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(buffer,'wb',preset=6) as xz,tarfile.open(fileobj=xz,mode='w|') as tar:
 for name,(raw,mode) in sorted(files.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(name);info.mode=mode;expected[name]=dict(sha256=h,mode=mode);key=(h,mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];tar.addfile(info)
  else:seen[key]=name;info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
packed=buffer.getvalue();before=growth()
assert before+len(packed)+1048576<150000000,(before,len(packed))
with tarfile.open(fileobj=io.BytesIO(packed)) as tar:
 actual={m.name:dict(sha256=hashlib.sha256(tar.extractfile(m).read()).hexdigest(),mode=m.mode) for m in tar}
assert actual==expected
for n,h in iv['kits'].items():assert J.seal(kit(n))==h
with target.open('xb') as f:f.write(packed)
J.write(D/'PACKAGE_MANIFEST.json',record)
final=growth()+1048576;assert final<150000000,final
storage=dict(final_allocated_upper_bound_bytes=final,cap_bytes=150000000,final_cap_met=True,transient_cap_met=False,observed_growth_at_least_bytes=367820800,no_deletions=True,lossless_retention=True)
J.write(D/'STORAGE_FINAL.json',storage)
delivery=dict(inner,sha256=hashlib.sha256(packed).hexdigest(),bytes=len(packed),verified_members=len(expected),storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/'out/DELIVERY_24M4C.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',members=len(expected),all_member_bytes_and_modes_verified=True,delivery_embedded=True,sha256=delivery['sha256'],bytes=len(packed),kit_seals=iv['kits']))
print(json.dumps(dict(package=str(target.relative_to(L)),sha256=delivery['sha256'],bytes=len(packed),members=len(expected),storage=storage),indent=2))
