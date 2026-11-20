"""Assemble and verify a bounded overlay in memory before allocating disk."""
from common import *
import datetime,gzip,io,tarfile,difflib,lzma
from storage import growth
from restore_scans import expand
assert J.load(D/'VALIDATION.json')['status']=='PASS'
assert J.load(D/'INVARIANTS.json')['status']=='PASS'
assert J.load(D/'PRIOR_PACKAGES.json')['status']=='PASS'
selected={};virtual={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in ('q','n','n_go','qd'):
 for p in kit(name).rglob('*'):add(p)
for p in (D/'upload').rglob('*'):add(p)
skip={'BASELINE.json','DISK_BASELINE.json','COVERAGE.json','extra.json','staged_inputs.json','tars.json','PIN_AUDIT.json','PACKAGE_MANIFEST.json','PACKAGE_CHECK.json','STORAGE_FINAL.json'}
for p in D.iterdir():
 if p.is_file() and p.name not in skip and p.suffix in ('.py','.json','.sh') and not p.name.startswith('naming24m1_'):add(p)
for p in (D/'scanners').rglob('environment_shell21g.json'):add(p)
for name in ('UPLOADS_24M2.json','UPLOADS_24M2.list','UPLOADS_24M2_GO.json','N_CARD_KIT_ROWS.md','BUILD24M2_REPORT.md','MISSING_STAGED_PINS.md','SCENE_REBUILD_INPUTS.md','POINTING_REMOVAL_BLOCKER.md','jd.sh','jr.sh','TREE_SEAL.json','TREE_FILES.sha256'):
 add(L/'out'/name)
for name in ('TREE24L3_SEAL.json','UNCHANGED24L3.json','HOST24LN3.patch'):
 add(L/'work/build24m2'/name)
add(L/'attic/build24m2c/compressed_fixture/big.json.gz')
donor=L.parent/'work/x24l3_back/out'
for name in ('BUILD24LN_REPORT.md','BUILD24L3_REPORT.md','KIT_WIRING_24LN.md','PIN_COMPARISONS_24N.md'):
 virtual['work/build24m2c/donor/'+name]=((donor/name).read_bytes(),0o644)

# All scan rows survive packaging. Common list spans are stored once so the
# four reports fit alongside the code archive within the user's disk cap.
scans={name:json.loads(gzip.decompress((D/('SCAN_'+name+'.json.gz')).read_bytes())) for name in ('q','n','n_go','qd')}
bundle=dict(schema='lossless-scan-bundle-v1',base=scans['q'],deltas={},sha256={name:J.load(D/('SCAN_'+name+'.json'))['uncompressed_sha256'] for name in scans})
for name in ('n','n_go','qd'):
 changes={}
 for key,value in scans[name].items():
  before=scans['q'][key]
  if value==before:continue
  if isinstance(value,list) and isinstance(before,list) and len(value)>100:
   aa=[json.dumps(v,sort_keys=True) for v in before];bb=[json.dumps(v,sort_keys=True) for v in value]
   steps=[]
   for tag,i,j,a,b in difflib.SequenceMatcher(a=aa,b=bb,autojunk=True).get_opcodes():
    if tag=='equal':steps.append(dict(copy=[i,j-i]))
    elif tag in ('insert','replace'):steps.append(dict(insert=value[a:b]))
   changes[key]=dict(sequence=steps)
  else:changes[key]=dict(replace=value)
 bundle['deltas'][name]=changes
for name in scans:assert json.loads(expand(bundle,name))==scans[name]
virtual['work/build24m2c/SCAN_BUNDLE.json']=(json.dumps(bundle,sort_keys=True).encode(),0o644)

files={name:(p.read_bytes(),p.stat().st_mode&511) for name,p in selected.items()};files.update(virtual)
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,'04o')) for n,(raw,mode) in sorted(files.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=L/'out'/('tree_rebuild_b24m2_'+seal[:8]+'.tar')
base=J.load(L/'out/DELIVERY_24M1.json');iv=J.load(D/'INVARIANTS.json');up=J.load(L/'out/UPLOADS_24M2.json')
before=growth()
inner=dict(schema='build24m2-overlay-v1',build_invocation='24m2c',status='PACKAGED_BLOCKED',package=str(target.relative_to(L)),package_seal=seal,base=dict(path=base['package'],sha256=base['sha256']),tree_sha256=iv['tree_sha256'],kits={k:v['kit_seal'] for k,v in iv['kits'].items()},GO=False,GO_template_upload_authorized=False,checks='PASS',production_admission='BLOCKED',expected_first_discovery_refusal='R1_STAGED_PIN_MISSING:4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84:config.streams.routing.database; before preparation',stopped_items={'2b':'Missing authenticated camera/routing source population','2c':'R1_NAMING_REMOVAL_ORDER: sealed tree rejects thirteenth list'},uploads=dict(files=up['total_files'],bytes=up['total_bytes'],stream_root=up['stream_root']),prior_packages_unchanged=len(J.load(D/'PRIOR_PACKAGES.json')['packages']),disk_cap_bytes=200_000_000,allocated_before_package_bytes=before,scan_reports='work/build24m2c/SCAN_BUNDLE.json; restore_scans.py reconstructs all four full reports and verifies their hashes',fixture_scope=J.load(D/'VALIDATION.json')['boundaries'],archive_sha256_record='The external delivery adds final archive SHA256, byte count and allocation. Embedded metadata precedes archive hashing.')
record=dict(schema='build24m2-manifest-v1',package_seal=seal,files=manifest,base=inner['base'],tree_sha256=iv['tree_sha256'],kits=inner['kits'],manifest_seal_domain='files only; this manifest and embedded delivery are metadata',fixtures='Large fixture payloads remain in the retained workspace and base packages; their recorded boundaries apply.')
inner['archive_compression']='xz; GNU tar and Python tarfile detect compression when opening the .tar file'
inner.update(status='PACKAGED_BLOCKED_WITH_OPERATIONAL_EXCEPTION',transient_disk_cap_met=False,storage_exception=J.load(D/'FIXTURE_RETENTION.json'),directory_accounting='All directory blocks changed since invocation start are counted in full as a conservative upper bound.')
files['work/build24m2c/PACKAGE_MANIFEST.json']=((json.dumps(record,sort_keys=True,indent=2)+'\n').encode(),0o644)
files['out/DELIVERY_24M2.json']=((json.dumps(inner,sort_keys=True,indent=2)+'\n').encode(),0o644)
output=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(output,mode='wb',preset=9) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
 for name,(raw,mode) in sorted(files.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(name);info.mode=mode;expected[name]=dict(sha256=h,mode=mode);key=(h,mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];archive.addfile(info)
  else:seen[key]=name;info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
raw=output.getvalue();print('allocation before',before,'archive bytes',len(raw),'projection',before+len(raw)+180_000,flush=True)
if before+len(raw)+180_000>=200_000_000:
 sizes=[];unique=set()
 for name,(body,mode) in files.items():
  key=(hashlib.sha256(body).hexdigest(),mode)
  if key in unique:continue
  unique.add(key)
  if len(body)>20000:sizes.append((len(gzip.compress(body,mtime=0)),len(body),name))
 print('Largest distinct compressed members:',sorted(sizes,reverse=True)[:18],flush=True)
assert before+len(raw)+180_000<200_000_000,'Package would exceed disk cap; no archive was written'
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
 actual={m.name:dict(sha256=hashlib.sha256(archive.extractfile(m).read()).hexdigest(),mode=m.mode) for m in archive}
assert actual==expected
with target.open('xb') as f:f.write(raw)
J.write(D/'PACKAGE_MANIFEST.json',record)
delivery=dict(inner,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),verified_members=len(expected),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/'out/DELIVERY_24M2.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',sha256=delivery['sha256'],bytes=len(raw),members=len(expected),all_member_bytes_and_modes_verified=True,delivery_embedded=True,full_scans_losslessly_reconstructed=True))
final=growth();assert final+8192<200_000_000
J.write(D/'STORAGE_FINAL.json',dict(status='FINAL_UNDER_CAP_TRANSIENT_OVERRUN',allocated_new_bytes=final+8192,cap_bytes=200_000_000,under_cap=True,transient_disk_cap_met=False,scope='New allocated bytes during this 24m2c invocation; baseline includes retained earlier attempts.',accounting='Distinct inode file-block growth plus full blocks of every changed directory; hard links counted once; conservative 8192-byte reserve for this record and delivery update.',no_deletions=True,lossless_fixture_retention='work/build24m2c/FIXTURE_RETENTION.json'))
delivery.update(final_retained_allocated_bytes=final+8192,final_storage_record='work/build24m2c/STORAGE_FINAL.json')
J.write(L/'out/DELIVERY_24M2.json',delivery)
print(json.dumps(delivery,indent=2))
