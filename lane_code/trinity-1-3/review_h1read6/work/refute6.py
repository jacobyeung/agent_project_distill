import sys,json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
ROOT=Path(sys.argv[1]); sys.path.insert(0,str(ROOT/'kit/launcher'))
import binding as B, orchard_launcher as L, export_stage as E
ok=[];bad=[]
def refuses(name,f):
    try: f(); bad.append(name)
    except (ValueError,TypeError,KeyError): ok.append(name)
for run,step,gen in [('673bc60f',400,None),('673bc60f',600,None),('05b8ac69',100,None),('05b8ac69',200,None),('05b8ac69',200,'mstop'),
    ('673bc60f',201,'mstop'),('673bc60f',0,'mstop'),('05b8ac69',601,'mstopC'),('673bc60f',200,'m200'),('673bc60f',150,'mstopD'),
    ('673bc60f',544,'mstop'),('05b8ac69',544,None),('673bc60f',True,None),('673bc60f',100.0,None)]:
    refuses(f'expected {run} {step} {gen}',lambda:B.expected(run,step,gen))
refuses('ns',lambda:B.expected('673bc60f',100,namespace='8865619c'))
b=B.expected('673bc60f',200)
assert b['done']=='/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m200.done' and b['object']=='q8/8865619b/673bc60f_m200.tar' and b['claim'] is None
s=B.expected('05b8ac69',333,'mstopB')
assert s['done']=='/project/community/jjyeung/okh7/x_7f1589c1/o/gcs_05b8ac69_m333.done' and s['claim']=='/project/community/jjyeung/okh7/x_7f1589c1/o/gcs_05b8ac69_mstopB.claim' and s['object']=='q8/8865619b/05b8ac69_mstopB.tar'
t=dict(b,done=b['done'].replace('x_69d2930d','x_7f1589c1')); refuses('validate cross-KH done',lambda:B.validate(t))
t=dict(s,run='673bc60f'); refuses('validate run swap',lambda:B.validate(t))
refuses('parse foreign object',lambda:B.parse(b'q8/8865619b/05b8ac69_m200.tar 7 '+b'a'*64+b'\n',b))
refuses('parse claim other step',lambda:B.parse(b'q8/8865619b/05b8ac69_mstopB.tar 7 '+b'a'*64+b'\n',s,b'm334\n'))
B.parse(b'q8/8865619b/05b8ac69_mstopB.tar 7 '+b'a'*64+b'\n',s,b'm333\n')
out=Path(sys.argv[2]); out.mkdir(exist_ok=True); i=[0]
def d(): i[0]+=1; return out/str(i[0])
refuses('469 main+a7',lambda:L.prepare('a000000002',d(),544,run='469ddece',generation='mstop',families=['main','a7'],types='direct'))
refuses('469 main',lambda:L.prepare('a000000002',d(),544,run='469ddece',generation='mstop',families=['main']))
refuses('R1 default families',lambda:L.prepare('a000000002',d(),200,run='673bc60f'))
refuses('R1 a7+forward',lambda:L.prepare('a000000002',d(),200,run='673bc60f',families=['a7','forward']))
c=L.prepare('a000000002',d(),200,run='673bc60f',families=['main','a7'],types='direct'); L.validate_request(c)
assert c['spec']['export_binding']==B.expected('673bc60f',200) and c['spec']['artifact']['path'].endswith('/ap/8865619b/runs/673bc60f/m200/artifact.json')
c2=L.prepare('a000000002',d(),137,run='673bc60f',generation='mstopC',families=['a7']); L.validate_request(c2)
c3=L.prepare('a000000002',d(),600,run='05b8ac69',families=['main']); L.validate_request(c3)
# tamper: change export_binding run in plan -> refused
import copy
x=copy.deepcopy(c); x['spec']['export_binding']['run']='05b8ac69'; x['plan_sha256']=L.canonical(x['spec']); refuses('plan run swap',lambda:L.validate_request(x))
x=copy.deepcopy(c); x['spec']['step']=400; x['spec']['export_binding']=B.expected('05b8ac69',400); x['plan_sha256']=L.canonical(x['spec']); refuses('artifact path mismatch',lambda:L.validate_request(x))
with patch.object(E.T,'writable',side_effect=Path):
    for run,step in [('05b8ac69',200),('673bc60f',201),('673bc60f',544),('469ddece',200),('deadbeef',100)]:
        refuses(f'stage {run} {step}',lambda:E.stage_export(NS(root=str(d()),run=run,step=step)))
    refuses('logical cross',lambda:E.logical_artifact(None,str(L.J.FSW/'ap/8865619b/runs/05b8ac69/m200/artifact.json'),200))
print('refused',len(ok),'WRONGLY ADMITTED',bad)
