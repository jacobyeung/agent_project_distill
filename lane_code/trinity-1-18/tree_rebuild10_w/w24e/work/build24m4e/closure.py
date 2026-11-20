from common import *
import subprocess,shutil,copy
F=D/'hidden';F.mkdir();target=F/'target/u';target.mkdir(parents=True)
W=L.parent/'w24';C=L.parent/'w24c';old=C/'work/build24m4c/hidden'
available=J.load(W/'work/build24m2c/PIN_AUDIT.json')['available']
external_links=[];mounts=[]
def link(a,b):
 a=Path(a);b=Path(b)
 if b.exists():return
 b.parent.mkdir(parents=True,exist_ok=True)
 if a.resolve().is_relative_to(L):os.link(a,b)
 else:
  b.touch();mounts.extend(['--ro-bind',str(a),'/tmp/f/'+str(b.relative_to(F))])
 if not a.resolve().is_relative_to(L):
  st=a.stat();external_links.append(dict(path=str(a),target=str(b.relative_to(L)),inode=f'{st.st_dev}:{st.st_ino}',blocks=st.st_blocks))
for e in J.load(kit('q')/'k/p.json')['uploads']:
 h=e['sha256'];src=old/'target/u'/h
 if h.startswith('eac5f9f0'):src=D/'inputs/pool_selection_eac5f9f0.json'
 if not src.is_file():src=Path(available[h])
 assert src.stat().st_size==e['bytes'] and J.sha(src)==h
 link(src,target/h)
cat='eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9'
assert J.sha(D/'inputs/pool_selection_eac5f9f0.json')==cat
assert (D/'inputs/pool_selection_eac5f9f0.json').stat().st_size==74599
link(D/'inputs/pool_selection_eac5f9f0.json',target/cat)
for d in ('inputs','payload'):
 (F/d).mkdir();mounts.extend(['--ro-bind',str(W/'work/build24m3/hidden'/d),'/tmp/f/'+d])
selection=J.load(old/'selection.json');J.write(F/'selection.json',selection)
sh=J.sha(F/'selection.json');link(F/'selection.json',target/sh)
resolved=J.load(old/'resolved.json');boundary=J.load(old/'boundary.json')
# Current decoded config; production receipt bytes and payload boundaries match
# the inherited hidden-path fixture. Mode q uses its reviewed fixture selection.
resolved['config']=J.load(kit('q')/'k/n.json')
resolved['request']=J.load(kit('q')/'k/r.json')
resolved['config']['r1_training']['p_run']=J.load(kit('q')/'k/p.json')['p_run']
J.write(F/'resolved.json',resolved)
J.write(F/'boundary.json',boundary)
byhash={}
for line in (D/'inputs/P_SHA256SUMS.txt').read_text().splitlines():
 h,path=line.split('  ',1);byhash.setdefault(h,[]).append(path)
sizes={}
for line in (D/'inputs/P_k_sizes.txt').read_text().splitlines():
 n,path=line.split(' ',1);sizes['k/'+path]=int(n)
assert J.sha(D/'inputs/P_SHA256SUMS.txt').startswith('2b8242f095c5a8c7')
pins={cat:dict(sha256=cat,size=74599,source='x_ee227714/k/pool_selection_eac5f9f0.json',fields=['config.s1_routing.catalog.'+cat,'P.materialization.inputs.catalog.'+cat],already_present=True)}
runner=F/'run.py';runner.write_text("""from pathlib import Path
import sys,json,os,traceback
sys.path[:0]=['/tmp/k/b','/tmp/t']
import z,pl
boundary=z.load('/tmp/f/boundary.json');native=z.checked;calls=[]
def checked(p,h,size=None):
 p=Path(p);calls.append(dict(path=str(p),sha256=h,size=size,boundary=boundary.get(h)==str(p)))
 if str(p).startswith(('/scratch/','/home/','/data','/lustre/')):raise RuntimeError('LITERAL_HOST_PATH:'+str(p))
 if boundary.get(h)==str(p):return p
 return native(p,h,size)
z.checked=pl.checked=checked
v=z.load('/tmp/f/resolved.json');v['kit_sha256']=z.seal('/tmp/k')
try:pl.plan_payload('/tmp/k',v,Path('/tmp/node/p'),regeneration=sys.argv[1]=='r')
except Exception as error:
 z.write('/tmp/node/result.json',dict(refusal=str(error),calls=calls,mode=sys.argv[1],traceback=traceback.format_exc()))
else:z.write('/tmp/node/result.json',dict(refusal=None,calls=calls,mode=sys.argv[1],planner_returned=True))
""")
def spec_add(spec):
 entries={e['sha256']:e for e in spec['uploads']}
 for h,row in pins.items():
  assert h not in entries or entries[h]['bytes']==row['size']
  entries[h]=dict(sha256=h,bytes=row['size'],opaque_name='u/'+h)
 spec['uploads']=[entries[h] for h in sorted(entries)]
 spec['pin_paths']={h:spec['namespace']+'/u/'+h for h in entries}
 return spec

def fixture(name,round):
 k=F/(name+'_kit_'+str(round))
 for src in kit(name).rglob('*'):
  if src.is_file():
   dst=k/src.relative_to(kit(name));dst.parent.mkdir(parents=True,exist_ok=True)
   if str(src.relative_to(kit(name))) in ('k/p.json','k/h.json','k/a.json','BUILD.json','SHA256SUMS.txt'):shutil.copyfile(src,dst);dst.chmod(src.stat().st_mode&511)
   else:os.link(src,dst)
 spec=spec_add(J.load(k/'k/p.json'));spec['n_root']='/tmp/f/target';spec['host_paths']={};cap(k,'k/p.json',spec)
 host=J.load(k/'k/h.json');host['routing_selection']=dict(path='u/'+sh,sha256=sh);cap(k,'k/h.json',host)
 for rel in ('k/a.json','BUILD.json'):
  value=J.load(k/rel);value['GO']=False;cap(k,rel,value)
 reseal(k);return k

def run(name,mode,round):
 k=fixture(name,round);node=F/(name+'_'+mode+'_'+str(round));(node/'p').mkdir(parents=True)
 if name=='qd':os.link(F/'selection.json',node/'routing_selection.json')
 args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp',
 '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py','--ro-bind','/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages','/opt/site','--setenv','PYTHONPATH','/opt/site','--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f',*mounts,'--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node',
 '/opt/py/bin/python3','-B','-s','/tmp/f/run.py',mode]
 subprocess.run(args,check=True)
 value=J.load(node/'result.json');value.update(kit=name,round=round)
 print(name,mode,value['refusal'],flush=True);return value
history=[];stopped=[]
for step in range(110):
 value=run('q','r',step);history.append(value);refusal=value['refusal'] or ''
 if not refusal.startswith('R1_STAGED_PIN_MISSING:'):break
 _,h,field=refusal.split(':',2)
 if h not in byhash:
  stopped.append(dict(sha256=h,field=field,mode='r',refusal=refusal));break
 assert h not in pins
 paths=[p for p in byhash[h] if p in sizes];assert paths,(h,byhash[h])
 path=paths[0];pins[h]=dict(sha256=h,size=sizes[path],source='x_ee227714/'+path,fields=[field],already_present=False)
 # Explicit unavailable-body boundary; this marker is never an upload and never
 # claimed to match the production hash. Its authority is P's sealed inventory.
 marker=target/h;marker.write_bytes(b'SQL authenticated P inventory body boundary\n')
 boundary[h]='/tmp/f/target/u/'+h;replace(F/'boundary.json',json.dumps(boundary,sort_keys=True,indent=2)+'\n')
else:raise AssertionError('closure did not terminate')
# Run the q branch too; a distinct missing P pin is bound by the same inventory.
for step in range(110,220):
 value=run('q','q',step);history.append(value);refusal=value['refusal'] or ''
 if not refusal.startswith('R1_STAGED_PIN_MISSING:'):break
 _,h,field=refusal.split(':',2)
 if h not in byhash:
  stopped.append(dict(sha256=h,field=field,mode='q',refusal=refusal));break
 assert h not in pins
 paths=[p for p in byhash[h] if p in sizes];assert paths
 path=paths[0];pins[h]=dict(sha256=h,size=sizes[path],source='x_ee227714/'+path,fields=[field],already_present=False)
 (target/h).write_bytes(b'SQL authenticated P inventory body boundary\n')
 boundary[h]='/tmp/f/target/u/'+h;replace(F/'boundary.json',json.dumps(boundary,sort_keys=True,indent=2)+'\n')
else:raise AssertionError('closure did not terminate')
seals={}
for name in ('q','n','n_go','qd'):
 cap(kit(name),'k/p.json',spec_add(J.load(kit(name)/'k/p.json')));seals[name]=reseal(kit(name))
final=[]
for idx,name in enumerate(('q','n','n_go','qd')):
 for j,mode in enumerate(('r','q')):final.append(run(name,mode,300+2*idx+j))
assert all(v['refusal'] and cat not in v['refusal'] and not v['refusal'].startswith('LITERAL_HOST_PATH') and 'No module named' not in v['refusal'] and 'R1_ROUTING_SELECTION_PIN_MISSING' not in v['refusal'] for v in final)
J.write(D/'PINS.json',dict(status='PASS',pins=list(pins.values()),inventory_sha256=J.sha(D/'inputs/P_SHA256SUMS.txt'),sizes_sha256=J.sha(D/'inputs/P_k_sizes.txt'),kits=seals))
J.write(D/'HIDDEN_PATH_TESTS.json',dict(status='PASS',records=final,history=history,still_missing=stopped,real_catalog=True,real_receipts=True,production_ready=False,hidden=['/scratch/jjyeung','/scratch/fsw','/lustre','/home','/data','/data2','/data3'],boundary_hashes=sorted(boundary),scope='Unchanged real planner and resolver with authentic metadata; only inventoried unavailable production bodies use explicit payload boundaries. The catalog is real and hash/size checked.'))
J.write(D/'EXTERNAL_LINKS.json',external_links)
J.write(L/'out/ORCHARD_COPIES_24M4E.json',[{k:v for k,v in row.items() if k in ('sha256','size','source')} for row in pins.values() if not row['already_present']])
lines=['Planner closure stops at the following pins absent from P’s sealed inventory.'] if stopped else ['No further missing staged pin was reached before the documented production-body boundary.']
for row in stopped:lines.append('Mode '+row['mode']+': '+row['sha256']+'; config field `'+row['field']+'`.')
lines+=['Mode '+v['mode']+' next refusal: `'+str(v['refusal'])+'`.' for v in final if v['kit']=='q']
(L/'out/STILL_MISSING_24M4E.md').write_text('\n'.join(lines)+'\n')
