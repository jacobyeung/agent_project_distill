"""R3 local regression tests. No transfer, scheduler, or production execution."""
import copy,hashlib,importlib.util,io,json,shlex,subprocess,tarfile,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parent;W=R.parent
H='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'
N=21583032320

def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def write(p,v):p.write_text(json.dumps(v,sort_keys=True))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class R3(unittest.TestCase):
 def test_real_preparation(self):
  for label in ('A','B'):
   m=load(R/label/'fill_export.py','fill_'+label);b=m.reviewed_binding()
   artifact={k:b[k] for k in ('config_sha256','base_identity','frame_layout')}
   pins,_=m.preparation(W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json',W/'in/s1/s1_receipt.json',W/'in/data_receipt.json',artifact)
   self.assertEqual({k:v['sha256'] for k,v in pins.items()},b['preparation_sha256'])

 def bind_case(self,label,field,value):
  m=load(R/label/'fill_export.py','fill_'+label);b=m.reviewed_binding()
  a=SimpleNamespace(object=b['object'],step=200,lineage='SFT')
  e=dict(member_directory='m200');artifact={k:b[k] for k in ('step','config_sha256','base_identity','frame_layout')}
  artifact.update(heads=dict(path='/run/673bc60f/m200/heads.pt'),full_weights=dict(path='/run/673bc60f/m200/full_weights/full_weights.json'))
  prep={k:dict(sha256=v) for k,v in b['preparation_sha256'].items()}
  archive=dict(sha256=H,parts=[dict(bytes=N)])
  m.bind_review(a,e,artifact,archive,prep,b)
  if field=='sha256':archive[field]=value
  else:archive['parts'][0]['bytes']=value
  with self.assertRaisesRegex(ValueError,'whole-tar'):m.bind_review(a,e,artifact,archive,prep,b)
  # A caller cannot authorize a different export by mutating its binding too.
  b['archive_sha256']=archive['sha256'];b['archive_bytes']=archive['parts'][0]['bytes']
  with self.assertRaisesRegex(ValueError,'whole-tar'):m.bind_review(a,e,artifact,archive,prep,b)

 def receipt_case(self,label,field,value):
  m=load(R/label/'fill_export.py','fill_'+label)
  root=Path(tempfile.mkdtemp(prefix='done_',dir=R/'test_tmp'));p=root/'done'
  p.write_bytes((W/'in/gcs_673bc60f_m200.done.txt').read_bytes());m.receipt_review(p)
  fields=p.read_text().split();fields[field]=str(value);p.write_text(' '.join(fields)+'\n')
  with self.assertRaisesRegex(ValueError,'whole-tar'):m.receipt_review(p)

 def fetch_case(self,label,field,value):
  m=load(R/label/'fetch_return.py','fetch_'+label)
  root=Path(tempfile.mkdtemp(prefix='fetch_',dir=R/'test_tmp'));package=root/'package';package.mkdir();pool=root/'pool';pool.mkdir()
  cfg=dict(token='abcdef0123456',pool=str(pool));token=cfg['token']+'00000001';source=pool/token;source.mkdir()
  raw=json.dumps(cfg,sort_keys=True).encode()
  with tarfile.open(package/'0.tgz','w:gz') as t:
   entry=tarfile.TarInfo('9.json');entry.size=len(raw);t.addfile(entry,io.BytesIO(raw))
  plan=hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  write(package/'0.json',dict(token=cfg['token'],payload_sha256=sha(package/'0.tgz'),plan_sha256=plan))
  (package/'a').mkdir();(package/'3.py').write_bytes((R/label/'package/3.py').read_bytes());(package/'a/7.py').write_bytes((R/label/'fetch_return.py').read_bytes())
  write(package/'PACKAGE.json',dict(files={n:sha(package/n) for n in ('0.tgz','0.json','3.py','a/7.py')}))
  archive=source/'result.tar.gz';archive.write_bytes(b'local fetch fixture')
  exit_value=dict(plan_sha256=plan,token=token,job='1',synthetic=False,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),complete=True,status='COMPLETE')
  def receipts(v):
   write(source/'EXIT.json',v)
   receipt=dict(plan_sha256=plan,token=token,job='1',returned=True,channels=dict(pool=dict(verified=True,files={n:dict(bytes=(source/n).stat().st_size,sha256=sha(source/n)) for n in ('EXIT.json','result.tar.gz')})))
   write(source/'RETURN_RECEIPT.json',receipt)
  receipts(exit_value)
  m.fetch(package,token,root/'valid')
  self.assertEqual((root/'valid/0.tgz').read_bytes(),archive.read_bytes())
  bad=dict(exit_value);bad[field]=value;receipts(bad)
  with self.assertRaises(ValueError):m.fetch(package,token,root/'refused')
  self.assertFalse((root/'refused').exists())
  result=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(package/'3.py'),'fetch','--return-token',token,'--out',str(root/'wrapper_refused')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  self.assertNotEqual(result.returncode,0);self.assertIn(b'ValueError:',result.stderr);self.assertFalse((root/'wrapper_refused').exists())
  # Failed-but-authentic returns remain available for partial diagnosis.
  receipts(dict(exit_value,complete=False,status='FAILED'));m.fetch(package,token,root/'partial')

 def test_fetch_entrypoints_are_sealed(self):
  for label in ('A','B'):
   d=R/label;s=(d/'o_fetch.sh').read_text()
   self.assertIn('"$P/a/7.py"',s);self.assertNotIn('3.py fetch',s)
   with tarfile.open(d/'1.tgz') as t:
    self.assertEqual(t.extractfile('a/7.py').read(),(d/'fetch_return.py').read_bytes())
   self.assertEqual(json.loads((d/'PACKAGE.json').read_text())['files']['a/7.py'],sha(d/'fetch_return.py'))

 def test_retry_settings_and_failure_stops(self):
  s=(R/'A/o_pullfill.sh').read_text();line=next(x.strip() for x in s.splitlines() if x.strip().startswith('gsutil '));args=shlex.split(line)
  for setting in ('Boto:num_retries=0','Boto:metadata_service_num_attempts=1','GSUtil:parallel_process_count=1','GSUtil:parallel_thread_count=1','GSUtil:sliced_object_download_threshold=0','GSUtil:sliced_object_download_max_components=1'):self.assertIn(setting,args)
  self.assertNotIn('-m',args);self.assertEqual(s.count('gsutil '),1);self.assertNotIn('gsutil',(R/'B/o_pullfill.sh').read_text())
  root=Path(tempfile.mkdtemp(prefix='retry_',dir=R/'test_tmp'))
  loop=s[s.index('for i in 0 1 2 3; do'):s.index('\ndone',s.index('for i in 0 1 2 3; do'))+5]
  script='set -euo pipefail\nE='+shlex.quote(str(root))+'\nOBJECT=fixture\ngsutil() { printf "%s\\n" "$*" >> "$E/calls"; return 7; }\n'+loop
  r=subprocess.run(['bash','-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  self.assertEqual(r.returncode,7);self.assertEqual(len((root/'calls').read_text().splitlines()),1)
  for i in range(4):self.assertFalse((root/str(i)).exists())

for label in ('A','B'):
 for name,field,value in [('wrong_sha_same_prefix','sha256',H[:8]+'0'*56),('wrong_prefix','sha256','0'*64),('wrong_bytes','bytes',N-1)]:
  setattr(R3,'test_bind_'+label+'_'+name,lambda self,l=label,f=field,v=value:self.bind_case(l,f,v))
 for name,field,value in [('wrong_sha_same_prefix',2,H[:8]+'0'*56),('wrong_prefix',2,'0'*64),('wrong_bytes',1,N-1),('wrong_object',0,'q8/wrong.tar')]:
  setattr(R3,'test_done_'+label+'_'+name,lambda self,l=label,f=field,v=value:self.receipt_case(l,f,v))
 for field,value in [('plan_sha256','0'*64),('token','abcdef012345600000002'),('synthetic',True),('archive_bytes',1),('archive_sha256','0'*64),('status','SYNTHETIC')]:
  setattr(R3,'test_fetch_'+label+'_'+field,lambda self,l=label,f=field,v=value:self.fetch_case(l,f,v))
if __name__=='__main__':unittest.main(verbosity=2)
