from pathlib import Path
from copy import deepcopy
import importlib.util,json,os,runpy,shutil,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24h';R=Path('/tmp/q_22c714e1');F=D/'receipt_fixture'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'out'),str(L/'work/build24f')]
import joblib as J
from kit24f import reseal
from arm_go import arm,scanner,capsule
from student_pilot.carrier_c1_run import identity
from student_pilot.p3_provenance import pinned,load
from student_pilot import r1_persisted as P,r1_rooms as Rooms,r1_direction_twins as Twins
from launch_r1 import entry
cfg=load(R/'p2/q/h/config.json');value=identity(cfg)
syn=load(L/'work/build24/proofs/capacity/TWIN_BOUNDARY.json')['pins']
Twins.ROWS=syn['rows']['sha256'];Twins.BINDING=syn['binding']['sha256'];Twins.ALIASES=syn['aliases']['sha256'];Rooms.STORE=syn['source_database']['sha256']
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
q=load(R/'p2/q/RESULT.json');assert q['status']=='ADMIT'
J.write(R/'p/q/RESULT.json',q)
host=dict(status='PASS',config_identity=value,assertions=dict.fromkeys(entry.ASSERTIONS,True),loader_audit=q['audit'],scope='CPU fixture only')
review=dict(verdict='PASS',config_identity=value,evidence=dict(checks={'fixture_canary':'PASS'},hashes={'canary':J.sha(R/'p2/q/RESULT.json')},reviewer_session='fixture-only-not-n_review1'))
review_path=F/'review.json';J.write(review_path,review)
armed=F/'armed';record=arm(review_path,value,L/'out/kit_n_go',L/'work/build24/kits/n',armed,F/'upload',scanner(L))
assert record['decoded_scan']=='PASS' and record['total_files']==4
normal=F/'normal';shutil.copytree(L/'work/build24/kits/n',normal)
legacy=F/'legacy';shutil.copytree(L/'out/kit_n_go',legacy);(legacy/'b/h.py').write_bytes((L/'attic/build24h/work/build24/kits/n/b/h.py').read_bytes());reseal(legacy)
records=[]
cases=[('host missing','R1_HOST_RECEIPT_MISSING'),('host FAIL','R1_HOST_RECEIPT_NOT_PASS'),('host identity','R1_HOST_IDENTITY_DIFFERS'),('host assertions','R1_HOST_ASSERTIONS_INCOMPLETE'),('host audit','R1_HOST_LOADER_AUDIT_INCOMPLETE'),('review missing','R1_REVIEW_RECEIPT_MISSING'),('review sha','R1_REVIEW_RECEIPT_CHANGED'),('review identity','R1_REVIEW_IDENTITY_DIFFERS'),('review FAIL','R1_REVIEW_RECEIPT_NOT_PASS')]
for version,k in [('before',legacy),('after',armed),('normal',normal)]:
 for i,(case,expected) in enumerate(cases):
  actual_host=deepcopy(host);actual_review=deepcopy(review)
  p=R/'p/host.json'
  if p.exists():p.rename(R/'p'/('host_saved_'+version+'_'+str(i)+'.json'))
  if case=='host FAIL':actual_host['status']='FAIL'
  if case=='host identity':actual_host['config_identity']='0'*64
  if case=='host assertions':actual_host['assertions'].pop('disk_plan')
  if case=='host audit':actual_host['loader_audit']['complete']=False
  if case!='host missing':J.write(p,actual_host)
  if case=='review identity':actual_review['config_identity']='0'*64
  if case=='review FAIL':actual_review['verdict']='FAIL'
  raw=(json.dumps(actual_review,sort_keys=True,indent=2)+'\n').encode();h=__import__('hashlib').sha256(raw).hexdigest()
  staged=R/'u'/h;staged.parent.mkdir(exist_ok=True);staged.write_bytes(raw)
  control=J.load(k/'k/a.json');control['review']={'path':'u/'+h,'sha256':h}
  if case=='review missing':control.pop('review')
  if case=='review sha':staged.write_bytes(raw+b' ')
  (k/'k/a.json').write_bytes(capsule(control));reseal(k)
  output=R/('v_'+version+'_'+str(i)+'.json');refusal=None;t_reachable=False
  try:
   with patch.object(sys,'argv',[str(k/'b/h.py'),str(R/'p'),str(output)]):runpy.run_path(str(k/'b/h.py'),run_name='__main__')
   t_reachable=True
  except ValueError as e:refusal=str(e)
  if version=='before':assert refusal is None and t_reachable
  else:assert refusal==expected and not output.exists(),(version,case,refusal)
  records.append(dict(version=version,case=case,refusal=refusal,t_reachable=t_reachable))
# Re-arm with the immutable fixture receipt; the native admit() is not mocked.
passkit=F/'pass_armed';record=arm(review_path,value,L/'out/kit_n_go',L/'work/build24/kits/n',passkit,F/'pass_upload',scanner(L))
J.write(R/'p/host.json',host)
row=next(r for r in record['files'] if r['name'].startswith('u/'));shutil.copyfile(row['local_path'],R/row['name'])
with patch.object(sys,'argv',[str(passkit/'b/h.py'),str(R/'p'),str(R/'v.json')]):runpy.run_path(str(passkit/'b/h.py'),run_name='__main__')
final=J.load(R/'v.json')
with P.scope(aliases),P.scope(cfg['r1_training']['persisted_files']):
 assert entry.admit(final)==0
assert identity(final)==value
for key in ('host_receipt','review'):assert Path(pinned(final['r1_training'][key])).is_relative_to(R/'p')
# arm_go refuses bad verdict and identity before creating an output directory.
for case,mutation,expected in [('FAIL',{'verdict':'FAIL'},'R1_REVIEW_RECEIPT_NOT_PASS'),('identity',{'config_identity':'0'*64},'R1_REVIEW_IDENTITY_DIFFERS')]:
 p=F/(case+'.json');J.write(p,dict(review,**mutation))
 try:arm(p,value,L/'out/kit_n_go',L/'work/build24/kits/n',F/('bad_'+case),F/('bad_upload_'+case),scanner(L))
 except ValueError as e:assert str(e)==expected
 else:raise AssertionError('arm accepted '+case)
 assert not (F/('bad_'+case)).exists()
J.write(D/'RECEIPT_TESTS.json',dict(status='PASS',records=records,native_admit=0,fixture_identity=value,armed_files=record['total_files'],armed_scan=record['decoded_scan'],production_host_receipt=False,production_review=False))
print('Receipt refusals, fixture arming and native admit PASS')
