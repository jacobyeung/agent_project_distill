from common import *
D=L/'work/build24m4x2/contract'
import importlib.util,copy,subprocess,sys
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('rcj_contract',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
F=D/'rcj_contract';F.mkdir();root=F/'node';root.mkdir()
records=[];orig=J.load
class Z:
 sha=staticmethod(J.sha);write=staticmethod(J.write)
 @staticmethod
 def checked(p,h,size=None):return Path(p)
 @staticmethod
 def load(p):
  if str(p).endswith('k/p.json'):return dict(namespace='/tmp/q_22c714e1',n_root=str(F/'remote'))
  if str(p).endswith('k/l.json'):return dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='a'*64))
  return orig(p)
env=dict(venv=str(root/'v'),paths=[str(root/'f'),str(root/'np'),str(kit('qd')/'b'),str(root/'cl'),str(root/'cl/site_alias')],mounts=[[str(root/'m'),'/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a']],scratch=str(root/'g'),record=str(root/'e.json'))
J.write(root/'env.json',env)
for mode in ('b','r'):
 J.write(root/'mode.json',dict(mode=mode))
 seen=[]
 def launch(cmd,**kw):seen.append((cmd,kw));return type('P',(),{'returncode':0})()
 with patch.object(R,'attach',return_value=Z),patch.object(R.subprocess,'run',side_effect=launch):assert R.launch(kit('qd'),root,'123')==0
 cmd,kw=seen[0]
 assert '--dev-bind' in cmd and '--proc' in cmd
 assert any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd))) == (mode=='b')
 assert '--bind' in cmd and not any(str(F/'remote')==x for x in cmd)
 assert 'publish' not in cmd and cmd[-4]=='run'
 if mode=='r':
  assert '--setenv' in cmd and 'PYTHONPATH' in cmd and os.pathsep.join(env['paths']) in cmd
  assert str(root/'g') in cmd and '/scratch' in cmd and '/tmp/q_22c714e1' in cmd
  assert '-I' not in cmd and '-s' in cmd and '-B' in cmd
 else:assert '-I' in cmd
 records.append(dict(case='launch_'+mode,command=cmd,environment_keys=sorted(set(kw['env'])-set(os.environ))))

# rdiff uses the exact full script hash and never relaxes the production gate.
seen=[];checks=[]
target=F/'remote/o/123';target.mkdir(parents=True)
def checked(p,h,size=None):checks.append((str(p),h));return Path(p)
with patch.object(R,'attach',return_value=Z),patch.object(Z,'checked',side_effect=checked),patch.object(R.subprocess,'run',side_effect=lambda cmd,**kw:seen.append(cmd) or type('P',(),{'returncode':0})()):
 assert R.rdiff(kit('qd'),root,target)==0
cmd=seen[0];assert '--expected-p-sha256' not in cmd
assert checks[0][1]=='bc2db7747322d4c3eda8372ce4c9a3e74d457baa609f2798c465bf4054e75d92'
assert str(root/'dr/p/q/n.json') in cmd and str(target/'rd0') in cmd
records.append(dict(case='rdiff_contract',command=cmd,authenticated_script=checks[0]))

# Run the unchanged comparison script against small synthetic SQLite files.
import sqlite3
db=F/'a.sqlite'
with sqlite3.connect(db) as c:
 c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
 c.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(dict(dataset='fixture',scene='room',qid='q')), '{}'))
J.write(F/'n.json',dict(remove_files=[]))
cmd=[sys.executable,'-I','-s','-B',str(D/'rdiff.py'),str(db),str(db),'--tree',str(T),'--removal-manifest',str(F/'n.json'),'--base',str(F),'--out',str(F/'rd0'),'--expected-p-sha256',J.sha(db)]
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(D/'rdiff_fixture.log').write_text(p.stdout);assert p.returncode==0,p.stdout
summary=J.load(F/'rd0/rdiff_summary.json');assert summary['matched_identical']==1 and summary['mismatched']==0
records.append(dict(case='real_rdiff_synthetic_database',summary=summary,scope='Synthetic DB hash supplied only by this local test; production wrapper uses default full P gate'))
J.write(D/'RCJ_CONTRACT_TESTS.json',dict(status='PASS',records=records))
print('RCJ CONTRACT PASS',len(records),'groups')
