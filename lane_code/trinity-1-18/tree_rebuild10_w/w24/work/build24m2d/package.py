from common import *
from storage import growth
from restore_scans import expand
import io,tarfile,gzip,lzma,difflib,datetime
iv=J.load(D/'INVARIANTS.json');assert J.load(D/'VALIDATION.json')['status']=='PASS'
selected={};virtual={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in ('q','n','n_go','qd'):
 for p in kit(name).rglob('*'):add(p)
for p in (D/'upload').rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and p.suffix in ('.py','.json','.sh') and p.name not in {'BASELINE.json','COMPRESSION_PLAN.json','package.py','install.py','hidden.py','hidden_continue.py','planner_test.py','planner_selection_test.py','run_suites.py','run_extra.py'} and not p.name.startswith('naming24m1_'):add(p)
for p in (D/'scanners').rglob('environment_shell21g.json'):add(p)
for name in ('UPLOADS_24M2D.json','UPLOADS_24M2D.list','UPLOADS_24M2D_GO.json','BUILD24M2D_REPORT.md','N_CARD_KIT_ROWS.md','MISSING_STAGED_PINS.md','SCENE_REBUILD_INPUTS.md','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/name)
scans={n:json.loads(gzip.decompress((D/('SCAN_'+n+'.json.gz')).read_bytes())) for n in ('q','n','n_go','qd')}
bundle=dict(schema='lossless-scan-bundle-v1',base=scans['q'],deltas={},sha256={n:J.load(D/('SCAN_'+n+'.json'))['uncompressed_sha256'] for n in scans})
for n in ('n','n_go','qd'):
 changes={}
 for key,value in scans[n].items():
  before=scans['q'][key]
  if value==before:continue
  if isinstance(value,list) and isinstance(before,list) and len(value)>100:
   aa=[json.dumps(v,sort_keys=True) for v in before];bb=[json.dumps(v,sort_keys=True) for v in value];steps=[]
   for tag,i,j,a,b in difflib.SequenceMatcher(a=aa,b=bb,autojunk=True).get_opcodes():
    if tag=='equal':steps.append(dict(copy=[i,j-i]))
    elif tag in ('insert','replace'):steps.append(dict(insert=value[a:b]))
   changes[key]=dict(sequence=steps)
  else:changes[key]=dict(replace=value)
 bundle['deltas'][n]=changes
for n in scans:assert json.loads(expand(bundle,n))==scans[n]
virtual['work/build24m2d/SCAN_BUNDLE.json']=(json.dumps(bundle,sort_keys=True).encode(),0o644)
files={n:(p.read_bytes(),p.stat().st_mode&511) for n,p in selected.items()};files.update(virtual)
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,'04o')) for n,(raw,mode) in sorted(files.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest();target=L/'out'/('tree_rebuild_b24m2d_'+seal[:8]+'.tar')
up=J.load(L/'out/UPLOADS_24M2D.json');base=J.load(L/'out/DELIVERY_24M2.json')
inner=dict(schema='build24m2d-overlay-v1',status='PACKAGED_BLOCKED_WITH_OPERATIONAL_EXCEPTION',package=str(target.relative_to(L)),package_seal=seal,base=dict(path=base['package'],sha256=base['sha256']),tree_sha256=iv['tree_sha256'],kits=iv['kits'],GO=False,GO_template_upload_authorized=False,checks='PASS',production_admission='BLOCKED',expected_first_discovery_refusal='If e00 lacks eac5f9f0: R1_STAGED_PIN_MISSING:<full catalog hash>:P.materialization.inputs.catalog.<hash>, before preparation; otherwise native reconstruction must reproduce the full pinned database SHA256 before downstream gates.',scene_rebuild=dict(installed=False,conditionally_buildable=True,condition='Selected camera/routing population equals its source receipt database pin and authenticates in-job; all other inputs resolve, including runtime catalog'),uploads=dict(files=up['total_files'],bytes=up['total_bytes'],stream_root=up['stream_root']),prior_packages_unchanged=iv['prior_packages_unchanged'],disk_cap_bytes=100000000,transient_disk_cap_met=False,storage_exception=dict(observed_allocated_bytes=146644992,lossless_retention=['work/build24m2d/RETENTION.json','work/build24m2d/RETENTION_XZ.json'],files_deleted=0),archive_compression='xz; tarfile and GNU tar detect it despite .tar suffix',scan_reports='work/build24m2d/SCAN_BUNDLE.json; restore_scans.py reconstructs and SHA256-verifies all four reports',archive_sha256_record='External delivery adds final archive SHA256, byte count and storage; embedded metadata precedes hashing.',fixture_boundaries=J.load(D/'VALIDATION.json')['boundaries'])
record=dict(schema='build24m2d-manifest-v1',package_seal=seal,files=manifest,manifest_seal_domain='files only; manifest and embedded delivery excluded',base=inner['base'])
files['work/build24m2d/PACKAGE_MANIFEST.json']=((json.dumps(record,sort_keys=True,indent=2)+'\n').encode(),0o644)
files['out/DELIVERY_24M2D.json']=((json.dumps(inner,sort_keys=True,indent=2)+'\n').encode(),0o644)
output=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(output,mode='wb',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
 for name,(raw,mode) in sorted(files.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(name);info.mode=mode;expected[name]=dict(sha256=h,mode=mode);key=(h,mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];archive.addfile(info)
  else:seen[key]=name;info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
raw=output.getvalue();before=growth();assert before+len(raw)+400000<100000000,(before,len(raw))
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
 actual={m.name:dict(sha256=hashlib.sha256(archive.extractfile(m).read()).hexdigest(),mode=m.mode) for m in archive}
assert actual==expected
for p,h in J.load(D/'PRIOR_PACKAGES.json').items():assert J.sha(p)==h
with target.open('xb') as f:f.write(raw)
J.write(D/'PACKAGE_MANIFEST.json',record)
delivery=dict(inner,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),verified_members=len(expected),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/'out/DELIVERY_24M2D.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',members=len(expected),sha256=delivery['sha256'],bytes=len(raw),all_member_bytes_and_modes_verified=True,delivery_embedded=True,scan_bundle_lossless=True,prior_packages_unchanged=True))
final=growth()+16384;assert final<100000000,final
J.write(D/'STORAGE_FINAL.json',dict(status='FINAL_UNDER_CAP_TRANSIENT_OVERRUN',final_allocated_upper_bound_bytes=final,cap_bytes=100000000,transient_cap_met=False,observed_transient_allocated_bytes=146644992,no_deletions=True,method='Distinct inode block growth including directories relative to pre-edit baseline, plus 16 KiB reserve for final metadata. Every retained fixture compression is lossless.'))
delivery.update(final_retained_allocated_upper_bound_bytes=final,final_storage_record='work/build24m2d/STORAGE_FINAL.json');J.write(L/'out/DELIVERY_24M2D.json',delivery)
print(json.dumps(delivery,indent=2))
