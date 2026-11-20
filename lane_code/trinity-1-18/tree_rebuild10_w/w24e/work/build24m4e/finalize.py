from common import *
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
from launch_r1.build import verify
from copy import deepcopy
original=J.load(D/'ORIGINAL_FILES.json');changed={}
for rel,item in original.items():
 p=L/rel
 if p.is_file() and dict(sha256=J.sha(p),mode=p.stat().st_mode&511,bytes=p.stat().st_size)==item:continue
 old=L/'attic/build24m4e'/rel
 assert old.is_file() and dict(sha256=J.sha(old),mode=old.stat().st_mode&511,bytes=old.stat().st_size)==item,(rel,'original not preserved')
 changed[rel]=str(old.relative_to(L))
allowed={str((kit(n)/rel).relative_to(L)) for n in ('q','n','n_go','qd') for rel in ('k/p.json','BUILD.json','SHA256SUMS.txt')}
assert set(changed)==allowed,changed
files=inventory(T);tree=digest(files);assert files==J.load(L/'work/build24m4c/TREE24L4_SEAL.json')['files']
assert tree=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
pins=J.load(D/'PINS.json');cat=pins['pins'][0]['sha256'];seals={};full={}
for n in ('q','n','n_go','qd'):
 k=kit(n);seals[n]=verify(k)
 assert J.load(k/'k/a.json')['GO']==(n=='n_go')==J.load(k/'BUILD.json')['GO']
 assert J.load(k/'k/7.json')['files']==files==J.load(k/'k/c0.json')['files']
 check_archive(file_pin(k/J.load(k/'k/a.json')['source']['path']),files)
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
 before=J.load(L/changed[str((k/'k/p.json').relative_to(L))]);after=J.load(k/'k/p.json')
 assert after['pin_paths'][cat]==after['namespace']+'/u/'+cat
 found=[r for r in after['uploads'] if r['sha256']==cat];assert found==[dict(sha256=cat,bytes=74599,opaque_name='u/'+cat)]
 after['uploads']=[r for r in after['uploads'] if r['sha256']!=cat];after['pin_paths'].pop(cat)
 before['uploads']=sorted(before['uploads'],key=lambda r:r['sha256']);after['uploads']=sorted(after['uploads'],key=lambda r:r['sha256'])
 assert before==after,'Unexpected staging-spec change'
 full[n]={}
 for p in k.rglob('*'):
  if not p.is_file():continue
  mode=p.stat().st_mode&511
  assert mode==original[str(p.relative_to(L))]['mode'],(p,mode)
  full[n][str(p.relative_to(k))]=dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=mode)
assert J.sha(L/'out/arm_routing.py')==original['out/arm_routing.py']['sha256']
unchanged=['Tree C and every source archive','Every kit executable, including pl.py, px.py, rv.py, b/pc.py and resolver identity checks','arm_routing.py semantics','All training configs, census, admission, legality, removals, opener rows, step-544 lineage and DEFERRED boundary']
J.write(D/'INVARIANTS.json',dict(status='PASS',original_files_verified=len(original),preserved_originals=changed,tree_sha256=tree,tree_files=len(files),kits=seals,unchanged=unchanged,only_change='Catalog upload inventory entry and pin_paths plus dependent seals',GO='false except out/kit_n_go'))
base=J.load(L/'work/build24m4d/ORCHARD_24M3_BASELINE.json')['kits'];m3=J.load(L/'out/UPLOADS_24M3.json')
known={r['name']:r for r in m3['files']};known['u/'+cat]=dict(sha256=cat,bytes=74599,mode='0400')
basis='24m3: UPLOADS_24M3.json applied on top of 24m2d, plus u/'+cat+' already present (0400)'
J.write(D/'ORCHARD_BASELINE.json',dict(basis=basis,kits=base,already_present=dict(name='u/'+cat,sha256=cat,size=74599,mode='0400'),baseline_manifest_sha256=J.sha(L/'out/UPLOADS_24M3.json')))
upload=D/'upload';upload.mkdir();rows=[]
def record(p,name,action):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action=action)
for n in ('q','n','qd'):
 for rel,row in sorted(full[n].items()):
  old=base[n].get(rel)
  if old==row:continue
  dst=upload/n/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.link(kit(n)/rel,dst);rows.append(record(dst,n+'/'+rel,'replace' if old else 'add'))
# Carry the outstanding 24m4d input delta by verified bytes from this untar.
for old in J.load(L/'out/UPLOADS_24M4D.json')['files']:
 if not old['name'].startswith('u/'):continue
 if old['name'] in known and known[old['name']]['sha256']==old['sha256']:continue
 src=L/'work/build24m4d/upload'/old['name'];assert J.sha(src)==old['sha256'] and src.stat().st_size==old['bytes']
 dst=upload/old['name'];dst.parent.mkdir(parents=True,exist_ok=True);os.link(src,dst);rows.append(record(dst,old['name'],'add'))
for row in m3['outside_kit_files']:assert J.sha(L/'out'/row['name'])==row['sha256']
reconstructed=deepcopy(base)
for row in rows:
 n,rel=row['name'].split('/',1)
 if n in reconstructed:reconstructed[n][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
assert all(reconstructed[n]==full[n] for n in ('q','n','qd'))
assert all(r['name']!='u/'+cat and not r['name'].startswith('n_go/') for r in rows)
assert J.load(L/'out/ORCHARD_COPIES_24M4E.json')==[]
up=dict(schema='build24m4e-upload-diff-v1',baseline=basis,baseline_inventory='work/build24m4e/ORCHARD_BASELINE.json',baseline_inventory_sha256=J.sha(D/'ORCHARD_BASELINE.json'),baseline_manifest_sha256=J.sha(L/'out/UPLOADS_24M3.json'),stream_root=str(upload),top_directories=['q','n','qd','u'],files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),kits={n:seals[n] for n in ('q','n','qd')},already_present=[dict(name='u/'+cat,sha256=cat,size=74599,bytes=74599,mode='0400',destination='x_22c714e1/u/'+cat,upload=False,basis='Lane supplied current Orchard state')],orchard_copies_manifest='out/ORCHARD_COPIES_24M4E.json',orchard_copies=[],GO=False,n_go_upload_authorized=False,outside_kit_files=[],uploaded=False)
J.write(L/'out/UPLOADS_24M4E.json',up);(L/'out/UPLOADS_24M4E.list').write_text(''.join(r['name']+'\n' for r in rows))
go=[]
for rel,row in full['n_go'].items():
 if row!=full['n'][rel]:go.append(record(kit('n_go')/rel,'n/'+rel,'replace'))
assert {r['name'] for r in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4E_GO.json',dict(schema='build24m4e-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(r['bytes'] for r in go),upload_authorized=False))
J.write(D/'UPLOAD_RECONSTRUCTION.json',dict(status='PASS',all_three_kits_match=True,already_present_catalog_not_uploaded=True,GO_files_not_uploaded=True,base=basis))
print('Original bytes/modes, tree, staging-only scope, and upload reconstruction PASS',len(rows),up['total_bytes'],flush=True)
