from common import *
import copy
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
seals={n:verify(kit(n)) for n in NAMES};assert seals==J.load(D/'SEALS.json')
base=J.load(L/'work/build24m4l/BASE_FILES.json');baseseals=J.load(L/'work/build24m4l/BASE_SEALS.json')
final={n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES}
upload=D/'upload';upload.mkdir();rows=[]
def record(p,name,action='replace'):
 q=upload/name;q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
 return dict(name=name,sha256=J.sha(q),bytes=q.stat().st_size,mode=format(q.stat().st_mode&511,'04o'),local_path=str(q),action=action,transfer='local-upload')
for n in ('q','n','qd'):
 assert not J.load(kit(n)/'k/a.json')['GO'] and not J.load(kit(n)/'BUILD.json')['GO']
 for rel,v in sorted(final[n].items()):
  if v!=base[n].get(rel):rows.append(record(kit(n)/rel,n+'/'+rel))
oldrcj=J.load(L/'work/build24m4l/BASE_RCJ.json')
oldrcj['x.py']=dict(sha256=J.sha(D/'reviewed_x.py'),bytes=(D/'reviewed_x.py').stat().st_size)
assert oldrcj['x.py']['sha256']=='7b9d646994904cca6f9bf22c94b8a30bbd5ff08287d7b7c16dc2e7a99f33947f'
assert oldrcj['rcj.sh']['sha256']=='b23393f2db4dfe65bbd91a771fb7c5d34f51a5669b820c33b6158fb68f9f5e8c'
for p in sorted((L/'out/rcj').iterdir()):
 if p.is_file() and oldrcj.get(p.name,{}).get('sha256')!=J.sha(p):rows.append(record(p,'rcj/'+p.name,'replace' if p.name in oldrcj else 'add'))
runtime=J.load(D/'RUNTIME_PIN_UPDATE.json')['n'];rows.append(record(Path(runtime['path']),'u/'+runtime['new'],'add'))
replay=copy.deepcopy(base)
for r in rows:
 n,rel=r['name'].split('/',1)
 if n in replay:replay[n][rel]=dict(sha256=r['sha256'],bytes=r['bytes'],mode=int(r['mode'],8))
assert all(replay[n]==final[n] for n in ('q','n','qd'))
up=dict(schema='build24m4n-upload-diff-v1',baseline='Orchard q/n/qd at 24m4j; rcj x.py 7b9d6469 and rcj.sh b23393f2',baseline_kit_seals={n:baseseals[n] for n in ('q','n','qd')},baseline_rcj=oldrcj,
 files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),stream_root=str(upload),kits={n:seals[n] for n in ('q','n','qd')},GO=False,uploaded=False,launched=False,
 n_go_in_ordinary_stream=False,source_tree=digest(inventory(T)),shared_u_additions=[runtime['new']],unchanged_rcj_files=['rcj/rcj.sh'])
J.write(L/'out/UPLOADS_24M4N.json',up);replace(L/'out/UPLOADS_24M4N.list',''.join(r['name']+'\n' for r in rows))
go=[]
for rel,v in sorted(final['n_go'].items()):
 if v!=final['n'][rel]:
  p=kit('n_go')/rel
  go.append(dict(name='n/'+rel,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action='replace'))
assert {r['name'] for r in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4N_GO.json',dict(schema='build24m4n-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(r['bytes'] for r in go),uploaded=False))
J.write(D/'UPLOAD_REPLAY.json',dict(status='PASS',baseline_kit_seals=baseseals,final_kit_seals=seals,ordinary_delta_files=len(rows),ordinary_delta_bytes=up['total_bytes'],all_three_kits_exact=True,GO_excluded=True))
cfg=kit('n_go')/'k/c.json'
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=digest(inventory(T)),kits=seals,n_go_identity=identity(J.load(cfg)),n_go_payload_sha256=J.load_raw(cfg)['sha256'],n_go_file_sha256=J.sha(cfg),GO='false except out/kit_n_go'))
print('DELTA',len(rows),up['total_bytes'],'GO',len(go));print('N_GO_IDENTITY',identity(J.load(cfg)))
