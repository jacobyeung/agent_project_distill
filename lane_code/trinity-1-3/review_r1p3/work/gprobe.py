import sys,json,copy,hashlib
from pathlib import Path
kit=Path(sys.argv[1]);tools=Path(sys.argv[2])
sys.path.insert(0,str(tools));from derive_deployment import validate_evidence
sys.path.insert(0,str(kit/'b'))
import g
called=[]
g.persistent_launch=lambda *a:called.append(a[3]) or 'stubbed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wr(p,v):p.write_text(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')
print('g.check full (persistence stubbed):',g.check(kit,{},'p'),called)
validate_evidence(kit);print('validate_evidence: PASS')
launch=json.loads((kit/'k/launch.json').read_text())
muts=[('review.json','config_sha256','0'*64),('staging.json','config_sha256','0'*64),('staging.json','status','FAIL'),
 ('review.json','admission_scope','x'),('archive.json','tree_sha256','0'*64),('archive.json','status','PENDING'),
 ('archive.json','location','/scratch/x'),('4.json','allow_until_utc','2020-01-01T00:00:00Z'),('4.json','config_sha256','0'*64),
 ('4.json','source_revision','x'),('4.json','modes',['t']),('staging.json','missing',None),('review.json','verdict','pass'),
 ('review.json','admission_contract_sha256','0'*64),('staging.json','project_community_write_bytes',1)]
for f,k,v in muts:
    p=kit/'k'/f;raw=p.read_bytes();r=json.loads(raw);r[k]=v;wr(p,r);alt=copy.deepcopy(launch)
    if f!='4.json':alt[f[:-5]]['sha256']=sha(p)
    wr(kit/'k/launch.json',alt)
    res=[]
    for name,fn in (('g',lambda:g.check(kit,{},'p')),('v',lambda:validate_evidence(kit))):
        try:fn();res.append(name+'=ACCEPT')
        except Exception as e:res.append(name+'=REFUSE')
    print(f,k,repr(v)[:20],*res)
    p.write_bytes(raw);wr(kit/'k/launch.json',launch)
# cfg.admission pin vs review pin: review.json mutated without updating cfg.admission
p=kit/'k/review.json';raw=p.read_bytes();r=json.loads(raw);r['note']='x';wr(p,r);alt=copy.deepcopy(launch);alt['review']['sha256']=sha(p);wr(kit/'k/launch.json',alt)
res=[]
for name,fn in (('g',lambda:g.check(kit,{},'p')),('v',lambda:validate_evidence(kit))):
    try:fn();res.append(name+'=ACCEPT')
    except Exception:res.append(name+'=REFUSE')
print('review.json re-pinned without cfg.admission',*res)
p.write_bytes(raw);wr(kit/'k/launch.json',launch)
