from pathlib import Path
import importlib.util,runpy,json,hashlib,base64,time
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z5';K=J/'out/kit_n';p=D/'range_probe.bin';p.write_bytes(b'q'*(256<<10))
s=importlib.util.spec_from_file_location('pc_range',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
G=runpy.run_path(str(K/'b/gc.py'));result={}
for mode in ('before','after'):
 state=dict(sent=0,lost=False,data=b'')
 class Reply:
  status=200
  def read(self):return json.dumps(dict(size=len(state['data']),md5Hash=base64.b64encode(hashlib.md5(state['data']).digest()).decode(),generation='1',name='q9/range')).encode()
 class Connection:
  def __init__(self,*a,**kw):self.data=b''
  def putrequest(self,*a):pass
  def putheader(self,*a):pass
  def endheaders(self):pass
  def close(self):pass
  def send(self,data):self.data+=data;state['sent']+=len(data)
  def getresponse(self):
   if self.data:
    state['data']=self.data
    if not state['lost']:state['lost']=True;raise OSError('lost final reply')
   if not state['data']:
    class Pending:
     status=308
     def read(self):return b''
     def getheader(self,n):return None
    return Pending()
   return Reply()
 upload=(lambda:G['upload']('https://local.invalid/q',p,0,p.stat().st_size,'q9/range')) if mode=='before' else (lambda:C.upload_range('https://local.invalid/q',p,0,p.stat().st_size,'q9/range',256<<10,time.time()+20))
 with patch.object(C.http.client,'HTTPSConnection',Connection):
  try:upload()
  except OSError:pass
  else:raise AssertionError('lost response not injected')
  row=upload();assert row['bytes']==p.stat().st_size
 result[mode]=dict(sent=state['sent'],expected=p.stat().st_size,no_resend=state['sent']==p.stat().st_size)
assert not result['before']['no_resend'] and result['after']['no_resend']
(D/'RESUME_BEFORE_AFTER.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
