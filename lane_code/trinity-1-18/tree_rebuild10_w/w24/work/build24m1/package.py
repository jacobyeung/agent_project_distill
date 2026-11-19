"""Package the kit overlay and evidence, preserving every prior package."""
from pathlib import Path
import datetime,gzip,hashlib,io,json,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
assert J.load(D/'INVARIANTS.json')['status']=='PASS'
assert J.load(D/'VALIDATION.json')['status']=='PASS'
assert J.load(D/'STORAGE.json')['final_under_200_MB']
selected={}
def add(p):
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for k in (L/'work/build24/kits/q',L/'work/build24/kits/n',L/'out/kit_n_go'):
 for p in k.rglob('*'):add(p)
for root in (D/'upload',D/'scanners',D/'retained_evidence',D/'regressions'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and p.name not in ('PACKAGE_MANIFEST.json','PACKAGE_CHECK.json','package.log'):
  add(p)
for root in ('guard_q','guard_n'):
 for p in (D/root).glob('*.json'):add(p)
for name in ('UPLOADS_24M1.json','UPLOADS_24M1.list','UPLOADS_24M1_GO.json','N_CARD_KIT_ROWS.md','BUILD24M1_REPORT.md','jr.sh','TREE_SEAL.json','TREE_FILES.sha256','arm_routing.py'):
 add(L/'out'/name)
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p),mode=format(p.stat().st_mode&511,'04o')) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=L/'out'/('tree_rebuild_b24m1_'+seal[:8]+'.tar');base=J.load(L/'out/DELIVERY_24K.json');invariants=J.load(D/'INVARIANTS.json');up=J.load(L/'out/UPLOADS_24M1.json')
inner=dict(schema='build24m1-overlay-v1',status='PACKAGED_BLOCKED_WITH_OPERATIONAL_EXCEPTION',package=str(target.relative_to(L)),package_seal=seal,base=dict(path=base['package'],sha256=base['sha256']),tree_sha256=invariants['tree_sha256'],kits=invariants['kits'],GO=False,GO_template_upload_authorized=False,checks='PASS',production_admission='BLOCKED',transient_disk_cap_met=False,final_retained_allocated_bytes=J.load(D/'STORAGE.json')['retained_allocated_bytes'],uploads=dict(files=up['total_files'],bytes=up['total_bytes'],stream_root=up['stream_root']),archive_sha256_record='The external out/DELIVERY_24M1.json adds the final archive SHA256 and byte count; this embedded record precedes archive hashing.')
record=dict(schema='build24m1-manifest-v1',package_seal=seal,files=manifest,base=inner['base'],tree_sha256=invariants['tree_sha256'],kits=invariants['kits'],fixtures='Retained workspace inputs are referenced by path; fixture payloads and lossless local retention blobs are excluded.',manifest_seal_domain='files only; embedded delivery and this manifest are archive metadata')
J.write(D/'PACKAGE_MANIFEST.json',record);add(D/'PACKAGE_MANIFEST.json')
embedded=(json.dumps(inner,sort_keys=True,indent=2)+'\n').encode()
seen={};expected={}
with target.open('xb') as output,gzip.GzipFile(filename='',fileobj=output,mode='wb',mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
 for name in [*sorted(selected),'out/DELIVERY_24M1.json']:
  p=selected.get(name);raw=p.read_bytes() if p else embedded
  h=hashlib.sha256(raw).hexdigest();mode=(p.stat().st_mode&511) if p else 0o644
  info=tarfile.TarInfo(name);info.mode=mode;key=(h,mode);expected[name]=dict(sha256=h,mode=mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];archive.addfile(info)
  else:seen[key]=name;info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
with tarfile.open(target) as archive:
 actual={m.name:dict(sha256=hashlib.sha256(archive.extractfile(m).read()).hexdigest(),mode=m.mode) for m in archive}
 assert actual==expected
 for name,value in actual.items():
  if any(name.startswith(prefix) for prefix in ('out/kit_n_go/','work/build24/kits/q/','work/build24/kits/n/')) and (name.endswith('/job.sh') or '/b/' in name and name.endswith('.sh')):assert value['mode']==0o755,name
delivery=dict(inner,sha256=J.sha(target),bytes=target.stat().st_size,verified_members=len(expected),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_packages_unchanged=len(J.load(D/'BASELINE.json')['packages']))
J.write(L/'out/DELIVERY_24M1.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',sha256=delivery['sha256'],bytes=delivery['bytes'],members=len(expected),all_member_bytes_and_modes_verified=True,delivery_embedded=True))
print(json.dumps(delivery,indent=2))
