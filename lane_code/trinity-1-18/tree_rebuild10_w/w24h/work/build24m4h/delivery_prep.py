import sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from launch_r1.build import verify
seals={n:verify(kit(n)) for n in NAMES};assert seals==J.load(D/'SEALS.json')
base=J.load(D/'ORIGINAL_KITS.json');baseline=J.load(L/'out/UPLOADS_24M4E.json')
for row in baseline['files']:
 n,rel=row['name'].split('/',1)
 if n in base:
  assert base[n][rel]['sha256']==row['sha256'] and base[n][rel]['bytes']==row['bytes']
upload=D/'upload';upload.mkdir();rows=[]
def record(p,name,action):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action=action,transfer='local-upload')
final={}
for n in NAMES:
 final[n]={str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()}
 if n=='n_go':continue
 for rel,v in sorted(final[n].items()):
  if base[n].get(rel)==v:continue
  p=upload/n/rel;p.parent.mkdir(parents=True,exist_ok=True);os.link(kit(n)/rel,p);rows.append(record(p,n+'/'+rel,'replace' if rel in base[n] else 'add'))
for kind in ('manifest','selection'):
 h=J.load(D/'CONFIG_INPUTS.json')[kind]['sha256'];src=input_file(h);p=upload/'u'/h;p.parent.mkdir(parents=True,exist_ok=True);os.link(src,p);rows.append(record(p,'u/'+h,'add'))
copies=J.load(L/'out/ORCHARD_COPIES_24M4H.json')
for item in copies:
 rows.append(dict(name='u/'+item['sha256'],sha256=item['sha256'],bytes=item['size'],mode='0400',local_path=None,source_path=item['source'],action='add',transfer='orchard-copy',destination=item['destination']))
replayed=copy.deepcopy(base)
for row in rows:
 n,rel=row['name'].split('/',1)
 if n in replayed:replayed[n][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
assert all(replayed[n]==final[n] for n in ('q','n','qd'))
local=[r for r in rows if r['transfer']=='local-upload']
up=dict(schema='build24m4h-upload-diff-v1',baseline='24m4e kits and UPLOADS_24M4E.json',baseline_manifest_sha256=J.sha(L/'out/UPLOADS_24M4E.json'),baseline_kit_seals={n:J.load(L/'attic/build24m4h'/kit(n).relative_to(L)/'BUILD.json')['kit_sha256'] for n in NAMES},stream_root=str(upload),files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),local_upload_files=len(local),local_upload_bytes=sum(r['bytes'] for r in local),orchard_copy_files=len(copies),orchard_copy_bytes=sum(r['size'] for r in copies),orchard_copies_manifest='out/ORCHARD_COPIES_24M4H.json',kits={n:seals[n] for n in ('q','n','qd')},GO=False,n_go_upload_authorized=False,uploaded=False,launch_authorized=False,outside_kit_files=[],list_semantics='UPLOADS_24M4H.list includes all delta names; LOCAL.list includes the actual local stream. orchard-copy rows have no local_path and must be copied from the listed P kit path with hash/size verification.')
J.write(L/'out/UPLOADS_24M4H.json',up)
(L/'out/UPLOADS_24M4H.list').write_text(''.join(r['name']+'\n' for r in rows))
(L/'out/UPLOADS_24M4H_LOCAL.list').write_text(''.join(r['name']+'\n' for r in local))
go=[record(kit('n_go')/rel,'n/'+rel,'replace') for rel,v in final['n_go'].items() if v!=final['n'][rel]]
assert {r['name'] for r in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4H_GO.json',dict(schema='build24m4h-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(r['bytes'] for r in go),upload_authorized=False))
J.write(D/'UPLOAD_RECONSTRUCTION.json',dict(status='PASS',baseline_manifest_sha256=up['baseline_manifest_sha256'],all_three_kits_match=True,no_tree_archive_changes=True,remote_copy_separate=True,n_go_excluded=True))
# Keep the failure record's exact output reference valid after retaining test runs.
p=D/'WRITE_BOUNDARY_INCIDENT.json';v=J.load(p);v['failure_log']='attic/build24m4h/test_pass1/resolver600_tests.log';replace(p,json.dumps(v,sort_keys=True,indent=2)+'\n')
print('DELTA',len(rows),up['total_bytes'],'LOCAL',len(local),up['local_upload_bytes'],'COPY',up['orchard_copy_bytes'])
