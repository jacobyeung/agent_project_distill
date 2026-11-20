from common import *
from unittest.mock import patch
from copy import deepcopy
import tarfile,subprocess
sys.path[:0]=[str(kit('n')/'b'),str(L/'work/build21')]
import z,resolver21e as R
root=D/'resolver/proofs/real';pool=root/'pool';listing=root/'listing.json'
f=dict(external=J.load(listing)['metadata']);records=[]
native=z.load
for name in ('q','n','n_go','qd'):
 k=kit(name);spec=deepcopy(J.load(k/'k/p.json'));m=pool/spec['milestone']
 with tarfile.open(m/'s.tar') as t:spec['m4']['v']=hashlib.sha256(t.extractfile('MANIFEST.json').read()).hexdigest()
 marker=(pool/spec['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();spec['m4'].update(t=marker[2],b=int(marker[1]))
 with R.external_boundary(f,module=z),patch.object(z,'load',side_effect=lambda p:deepcopy(spec) if Path(p)==k/'k/p.json' else native(p)),patch.object(z,'write'):
  value=z.resolve(k,pool,listing,D/'unused_resolver_output.json')
 h=spec['code_sha256'];assert value['config']['code']['sha256']==h and h in value['paths']
 assert spec['pin_paths']=={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']}
 records.append(dict(kit=name,seal=J.seal(k),source_sha256=h,resolver='PASS'))
J.write(D/'SOURCE_PIN_TESTS.json',dict(status='PASS',records=records,boundary='Retained real-receipt fixture; external model payload boundary only; final output serialization suppressed to conserve disk.'))

F=D/'hidden';h=J.load(kit('q')/'k/p.json')['code_sha256'];target=F/'target/u'/h
if not target.exists():os.link(D/'generated/u'/h,target)
resolved=J.load(F/'resolved.json');resolved['config']['code']=J.load(kit('q')/'k/n.json')['code'];J.write(F/'resolved.json',resolved)
for name in ('q','n','n_go','qd'):
 k=F/name
 for part in ('k/n.json','b/pl.py','b/px.py'):replace(k/part,(kit(name)/part).read_bytes())
 spec=J.load(kit(name)/'k/p.json');spec['n_root']='/tmp/f/target';spec['host_paths']={};cap(k,'k/p.json',spec)
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 reseal(k)
results=[]
for name in ('old','q','n','n_go','qd'):
 for mode in ('r','q'):
  k=F/('old_view' if name=='old' else name);node=F/(name+'_'+mode)
  prev=L/'attic/build24m2c/hidden'/node.name/'p';prev.parent.mkdir(parents=True,exist_ok=True);(node/'p').rename(prev);(node/'p').mkdir()
  args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp',
   '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py',
   '--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f','--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node',
   '/opt/py/bin/python3','-B','-s','/tmp/f/run.py',mode]
  subprocess.run(args,check=True);v=J.load(node/'result.json');v.update(kit=name,final_kit_seal=J.seal(kit(name)) if name!='old' else J.seal(F/'old'))
  if name=='old':assert v['refusal'].startswith('LITERAL_HOST_PATH:') and 'routing/rows.sqlite' in v['refusal']
  else:assert v['refusal']=='R1_STAGED_PIN_MISSING:4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84:config.streams.routing.database',v
  results.append(v);print(name,mode,v['refusal'],flush=True)
v=J.load(D/'HIDDEN_PATH_TESTS.json');v['records']=results;J.write(D/'HIDDEN_PATH_TESTS.json',v)
