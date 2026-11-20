from common import *
import subprocess
from student_pilot.r1_persisted import scope
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
records=[]
for name in ('q','n','n_go','qd'):
 sys.path.insert(0,str(kit(name)/'b'))
 for mod in ('cs','sv','rv','z'):sys.modules.pop(mod,None)
 import cs
 for case in ('clean','protected','outside'):
  root=D/'census_bytes'/(name+'_'+case)
  cfg=J.load(root/'cfg.json') if case=='clean' else J.load(D/'census_bytes'/(name+'_clean')/'cfg.json')
  if case!='clean':
   # Rebuild the original case's pinned configuration from its receipt data.
   cfg=J.load(D/'census_final'/(name+'_clean')/'cfg.json')
   cfg['streams']={s:dict(path=str(root/(s+'.json')),sha256=J.sha(root/(s+'.json'))) for s in cs.STREAMS}
   cfg['preparation']=dict(path=str(root/'prep.json'),sha256=J.sha(root/'prep.json'))
  active=dict(paths);folder=root/'p/q/u'
  if folder.exists():active.update({p.name:str(p) for p in folder.iterdir()})
  refusal=None
  with scope(active):
   try:cs.publish(root/'kit',root,cfg,'91')
   except ValueError as e:refusal=str(e)
  expected=None if case=='clean' or name=='qd' else ('R1_PROTECTED_ROOM_ROWS:pointing' if case=='protected' else 'R1_PROTECTED_LIST_KEY_NOT_PROTECTED:pointing')
  assert refusal==expected,(name,case,refusal)
  live=root/'target/o/91/live/c4.json';report=root/'c5.json';assert J.sha(report)==J.sha(live)
  records.append(dict(kit=name,case=case,refusal=refusal,status=J.load(report)['status'],byte_identical_publication=True))
  if case!='clean':continue
  k=root/'sealed'
  for rel in ('b/cs.py','b/sv.py','b/h.py','b/rv.py'):replace(k/rel,(kit(name)/rel).read_bytes())
  for rel in ('BUILD.json','SHA256SUMS.txt'):replace(k/rel,(k/rel).read_bytes())
  reseal(k)
  def invoke(expected):
   p=subprocess.run([sys.executable,'-B','-s',str(k/'b/h.py'),str(root/'p'),str(root/'verified_h.json')],capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'91'})
   if expected:assert p.returncode and expected in p.stderr,(name,expected,p.stderr)
   else:assert p.returncode==0,(name,p.stderr)
  invoke(None)
  assert J.sha(root/'target/o/91/live/h0.json')==J.load(root/'verified_h.json')['r1_training']['host_receipt']['sha256']
  raw=report.read_bytes()
  for mutation,code in (('identity','R1_CENSUS_IDENTITY_DIFFERS'),('store','R1_CENSUS_STORE_PINS_DIFFER:pointing')):
   value=json.loads(raw)
   if mutation=='identity':value['config_identity']='0'*64
   else:value['streams']['pointing']['store_pins']['count']+=1
   body=json.dumps(value).encode();report.write_bytes(body);live.write_bytes(body)
   invoke(code);report.write_bytes(raw);live.write_bytes(raw)
   records.append(dict(kit=name,case='h_'+mutation,refusal=code))
  retained=root/'c5_missing_test.json';report.rename(retained);invoke('R1_CENSUS_RECEIPT_MISSING');retained.rename(report)
  invoke(None);records.append(dict(kit=name,case='h_missing',refusal='R1_CENSUS_RECEIPT_MISSING'))
J.write(D/'CENSUS_VERIFIED_TESTS.json',dict(status='PASS',records=records,keys=320,kits={n:J.seal(kit(n)) for n in ('q','n','n_go','qd')},native_complete_populations=True))
print('Final sealed census, identity/store/missing binding and exact publication PASS',len(records))
