from common import *
import tarfile,shutil,subprocess
F=D/'hidden';old=F/'old_view';old.mkdir()
with tarfile.open(L/'out/tree_rebuild_b24m1_63d040db.tar') as f:
 for m in f:
  prefix='work/build24/kits/q/'
  if m.isfile() and m.name.startswith(prefix):
   p=old/m.name[len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(f.extractfile(m).read());p.chmod(m.mode)
assert J.seal(old)==J.load(L/'out/DELIVERY_24M1.json')['kits']['q']
spec=J.load(old/'k/p.json');spec['n_root']='/tmp/f/target';spec['host_paths']={};cap(old,'k/p.json',spec)
hp=J.load(old/'k/h.json');hp['routing_selection']=dict(path='u/'+J.sha(F/'selection.json'),sha256=J.sha(F/'selection.json'));cap(old,'k/h.json',hp);reseal(old)
s=(D/'hidden_final2.py').read_text();tail=s[s.index('results=[]'):]
tail=tail.replace("node=F/(name+'_'+mode)","node=F/(name+'_'+mode+'_final')")
(D/'hidden_run.py').write_text("from common import *\nimport subprocess\nF=D/'hidden';old=F/'old_view'\n"+tail)
