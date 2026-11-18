import json,sys,tempfile,os,subprocess
from pathlib import Path
o=Path(sys.argv[1]);sys.path[:0]=[str(o),str(o/'src')]
import node_check
from orchard_h10.common import install_process_guard,write,sha
r=Path(tempfile.mkdtemp(prefix='a',dir=str(o/'checks')))
install_process_guard(r)
proof=node_check.check_bundle_guard(o/'package',r)
write(r/'a/1.json',dict(action=1,config={}))
argv=[sys.executable,'-I','-s','-B',str(r/'a/5.py'),str(r/'a/1.json')]
calls=[]
proof=node_check.dispatch_operator(r,proof,argv,lambda a,**kw:calls.append(a))
assert calls[0][-2]==str(r/'7.py') and proof['entry_sequence_passed'] is True
(o/'PY36_GUARD.json').write_text(json.dumps(proof,sort_keys=True,indent=2)+'\n')
print('guard and dispatch passed')
