import base64,hashlib,json,sys,tarfile
from pathlib import Path
def read(p):
 v=json.loads(p.read_text());r=base64.b64decode(v['payload'],validate=True)
 if hashlib.sha256(r).hexdigest()!=v['sha256']:raise ValueError('E01')
 return json.loads(r)
kit=Path(__file__).resolve().parents[1];control=read(kit/'k/a.json')
if len(sys.argv)!=3 or sys.argv[1] not in ('p','t'):raise ValueError('E02')
if sys.argv[1]=='t' and control['GO'] is not True:raise ValueError('E03')
root=Path(sys.argv[2]).resolve()
if root.exists() and any(root.iterdir()):raise ValueError('E04')
root.mkdir(parents=True,mode=0o700,exist_ok=True)
src=control['source'];p=kit/src['path']
if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256']:raise ValueError('E05')
with tarfile.open(p) as t:t.extractall(root/'s',filter='data')
sys.path.insert(0,str(root/'s'))
from launch_r1.build import verify
verify(kit)
from launch_r1.entry import frame_host,admit
cfg=read(kit/'k/c.json')
if sys.argv[1]=='p':
 r=frame_host(cfg,root/'p',read(kit/'k/h.json'))
 print(json.dumps({'ok':r['status']=='PASS'}))
 sys.exit(0 if r['status']=='PASS' else 1)
admit(cfg)
from student_pilot.carrier_c1_run import train
train(cfg)
