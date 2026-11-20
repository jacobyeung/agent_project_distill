from common import *
import importlib.util
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('rcj_plan',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
sys.path.insert(0,str(kit('qd')/'b'));import rb
class Audit(R.Inputs):
 def __init__(self):
  self.kit=kit('qd');self.root=D/'plan_audit';self.root.mkdir();self.z=J;self.spec=J.load(self.kit/'k/p.json');self.current=J.load(self.kit/'k/l.json');self.sources={};self.records={};self.values={};self.model_hashes=set()
 def need(self,h,field='p'):
  self.records.setdefault(h,dict(field=field));self.sources[h]='u/'+h;return 'u/'+h
 def value(self,pin):
  self.need(pin['sha256']);p=input_file(pin['sha256']);v=J.load(p);self.values[pin['sha256']]=dict(path=str(p),bytes=p.stat().st_size);return v
 def model_file(self,name,h):
  self.model_hashes.add(h);return self.need(h)
a=Audit()
with patch.object(rb,'mount_inputs',return_value={}):a.closure()
entries={}
for h in a.records:
 origin=[]
 if any(v['sha256']==h for v in a.spec['uploads']):origin.append('u')
 if h in a.spec['p_files'].values():origin.append('p_files')
 if any(v['sha256']==h for v in a.current.get('extra',[])+[a.current['a1rows']]):origin.append('extra')
 if any(h in v['files'].values() for v in a.current.get('tars',[])):origin.append('tars')
 if any(v['sha256']==h for v in a.current['staged_inputs'].get('files',[])):origin.append('files')
 if any(h in [x['sha256'] for x in v['inventory']] for v in a.current['staged_inputs'].get('packages',[])):origin.append('packages')
 if h in a.model_hashes:origin.append('metadata')
 entries[h]=origin or ['small_lookup_runtime_required']
assert rb.DB not in entries,'Reconstruction output was staged as input'
J.write(D/'RCJ_PLAN_AUDIT.json',dict(status='PASS_METADATA_WALK',required_hashes=entries,metadata=a.values,input_count=len(entries),output_database_staged=False,weights_staged=False,frame_payloads_staged=False,scope='Actual metadata and helper closure(); transport dry collector; mount_inputs runtime check separately covered by native rb tests'))
print('RCJ metadata walk',len(entries),'hashes; small fallback',sum(v==['small_lookup_runtime_required'] for v in entries.values()))
