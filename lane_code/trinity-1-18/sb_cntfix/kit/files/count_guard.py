"""Pinned dev authorization, completion validation, and one-look registration."""
import fcntl, gzip, hashlib, json, os, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=Path('/scratch/jjyeung/orch_n30/sb_cntfix')
LEDGER=WORK/'state'
AUTH_SHA='fab9576c4f224544410e7e8c0cb3c5297d568faf6fa52f995dce3d4a5f7bc28e'
MRA_SHA='f0730b4039a3bc5768866ae39cd13ba0d69f04dd99be17fcc353d85221b258f9'
ITEM_SHA='b20e72603589aa8c900f993a83d670e880dd8a9b151cb5c300b02bbf00a3398a'
CONTRACT={'joint_floor':0.2,'cap':10,'prompts':'teacher_names_verbatim_normalized','mask_threshold':0.5,'resolution':1008,'dtype':'bf16','checkpoint_sha256':'9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name(p.name+'.tmp.%s'%os.getpid())
 with tmp.open('x') as f:json.dump(d,f,sort_keys=True,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
 os.replace(str(tmp),str(p))
def exclusive(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,sort_keys=True,allow_nan=False);f.flush();os.fsync(f.fileno())
def scratch(p,exists=True):
 p=Path(p).resolve(strict=exists)
 if not str(p).startswith('/scratch/'):raise ValueError('resolved path is not scratch: '+str(p))
 return p
def output(p):
 p=scratch(p,False)
 if WORK not in p.parents:raise ValueError('output must remain in authorized workspace')
 return p
def pins():
 for p,h in read(HERE/'BACKEND_PINS.json')['inputs_sha256'].items():
  if sha(p)!=h:raise ValueError('backend source pin differs: '+p)
 return {str(p):sha(p) for p in sorted(HERE.glob('*.py'))}|{str(HERE/n):sha(HERE/n) for n in ('FROZEN_CONFIG.json','DEV_AUTHORIZATION.json','MRA_SOURCE.json','BACKEND_PINS.json','MRA_BOUNDARIES.json')}
def config():
 if sha(HERE/'official_vsi_mra.py')!=MRA_SHA:raise ValueError('official metric source changed')
 c=read(HERE/'FROZEN_CONFIG.json')
 if c['training_split']!='train':raise ValueError('training receipt required')
 return c
def items(p,setname='R0-dev'):
 p=scratch(p)
 # Check authorization before parsing a caller-supplied item file.
 if sha(p)!=ITEM_SHA:raise ValueError('item file is not the pinned dev allowlist')
 if setname not in ('R0-dev','dev-S1'):raise ValueError('official items prohibited')
 rows=[json.loads(l) for l in p.read_text().splitlines()]
 return [x for x in rows if x['set']==setname]
def manifest(p):
 p=scratch(p)
 if sha(HERE/'DEV_AUTHORIZATION.json')!=AUTH_SHA:raise ValueError('allowlist pin changed')
 m=read(p);auth=read(HERE/'DEV_AUTHORIZATION.json')
 if m.get('schema')!='owngrd-teacher-manifest-v1' or m.get('source',{}).get('set')!='R0-dev':raise ValueError('only pinned R0-dev captures are runnable; dev-S1 frame authority MISSING')
 if m['source'].get('items_sha256')!=ITEM_SHA or m['captures']!=auth['captures']:raise ValueError('manifest differs from pinned capture/frame/category allowlist')
 for c in m['captures']:
  for f in c['frames']:
   if str(scratch(f['path']))!=f['path']:raise ValueError('frame path is not canonical scratch path')
 return m

def binding(mp,settings,stub):
 m=manifest(mp); ip=HERE/'COUNT_ITEMS_535.jsonl';rows=items(ip)
 return dict(evaluation_category='counting',set='R0-dev',item_ids=sorted(x['id'] for x in rows),captures=[c['canonical'] for c in m['captures']],manifest_sha256=sha(mp),items_sha256=sha(ip),config_sha256=sha(HERE/'FROZEN_CONFIG.json'),code_sha256=pins(),contract_sha256=digest(CONTRACT),settings_sha256=sha(settings) if settings else digest({'stub':True}),stub=bool(stub))
def ledger(stub):
 LEDGER.mkdir(exist_ok=True)
 return LEDGER/('stub-counting.json' if stub else 'R0-dev-counting.json')
def register(mp,settings,stub,deadline,budget):
 if not stub and config()['training_decision']!='ACCEPT_FOR_COMPARISON':raise ValueError('K1 training rejects this proposal; no real dev comparison authorized')
 if not (time.time()<deadline and 0<budget<=1800):raise ValueError('future absolute deadline and budget <=1800 seconds required')
 b=binding(mp,settings,stub)
 exclusive(ledger(stub),dict(binding=b,absolute_deadline=deadline,budget_seconds=budget,registered_unix=time.time(),inputs_sha256={str(mp):sha(mp),**pins()}))
 return b

def registered(mp,settings,stub):
 p=ledger(stub);r=read(p)
 if r['binding']!=binding(mp,settings,stub):raise ValueError('registration binding changed')
 return r

def consume(mp,settings,stub):
 r=registered(mp,settings,stub)
 # Stable evaluation-category key, independent of output root/config; consume before reading teacher results.
 exclusive(ledger(stub).with_suffix('.consumed.json'),dict(binding=r['binding'],consumed_unix=time.time(),inputs_sha256={str(ledger(stub)):sha(ledger(stub))}))
 return r

def validate_done(root,c,mp,settings,stub):
 d=Path(root)/c['canonical'].replace('/','__');dp=d/'DONE.json';tp=d/'teacher.json.gz'
 done=read(dp)
 expected=dict(canonical=c['canonical'],teacher_sha256=sha(tp),frames=32,names=len(c['names']),manifest_sha256=sha(mp),contract_sha256=digest(CONTRACT),settings_sha256=sha(settings) if settings else digest({'stub':True}),stub=bool(stub),config_sha256=sha(HERE/'FROZEN_CONFIG.json'),code_sha256=pins())
 for k,v in expected.items():
  if done.get(k)!=v:raise ValueError('invalid DONE '+str(dp)+' field '+k)
 with gzip.open(tp,'rt') as f:t=json.load(f)
 names=[n['name'] for n in c['names']]
 if t.get('stub') is not bool(stub) or t.get('contract')!=CONTRACT:raise ValueError('teacher stub/contract mismatch')
 if t.get('frame_indices')!=[f['index'] for f in c['frames']] or t.get('frame_sha256')!=[f['sha256'] for f in c['frames']] or t.get('frame_slots')!=list(range(32)):raise ValueError('teacher frame provenance mismatch')
 if t.get('phrases')!=names or t.get('roles')!={n:'gt' for n in names} or set(t['frames'])!={str(i) for i in range(32)}:raise ValueError('teacher category/frame coverage mismatch')
 for fr in t['frames'].values():
  if set(fr['phrases'])!=set(names):raise ValueError('incomplete category coverage')
  for ph in fr['phrases'].values():
   if not isinstance(ph.get('instances'),list):raise ValueError('missing instances')
 return t,{str(dp):sha(dp),str(tp):sha(tp)}

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--register',action='store_true',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--settings');ap.add_argument('--stub',action='store_true');ap.add_argument('--deadline-unix',type=float,required=True);ap.add_argument('--budget-seconds',type=float,default=1800)
 a=ap.parse_args();register(a.manifest,a.settings,a.stub,a.deadline_unix,a.budget_seconds);print('registered counting comparison')
