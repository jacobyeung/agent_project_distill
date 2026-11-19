"""R2 small-part fill fixtures; the missing data receipt is explicitly synthetic."""
from pathlib import Path
import hashlib,io,json,tarfile,copy,subprocess,tempfile,ast
W=Path(__file__).resolve().parent;ROOT=W.parent
TMP=W/'fill_fixtures';TMP.mkdir(exist_ok=True)
def pin(raw):return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def tarbytes(files):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as t:
  for n,raw in sorted(files.items()):m=tarfile.TarInfo(n);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
 return b.getvalue()
def fixture(kind='A',bad=None,production_pin=False,real_data=False):
 root=Path(tempfile.mkdtemp(prefix='f_',dir=TMP));p=root/'p';(p/'a').mkdir(parents=True)
 original=W/kind;binding=copy.deepcopy(json.loads((original/'src/9.json').read_text())['export_binding'])
 config=ROOT/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json';config_raw=config.read_bytes();receipt=(ROOT/'in/s1/s1_receipt.json').read_bytes();cfg=json.loads(config_raw)
 data=dict(schema='s1-in-job-data-v1',status='PREPARED',real_frames_verified=True,rehearsal=False,synthetic=False,config=dict(path=str(Path(cfg['preparation']['path']).parent.parent/'config.json'),sha256=pin(config_raw)['sha256']),preparation=cfg['preparation'])
 data_raw=(ROOT/'in/data_receipt.json').read_bytes() if real_data else (json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
 assert pin(config_raw)['sha256']==binding['preparation_sha256']['config']
 assert pin(receipt)['sha256']==binding['preparation_sha256']['receipt']
 assert (pin(data_raw)['sha256']==binding['preparation_sha256']['data_receipt']) is real_data
 for n,raw in [('config',config_raw),('receipt',receipt),('data_receipt',data_raw)]:(root/(n+'.json')).write_bytes(raw)
 if not production_pin:binding['preparation_sha256']['data_receipt']=pin(data_raw)['sha256']
 artifact=dict(step=200,config_sha256=binding['config_sha256'],base_identity=binding['base_identity'],frame_layout='duplicate',geometry_online=False)
 files={'m200/heads.pt':b'heads','m200/full_weights/w':b'weights','m200/full_weights/i':b'index'}
 full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='w',**pin(b'weights'))],index=dict(name='i',**pin(b'index')))
 files['m200/full_weights/full_weights.json']=json.dumps(full).encode()
 for n,sub in [('heads','heads.pt'),('full_weights','full_weights/full_weights.json')]:artifact[n]=dict(path='/fixture/673bc60f/m200/'+sub,sha256=pin(files['m200/'+sub])['sha256'])
 if bad=='artifact_step':artifact['step']=100
 if bad=='run':artifact['heads']['path']=artifact['heads']['path'].replace('673bc60f','17c4ffa4')
 if bad=='config':artifact['config_sha256']='0'*64
 if bad=='prep_config':(root/'config.json').write_bytes(config_raw+b' ')
 if bad=='prep_receipt':(root/'receipt.json').write_bytes(receipt+b' ')
 files['m200/artifact.json']=json.dumps(artifact).encode();raw=tarbytes(files);parts=[]
 for i in range(4):
  part=root/str(i);part.write_bytes(raw[i*len(raw)//4:(i+1)*len(raw)//4]);parts.append(str(part))
 whole=pin(raw);done=root/'5';done.write_text(binding['object']+' '+str(whole['bytes'])+' '+('0'*64 if bad=='sha' else whole['sha256'])+'\n')
 sealed=json.loads((original/'src/9.json').read_text());sealed['export_binding']=binding
 if production_pin:
  (p/'0.tgz').write_bytes((original/'0.tgz').read_bytes());(p/'0.json').write_bytes((original/'package/0.json').read_bytes())
 else:
  code=tarbytes({'9.json':json.dumps(sealed).encode()});(p/'0.tgz').write_bytes(code)
  write(p/'0.json',dict(payload_sha256=pin(code)['sha256'],plan_sha256=hashlib.sha256(json.dumps(sealed,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
 helper=(original/'fill_export.py').read_text()
 # Only disposable test helpers use a small archive pin; production constants stay sealed.
 helper=helper.replace('REVIEWED_ARCHIVE_BYTES = 21583032320','REVIEWED_ARCHIVE_BYTES = '+str(whole['bytes'])).replace("REVIEWED_ARCHIVE_SHA256 = '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'",'REVIEWED_ARCHIVE_SHA256 = '+repr(whole['sha256']))
 (p/'a/4.py').write_text(helper);(p/'a/0.json').write_bytes((original/'package/a/0.json').read_bytes())
 args=['/usr/bin/python3','-I','-s','-B',str(p/'a/4.py'),'--parts']+parts+['--done',str(done),'--object',binding['object'],'--config',str(root/'config.json'),'--receipt',str(root/'receipt.json'),'--data-receipt',str(root/'data_receipt.json'),'--lineage','SFT','--step','100' if bad=='step' else '200','--out',str(p/'a/export.json'),'--prep-tar',str(root/'6'),'--base-inputs',str(p/'a/0.json'),'--inputs-out',str(p/'a/1.json')]
 result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 write(root/'proof.json',dict(passed=result.returncode==0,real_config=True,real_receipt=True,synthetic_data_receipt=not real_data,production_payload=production_pin,argv=args,returncode=result.returncode,stderr=result.stderr.decode(),binding=binding,artifact_source='Synthetic schema fixture, based on surviving scan code; m100 artifact file is lost.'))
 return root,p,result
if __name__=='__main__':
 records=[]
 for k in ('A','B'):
  for bad in (None,'step','artifact_step','run','config','sha','prep_config','prep_receipt'):
   root,p,r=fixture(k,bad);ok=(r.returncode==0)==(bad is None)
   records.append(dict(package=k,case=bad or 'valid_fixture',passed=ok,proof=str(root/'proof.json')))
   print(k,bad or 'valid_fixture',ok,r.stderr.decode()[-150:])
  root,p,r=fixture(k,production_pin=True);ok=r.returncode!=0 and b'Reviewed preparation differs: data_receipt' in r.stderr
  records.append(dict(package=k,case='production_rejects_synthetic_receipt',passed=ok,proof=str(root/'proof.json')))
  print(k,'production_rejects_synthetic_receipt',ok,r.stderr.decode()[-150:])
 write(W/'FILL_TESTS.json',records)
 if not all(v['passed'] for v in records):raise SystemExit(1)
