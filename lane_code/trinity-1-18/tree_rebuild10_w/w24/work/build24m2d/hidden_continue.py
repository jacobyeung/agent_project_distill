"""Exercise production receipt closure with all host roots hidden."""
from common import *
import subprocess,shutil,tarfile,copy
F=D/'hidden'
resolved=J.load(F/'resolved.json');boundary=J.load(F/'boundary.json')
sys.path.insert(0,str(kit('q')/'b'))
from z import selected400
for row in J.load(L.parent/'ext/m400real/MANIFEST.json')['files']:
 try:selected400(row['path'])
 except ValueError:continue
 h=row['sha256']
 if h in resolved['small_files'] or h in boundary:continue
 p=F/'payload'/h;p.write_bytes(b'SQL authenticated m400 payload boundary\n');boundary[h]='/tmp/f/payload/'+h
 resolved['external_metadata'].append(dict(sha256=h,path=boundary[h],bytes=p.stat().st_size))
J.write(F/'boundary.json',boundary);J.write(F/'resolved.json',resolved)
results=[]
for name in ('old','q','n','n_go','qd'):
 for mode in ('r','q'):
  k=F/('old_view' if name=='old' else name);node=F/(name+'_'+mode+'_v2');(node/'p').mkdir(parents=True)
  if name=='qd':os.link(F/'selection.json',node/'routing_selection.json')
  args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp',
   '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py',
   '--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f','--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node',
   '/opt/py/bin/python3','-B','-s','/tmp/f/run.py',mode]
  subprocess.run(args,check=True)
  value=J.load(node/'result.json');value.update(kit=name)
  if name=='old':assert value['refusal'].startswith('LITERAL_HOST_PATH:') and 'routing/rows.sqlite' in value['refusal'],value
  else:
   assert value['refusal'].startswith('R1_STAGED_PIN_MISSING:eac5f9f0'),value['refusal']
   assert '4e8e6c04' not in value['refusal'],value
  results.append(value);print(name,mode,value['refusal'],flush=True)
J.write(D/'HIDDEN_PATH_TESTS.json',dict(status='PASS',production_ready=False,records=results,real_receipts=True,
 hidden=['/scratch/jjyeung','/scratch/fsw','/lustre','/home','/data','/data2','/data3'],
 stand_ins=['Unavailable payloads already listed in the staged inventory; metadata bytes are original','Reviewed selection placeholder only to reach planning'],
 scope='Both planners execute plan_payload. The baseline opens a literal host path; mode r plans reconstruction and mode q follows the selection base; final kits refuse the unavailable catalog by hash and field before preparation.'))
