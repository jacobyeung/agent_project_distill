import base64,hashlib,json,sys,tarfile
from pathlib import Path
if sys.version_info < (3,12):raise RuntimeError('Python 3.12 or newer required')
def read(p):
 v=json.loads(p.read_text());r=base64.b64decode(v['payload'],validate=True)
 if hashlib.sha256(r).hexdigest()!=v['sha256']:raise ValueError('E01')
 return json.loads(r)
kit=Path(__file__).resolve().parents[1];control=read(kit/'k/a.json')
if len(sys.argv) not in (3,4) or sys.argv[1] not in ('p','t','q'):raise ValueError('E02')
if (sys.argv[1]=='q') != (len(sys.argv)==4):raise ValueError('E02')
if sys.argv[1]=='t' and control['GO'] is not True:raise ValueError('E03')
root=Path(sys.argv[2]).resolve()
if root==Path('/tmp') or not root.is_relative_to(Path('/tmp')):raise ValueError('E06')
if root.exists() and any(root.iterdir()):raise ValueError('E04')
root.mkdir(parents=True,mode=0o700,exist_ok=True)
src=control['source'];p=kit/src['path']
if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256']:raise ValueError('E05')
with tarfile.open(p) as t:t.extractall(root/'s',filter='data')
sys.path.insert(0,str(root/'s'))
from launch_r1.build import verify
verify(kit)
if sys.argv[1]=='q':
 from launch_r1.production_proof import run
 from student_pilot.p3_provenance import load
 r=run(load(sys.argv[3]),root/'q')
 print(json.dumps({'ok':r['status']=='ADMIT'}))
 sys.exit(0 if r['status']=='ADMIT' else 1)
from launch_r1.entry import frame_host,admit,create_job_tmp
cfg=read(kit/'k/c.json')
if sys.argv[1]=='p':
 request=read(kit/'k/h.json')
 job_tmp=root/'j'
 token=create_job_tmp(job_tmp)
 request['job_tmp']=str(job_tmp)
 r=frame_host(cfg,job_tmp/'p',request,job_tmp_token=token)
 print(json.dumps({'ok':r['status']=='PASS'}))
 sys.exit(0 if r['status']=='PASS' else 1)
admit(cfg)
from student_pilot.carrier_c1_run import train
train(cfg)
