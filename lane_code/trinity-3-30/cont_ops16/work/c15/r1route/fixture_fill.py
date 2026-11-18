"""Small local export fixture; production pins are never relaxed."""
from pathlib import Path
import hashlib,io,json,tarfile,copy,subprocess,sys,tempfile
W=Path(__file__).resolve().parent
BASE_ART=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/a5d2d909067/fetched/x/metadata/EXPORT_ARTIFACT.json')
H1=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/in/h1_1_run_inputs/node_local/prepared/s1_receipt.json')
def pin(raw):return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def tarbytes(files):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as t:
  for n,raw in sorted(files.items()):
   m=tarfile.TarInfo(n);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
 return b.getvalue()
def fixture(kind='b1',bad=None):
 root=Path(tempfile.mkdtemp(prefix='f_',dir=W/'tmp'));p=root/'p';(p/'a').mkdir(parents=True)
 original=W/'out'/kind;binding=copy.deepcopy(json.loads((W/'out/EXPORT_BINDING.json').read_text()))
 cfg=json.loads((W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json').read_text());data=json.loads((W/'in/inputs/data_receipt.json').read_text())
 receipts=list((W/'in/s1').glob('*.json')) if (W/'in/s1').exists() else []
 real=next((v for v in receipts if pin(v.read_bytes())['sha256']==binding['preparation_sha256']['receipt']),None)
 if real:
  receipt=real.read_bytes();config_raw=(W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json').read_bytes();data_raw=(W/'in/inputs/data_receipt.json').read_bytes()
 else:
  rec=json.loads(H1.read_text());rec['config_sha256']=binding['config_sha256'];rec['frame_layout']=binding['frame_layout']
  receipt=(json.dumps(rec,sort_keys=True,indent=2)+'\n').encode();cfg['preparation']['sha256']=pin(receipt)['sha256'];data['preparation']=cfg['preparation']
  config_raw=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode();data['config']['sha256']=pin(config_raw)['sha256'];data_raw=(json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
 for name,raw in [('config',config_raw),('receipt',receipt),('data_receipt',data_raw)]:
  (root/(name+'.json')).write_bytes(raw);binding['preparation_sha256'][name]=pin(raw)['sha256']
 artifact=json.loads(BASE_ART.read_text());artifact['step']=200
 for n in ('heads','full_weights'):artifact[n]['path']=artifact[n]['path'].replace('/m100/','/m200/')
 files={'m200/heads.pt':b'heads','m200/full_weights/w':b'weights','m200/full_weights/i':b'index'}
 full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='w',**pin(b'weights'))],index=dict(name='i',**pin(b'index')))
 files['m200/full_weights/full_weights.json']=json.dumps(full).encode()
 for n,path in [('heads','heads.pt'),('full_weights','full_weights/full_weights.json')]:artifact[n]['sha256']=pin(files['m200/'+path])['sha256']
 if bad=='artifact_step':artifact['step']=100
 if bad=='run':artifact['heads']['path']=artifact['heads']['path'].replace('673bc60f','17c4ffa4')
 if bad=='config':artifact['config_sha256']='0'*64
 files['m200/artifact.json']=json.dumps(artifact).encode();raw=tarbytes(files);parts=[]
 for i in range(4):
  part=root/str(i);part.write_bytes(raw[i*len(raw)//4:(i+1)*len(raw)//4]);parts.append(str(part))
 whole=pin(raw);done=root/'5';done.write_text(binding['object']+' '+str(whole['bytes'])+' '+('0'*64 if bad=='sha' else whole['sha256'])+'\n')
 with tarfile.open(original/'0.tgz') as t:sealed=json.load(t.extractfile('9.json'))
 sealed['export_binding']=binding
 code=tarbytes({'9.json':json.dumps(sealed).encode()});(p/'0.tgz').write_bytes(code)
 write(p/'0.json',dict(payload_sha256=pin(code)['sha256'],plan_sha256=hashlib.sha256(json.dumps(sealed,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
 (p/'a/4.py').write_bytes((original/'fill_export.py').read_bytes());(p/'a/0.json').write_bytes((original/'package/a/0.json').read_bytes())
 args=['/usr/bin/python3','-I','-s','-B',str(p/'a/4.py'),'--parts']+parts+['--done',str(done),'--object',binding['object'],'--config',str(root/'config.json'),'--receipt',str(root/'receipt.json'),'--data-receipt',str(root/'data_receipt.json'),'--lineage','SFT','--step','100' if bad=='step' else '200','--out',str(p/'a/export.json'),'--prep-tar',str(root/'6'),'--base-inputs',str(p/'a/0.json'),'--inputs-out',str(p/'a/1.json')]
 result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 write(root/'proof.json',dict(passed=result.returncode==0,real_receipt=bool(real),synthetic_preparation=not bool(real),argv=args,returncode=result.returncode,stderr=result.stderr.decode(),binding=binding,source_artifact=str(BASE_ART),source_artifact_sha256=pin(BASE_ART.read_bytes())['sha256']))
 return root,p,result
if __name__=='__main__':
 results=[]
 for kind in ('b1','b2'):
  for bad in (None,'step','artifact_step','run','config','sha'):
   root,p,r=fixture(kind,bad);ok=(r.returncode==0)==(bad is None);results.append(dict(package=kind,case=bad or 'valid',passed=ok,proof=str(root/'proof.json')))
   print(kind,bad or 'valid',ok,r.stderr.decode()[-160:])
 write(W/'out/FILL_TESTS.json',results)
 if not all(v['passed'] for v in results):raise SystemExit(1)
