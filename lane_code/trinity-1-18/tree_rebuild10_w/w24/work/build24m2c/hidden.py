"""Exercise production receipt closure with all host roots hidden."""
from common import *
import subprocess,shutil,tarfile,copy
F=D/'hidden';F.mkdir(exist_ok=True);inputs=F/'inputs';inputs.mkdir(exist_ok=True)
def link(a,b):
 if Path(b).exists():return
 try:os.link(a,b)
 except OSError as e:
  if e.errno!=18:raise
  shutil.copyfile(a,b)
audit=J.load(D/'PIN_AUDIT.json');available=audit['available']
for h,p in available.items():
 if Path(p).stat().st_size<5_000_000 and J.sha(p)==h:link(p,inputs/h)
receipt=L.parent/'ext/m400real/e.json';h=J.sha(receipt)
if not (inputs/h).exists():link(receipt,inputs/h)
J.write(F/'receipt.json',dict(path='/tmp/f/inputs/'+h,sha256=h,bytes=receipt.stat().st_size))
old=F/'old';old.mkdir()
with tarfile.open(L/'out/tree_rebuild_b24m1_63d040db.tar') as archive:
 for member in archive:
  prefix='work/build24/kits/q/'
  if member.name.startswith(prefix):
   p=old/member.name[len(prefix):];p.parent.mkdir(parents=True,exist_ok=True)
   p.write_bytes(archive.extractfile(member).read());p.chmod(member.mode)
assert J.seal(old)==J.load(L/'out/DELIVERY_24M1.json')['kits']['q']
for name in ('old','q','n','n_go','qd'):
 src=old if name=='old' else kit(name);k=F/name if name!='old' else F/'old_view'
 def copyfile(a,b):
  if Path(a).name in ('p.json','h.json','BUILD.json','SHA256SUMS.txt'):return shutil.copyfile(a,b)
  os.link(a,b);return b
 shutil.copytree(src,k,copy_function=copyfile)
 spec=J.load(k/'k/p.json');spec['n_root']='/tmp/f/target';spec['host_paths']={}
 cap(k,'k/p.json',spec)
 selected=J.write(F/'selection.json',dict(regenerated_sha256='1'*64,rows=1,row_id_digest='2'*64))
 target=F/'target/u';target.mkdir(parents=True,exist_ok=True)
 if not (target/selected['sha256']).exists():os.link(selected['path'],target/selected['sha256'])
 host=J.load(k/'k/h.json');host['routing_selection']=dict(path='u/'+selected['sha256'],sha256=selected['sha256']);cap(k,'k/h.json',host)
 for entry in spec['uploads']:
  h=entry['sha256'];p=Path(available[h]);assert J.sha(p)==h
  if not (target/h).exists():link(p,target/h)
 reseal(k)
cfg=J.load(kit('q')/'k/n.json');spec=J.load(kit('q')/'k/p.json')
pc=J.load(available[spec['p_run']['config']['sha256']]);cfg['s1_routing']=pc['s1_routing']
cfg['r1_training']['p_run']=spec['p_run']
small={p.name:dict(path='/tmp/f/inputs/'+p.name,bytes=p.stat().st_size,original='u/'+p.name) for p in inputs.iterdir()}
# Payload stand-ins represent only databases already named in the sealed staging
# map. Production metadata stays byte-exact. The missing P database has no stand-in.
sys.path.insert(0,str(kit('q')/'b'))
from px import inventory
boundary={}
for h,rows in inventory(kit('q')).items():
 if h in small:continue
 p=F/'payload'/h;p.parent.mkdir(exist_ok=True);p.write_bytes(b'SQL production payload boundary\n')
 boundary[h]='/tmp/f/payload/'+h
J.write(F/'boundary.json',boundary)
J.write(F/'resolved.json',dict(config=cfg,archive=None,small_files=small,receipt=J.load(F/'receipt.json'),
 paths={},request=J.load(kit('q')/'k/r.json'),external_metadata=[dict(sha256=h,path=p,bytes=32) for h,p in boundary.items()]))
runner=F/'run.py';runner.write_text('''from pathlib import Path
import sys,json,os
sys.path[:0]=['/tmp/k/b','/tmp/t']
import z,pl
boundary=z.load('/tmp/f/boundary.json');native=z.checked;calls=[]
def checked(p,h,size=None):
 p=Path(p);calls.append(str(p))
 if str(p).startswith(('/scratch/','/home/','/data','/lustre/')):
  raise RuntimeError('LITERAL_HOST_PATH:'+str(p))
 if boundary.get(h)==str(p):return p
 return native(p,h,size)
z.checked=pl.checked=checked
v=z.load('/tmp/f/resolved.json');v['kit_sha256']=z.seal('/tmp/k')
try:pl.plan_payload('/tmp/k',v,Path('/tmp/node/p'),regeneration=sys.argv[1]=='r')
except Exception as error:
 z.write('/tmp/node/result.json',dict(refusal=str(error),calls=calls,mode=sys.argv[1]))
else:raise AssertionError('expected production boundary')
''')
results=[]
for name in ('old','q','n','n_go','qd'):
 for mode in ('r','q'):
  k=F/('old_view' if name=='old' else name);node=F/(name+'_'+mode);(node/'p').mkdir(parents=True)
  if name=='qd':os.link(F/'selection.json',node/'routing_selection.json')
  args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp',
   '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py',
   '--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f','--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node',
   '/opt/py/bin/python3','-B','-s','/tmp/f/run.py',mode]
  subprocess.run(args,check=True)
  value=J.load(node/'result.json');value.update(kit=name)
  if name=='old':assert value['refusal'].startswith('LITERAL_HOST_PATH:') and 'routing/rows.sqlite' in value['refusal'],value
  else:assert value['refusal']=='R1_STAGED_PIN_MISSING:4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84:config.streams.routing.database',value
  results.append(value);print(name,mode,value['refusal'],flush=True)
J.write(D/'HIDDEN_PATH_TESTS.json',dict(status='PASS',production_ready=False,records=results,real_receipts=True,
 hidden=['/scratch/jjyeung','/scratch/fsw','/lustre','/home','/data','/data2','/data3'],
 stand_ins=['Unavailable payloads already listed in the staged inventory; metadata bytes are original','Reviewed selection placeholder only to reach planning'],
 scope='Both planners execute plan_payload. The baseline opens a literal host path; all final kits refuse the unstaged P database by hash and config field before production IO.'))
