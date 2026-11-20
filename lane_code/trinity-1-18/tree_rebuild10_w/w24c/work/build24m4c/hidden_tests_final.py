from common import *
import subprocess
F=D/'hidden';old=F/'old_view'
results=[]
for name in ('q','n','n_go','qd'):
 for mode in ('r','q'):
  k=old if name=='old' else F/name;node=F/(name+'_'+mode+'_c_final');(node/'p').mkdir(parents=True)
  if name=='qd':os.link(F/'selection.json',node/'routing_selection.json')
  args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp',
   '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py',
   '--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f','--ro-bind','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/hidden/inputs','/tmp/f/inputs','--ro-bind','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/hidden/payload','/tmp/f/payload','--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node',
   '/opt/py/bin/python3','-B','-s','/tmp/f/run.py',mode]
  mount=[]
  available=J.load(L.parent/'w24/work/build24m2c/PIN_AUDIT.json')['available']
  for item in J.load(k/'k/p.json')['uploads']:
   h=item['sha256'];p=F/'target/u'/h
   if not p.exists():p=L.parent/'w24/work/build24m3/hidden/target/u'/h
   if not p.exists():p=Path(available[h])
   assert J.sha(p)==h
   mount.extend(['--ro-bind',str(p),'/tmp/f/target/u/'+h])
  h=J.sha(F/'selection.json');mount.extend(['--ro-bind',str(F/'selection.json'),'/tmp/f/target/u/'+h])
  at=args.index('/opt/py/bin/python3');args[at:at]=['--tmpfs','/tmp/f/target/u']+mount
  subprocess.run(args,check=True)
  value=J.load(node/'result.json');value.update(kit=name,final_kit_seal=J.seal(kit(name)) if name!='old' else None)
  if name=='old':assert value['refusal'].startswith('LITERAL_HOST_PATH:'),value
  else:assert value['refusal'].startswith('R1_STAGED_PIN_MISSING:eac5f9f0'),value
  results.append(value);print(name,mode,value['refusal'],flush=True)
J.write(D/'HIDDEN_PATH_TESTS.json',dict(status='PASS',records=results,real_receipts=True,production_ready=False,stand_ins='Unavailable payload bodies already authenticated by supplied inventory; missing catalog is not fabricated. Every real metadata receipt stays byte-identical.'))
