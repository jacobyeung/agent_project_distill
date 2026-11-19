from pathlib import Path
import datetime,gzip,hashlib,json,shutil,subprocess,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24c';T=L/'work/tree_r1'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
start=4372639901
size=lambda:int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
subprocess.run(['date','-u'],check=True)
assert size()-start<290_000_000
assert shutil.disk_usage('/scratch').free>85*(1<<30)
assert J.load(D/'TEST_COUNTS.json')['successful']
assert {str(p.relative_to(T)):J.sha(p) for p in T.rglob('*') if p.is_file()}==J.load(L/'work/build24b/TREE_FILES.json')
kits=J.load(D/'KIT.json')
for name in ('q','n'):
 assert J.seal(L/'work/build24/kits'/name)==kits[name]['kit_seal']
 assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==kits[name]['kit_seal']
 assert J.load(D/('LOOKAHEAD_'+name+'.json'))['kit_seal']==kits[name]['kit_seal']
base=L/'out/tree_rebuild_b24b_7d7a8858.tar'
assert J.sha(base)=='4bfb9f759f505276cc908be8885942822edb53b7c048adda0e6ae1c171366f01'
selected={}
def add(p):
 p=Path(p)
 assert p.is_file() and not p.is_symlink(),p
 selected[str(p.relative_to(L))]=p
for root in (T,L/'work/build24/kits',L/'attic/build24c/kit_q',L/'attic/build24c/kit_n'):
 for p in root.rglob('*'):
  if p.is_file():add(p)
for p in D.iterdir():
 if p.is_file() and p.name not in ('PACKAGE_MANIFEST.json','DELIVERY.json','package.log','INSPECT.txt') and p.suffix in ('.py','.json','.log','.sh','.diff'):add(p)
for folder in ('scanners','results','guard_q','guard_n','upload'):
 for p in (D/folder).rglob('*'):
  if p.is_file():add(p)
for name in ('q','n'):
 root=D/'sequence'/name
 add(root/'fixture.py');add(root/'operator/shell.log')
 node=root/'q_22c714e1_20'
 for label in ('tail.sh','tail.stdout','tail.stderr','guard.py','q.log','rooms.log','rooms.json','args.json','p/q/RESULT.json','o/RESULT.json','o/o.tar'):
  p=node/label
  if p.is_file():add(p)
for name in J.load(D/'CHANGES.json')['generators']+['work/build24/kit.py','work/build24/joblib.py']:
 add(L/name)
 p=L/'attic/build24c'/name
 if p.is_file():add(p)
for name in ('UPLOADS_24C.json','UPLOADS_24C.list','OPERATOR_24C.md','TREE_SEAL.json'):add(L/'out'/name)
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
value=dict(schema='build24c-kit-overlay-v1',GO=False,package_seal=seal,base=dict(package=base.name,bytes=base.stat().st_size,sha256=J.sha(base)),tree_sha256=kits['q']['tree_seal'],kits=kits,files=manifest,
 included=['Complete final deployable q/n kits and unchanged source tree','External generator changes and byte-identical generator regression','Before/after evidence, scans, guard/naming/resolver tests and own-config CPU look-ahead','Complete 24c upload stream'],
 inherited_from_base=['Unchanged fixture prerequisites and historical test harnesses; extract the base package before this overlay'],
 omitted=['Generated source copies and temporary fixture stores','Production GPU execution and data','BUILD24C_REPORT.md and DELIVERY_24C.json remain external to avoid a checksum cycle'])
J.write(D/'PACKAGE_MANIFEST.json',value);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24c_'+seal[:8]+'.tar');assert not target.exists()
blobs={};links={}
with target.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=9,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
 for name,p in sorted(selected.items()):
  item=archive.gettarinfo(str(p),arcname=name);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
  h=manifest.get(name,{}).get('sha256') or J.sha(p)
  if p.stat().st_size>=10000 and p.suffix not in ('.py','.sh') and not name.startswith('work/tree_r1/'):
   if h in blobs:
    item.type=tarfile.LNKTYPE;item.linkname=blobs[h];item.size=0;links[name]=item.linkname;archive.addfile(item);continue
   blobs[h]=name
  with p.open('rb') as stream:archive.addfile(item,stream)
seen={}
with tarfile.open(target,'r|gz') as archive:
 for member in archive:
  assert member.name not in seen
  if member.islnk():seen[member.name]=dict(seen[member.linkname]);continue
  assert member.isfile();h=hashlib.sha256()
  with archive.extractfile(member) as stream:
   for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
  seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
expected={**manifest,'work/build24c/PACKAGE_MANIFEST.json':dict(bytes=(D/'PACKAGE_MANIFEST.json').stat().st_size,sha256=J.sha(D/'PACKAGE_MANIFEST.json'))}
assert seen==expected
growth=size()-start;assert growth<300_000_000
record=dict(status='PASS',GO=False,package=str(target.relative_to(L)),package_seal=seal,sha256=J.sha(target),bytes=target.stat().st_size,members=len(seen),stream_verified=True,kind='kit-only overlay on build24b',base=value['base'],kits=kits,tree_sha256=kits['q']['tree_seal'],workspace_start_bytes=start,workspace_growth_bytes=growth,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(D/'DELIVERY.json',record);J.write(L/'out/DELIVERY_24C.json',record)
print(json.dumps(record,indent=2))
