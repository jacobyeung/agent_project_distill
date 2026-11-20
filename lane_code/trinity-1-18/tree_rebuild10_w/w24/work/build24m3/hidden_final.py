from common import *
import subprocess,shutil
base=L/'work/build24m2d/hidden';F=D/'hidden';F.mkdir(exist_ok=True)
for folder in ('inputs','payload'):
 assert (F/folder).is_dir()
for n in ('boundary.json','receipt.json','selection.json','run.py'):
 (F/n).write_bytes((base/n).read_bytes())
import lzma
resolved=json.loads(lzma.decompress((L/'attic/build24m2d/retained_xz/work/build24m2d/hidden/resolved.json.xz').read_bytes()))
cfg=J.load(kit('q')/'k/n.json')
resolved['config']['remove_files']=cfg['remove_files']
resolved['config']['r1_training']['launch22']['removal_order']=cfg['r1_training']['launch22']['removal_order']
J.write(F/'resolved.json',resolved)
u=F/'target/u';u.mkdir(parents=True,exist_ok=True)
old=base/'old_view'
for name in ('q','n','n_go','qd'):
 k=F/name
 def transport(a,b):
  if Path(a).name in ('p.json','h.json','BUILD.json','SHA256SUMS.txt'):return shutil.copyfile(a,b)
  os.link(a,b);return b
 if not k.exists():shutil.copytree(kit(name),k,copy_function=transport)
 spec=J.load(k/'k/p.json');spec['n_root']='/tmp/f/target';spec['host_paths']={};cap(k,'k/p.json',spec)
 for v in spec['uploads']:
  h=v['sha256'];p=D/'u'/h
  if not p.exists():p=base/'target/u'/h
  if not p.exists():p=Path(J.load(L/'work/build24m2c/PIN_AUDIT.json')['available'][h])
  assert J.sha(p)==h,(name,h,p)
  if not (u/h).exists():os.link(p,u/h)
 hp=J.load(k/'k/h.json');hp['routing_selection']=dict(path='u/'+J.sha(F/'selection.json'),sha256=J.sha(F/'selection.json'));cap(k,'k/h.json',hp)
 reseal(k)
os.link(F/'selection.json',u/J.sha(F/'selection.json'))
results=[]
for name in ('old','q','n','n_go','qd'):
 for mode in ('r','q'):
  k=old if name=='old' else F/name;node=F/(name+'_'+mode);(node/'p').mkdir(parents=True)
  if name=='qd':os.link(F/'selection.json',node/'routing_selection.json')
  args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp',
   '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py',
   '--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f','--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node',
   '/opt/py/bin/python3','-B','-s','/tmp/f/run.py',mode]
  subprocess.run(args,check=True)
  value=J.load(node/'result.json');value.update(kit=name,final_kit_seal=J.seal(kit(name)) if name!='old' else None)
  if name=='old':assert value['refusal'].startswith('LITERAL_HOST_PATH:'),value
  else:assert value['refusal'].startswith('R1_STAGED_PIN_MISSING:eac5f9f0'),value
  results.append(value);print(name,mode,value['refusal'],flush=True)
J.write(D/'HIDDEN_PATH_TESTS.json',dict(status='PASS',records=results,real_receipts=True,production_ready=False,stand_ins='Unavailable payload bodies already authenticated by supplied inventory; missing catalog is not fabricated. Every real metadata receipt stays byte-identical.'))
