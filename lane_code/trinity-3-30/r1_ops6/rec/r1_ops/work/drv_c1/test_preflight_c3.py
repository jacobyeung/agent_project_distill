"""Stream a tiny real-format A slot and compare authenticated prepared families."""
import copy,hashlib,importlib.util,io,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
from packet_config import MEMBERS
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='preflight_c3_',dir=W))
sha=lambda v:hashlib.sha256(v).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,sort_keys=True)+'\n');return sha(p.read_bytes())
spec=importlib.util.spec_from_file_location('bridge',W/'fixture_c3/c0.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
# The inherited READY fixture supplies the sealed A template and code record.
ready=W/'tests_c2_cszuhpu9/derived_ready';parent=json.loads((ready/'k/a0.json').read_text());code=json.loads((ready/'k/7.json').read_text());cfg=json.loads((ready/json.loads((ready/'k/launch.json').read_text())['config']['file']).read_text())
_,source,_=bridge.fixture(T/'donor',parent,code);tree=T/'donor/t';ain=tree/'inputs';cin=T/'cinputs';cin.mkdir();b=T/'i_7f1589c1';b.mkdir();k=T/'x_7f1589c1';k.mkdir()
mix=dict(populations={'vqa':{'room':3,'direction':4}},effective={'vqa':{'room':1,'direction':2}},spec={'vqa':{'room':170,'direction':3119}})
for inputs,base,sourcecfg in ((ain,parent,parent),(cin,cfg,cfg)):
 logical=Path(base['output'])/'inputs'
 def pin(name):return dict(path=str(logical/name),sha256=sha((inputs/name).read_bytes()))
 write(inputs/'prepared/type_mix.json',mix)
 effective=copy.deepcopy(base);effective.pop('admission',None)
 prep=dict(config_sha256=bridge.identity(effective),streams={'vqa':{'count':203812}},recipe=parent['recipe'],type_mix_population=pin('prepared/type_mix.json'))
 write(inputs/'prep.json',prep);effective['preparation']=pin('prep.json');write(inputs/'effective.json',effective)
 receipt=dict(status='PREPARED',rehearsal=False,real_frames_verified=True,world_size=4,source_revision=code['commit'],input_streams=sourcecfg['streams'],config=pin('effective.json'),preparation=pin('prep.json'))
 write(inputs/'data_receipt.json',receipt)
 if inputs==ain:
  bound=dict(config_sha256=bridge.identity(effective),preparation=pin('prep.json'),trainer_commit=code['commit'],world_size=4)
  write(tree/'binding.json',bound);write(source/'binding.json',bound);(source/'binding.json.sha256').write_text(sha((source/'binding.json').read_bytes()))
  complete=tree/'checkpoint_000200/complete.json';m=json.loads(complete.read_text());m['binding']=bound;write(complete,m)
with tarfile.open(source/'A.tar','w') as tf:
 for p in sorted(tree.rglob('*')):
  if p.is_file():v=p.read_bytes();info=tarfile.TarInfo(str(p.relative_to(tree)));info.size=len(v);tf.addfile(info,io.BytesIO(v))
r=json.loads((source/'A.json').read_text());r.update(archive_sha256=sha((source/'A.tar').read_bytes()),bytes=(source/'A.tar').stat().st_size,manifest_sha256=sha((tree/'checkpoint_000200/complete.json').read_bytes()));write(source/'A.json',r);(source/'A.sha256').write_text(r['archive_sha256'])
(k/'b').mkdir();(k/'b/c0.py').write_bytes(MEMBERS['c0.py']);write(k/'k/a0.json',parent);write(k/'k/7.json',code);digest=write(k/'k/config.json',cfg);write(k/'k/launch.json',dict(config=dict(file='k/config.json',sha256=digest)))
(k/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(k))+'\n' for p in sorted(k.rglob('*')) if p.is_file()))
old=k.with_name(k.name+'.f172180');(old/'o').mkdir(parents=True)
(old/'o/172180.proof.log').write_bytes((W/'f172180.proof.log').read_bytes());(old/'o/172180.proof.json').write_bytes((W/'f172180.proof.json').read_bytes())
body=(W/'preflight_c3.py').read_text().replace("root=Path(pointer['root'])","root=Path("+repr(str(source))+")")
for label in ('equal','family_diff','bad_archive','missing_c_inputs'):
 test=body
 args=[sys.executable,'-I','-B','-c',test,str(b),str(k),str(cin if label!='missing_c_inputs' else T/'missing')]
 if label=='family_diff':
  changed=copy.deepcopy(mix);changed['populations']['vqa']['room']=8;write(cin/'prepared/type_mix.json',changed)
  p=json.loads((cin/'prep.json').read_text());p['type_mix_population']['sha256']=sha((cin/'prepared/type_mix.json').read_bytes());write(cin/'prep.json',p)
  d=json.loads((cin/'data_receipt.json').read_text());d['preparation']['sha256']=sha((cin/'prep.json').read_bytes());write(cin/'data_receipt.json',d)
 if label=='bad_archive':
  rr=copy.deepcopy(r);rr['archive_sha256']='0'*64;write(source/'A.json',rr);(source/'A.sha256').write_text('0'*64)
 result=subprocess.run(args,capture_output=True,text=True)
 (T/(label+'.out')).write_text(result.stdout+result.stderr)
 assert (result.returncode==0)==(label=='equal'),(label,result.stdout,result.stderr)
 if label=='family_diff':assert 'FAMILY populations/vqa/room different' in result.stdout
 if label=='bad_archive':write(source/'A.json',r);(source/'A.sha256').write_text(r['archive_sha256'])
 print('PASS preflight',label)
print('PASS read-only archive verification and family comparison on synthetic prepared receipts; no GPU payload deserialized')
