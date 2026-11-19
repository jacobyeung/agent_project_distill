"""Build the tower-and-own camera read delivery from the reviewed A4 delivery.

The seal steps are out3's: rebuild.py's tarbytes (pinned to GNU format, the
default of the Python 3.6 that sealed A4), build_package.py's token reseal,
build_operator.py's bundle and batch, and seal_delivery.py's manifest rewrite.
Only the token, the operator and, with --export-pin, the export identity change.
"""
import argparse,ast,gzip,hashlib,io,json,re,secrets,sys,tarfile
from datetime import datetime,timezone
from pathlib import Path

A4_DELIVERY_SHA256='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'
A4_OPERATOR_SHA256='97c8e6dfe33e7fd2988dc44e740f7a3b19627259b8f86827598ed368e1659e22'
KIT=Path(__file__).resolve().parent
O3=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
CAMERA=(0,1,2)
FILL_PINS=('REVIEWED_OBJECT','REVIEWED_ARCHIVE_BYTES','REVIEWED_ARCHIVE_SHA256')
PIN_KEYS={'step','member_directory','object','archive_bytes','archive_sha256','done','part_bytes',
          'run','lineage','config_sha256','base_identity','frame_layout','preparation_sha256','prep_paths'}
RUN_DIRS={'673bc60f':'x_69d2930d','6ed2c7aa':'x_ee227714'}
PREP_NAMES={'config':'config.json','receipt':'prepared/s1_receipt.json','data_receipt':'data_receipt.json'}

def done_path(run,step):
 if run not in RUN_DIRS:raise ValueError('Unknown export run: '+str(run))
 return '/project/community/jjyeung/okh7/%s/o/gcs_%s_m%d.done'%(RUN_DIRS[run],run,step)

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':')).encode())
def jbytes(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()

def unpack(b):
 with tarfile.open(fileobj=io.BytesIO(b)) as t:
  assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in t)
  return {m.name:t.extractfile(m).read() for m in t}

def tarbytes(files):
 buf=io.BytesIO()
 with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w',format=tarfile.GNU_FORMAT) as t:
   for n,b in sorted(files.items()):
    m=tarfile.TarInfo(n);m.size=len(b);m.mode=0o600;t.addfile(m,io.BytesIO(b))
 return buf.getvalue()

def bundle_of(batch_text):
 line=next(s for s in batch_text.decode().splitlines() if s.startswith('b=bytes.fromhex('))
 return unpack(bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0])))

def load_a4(a4):
 raw=(Path(a4)/'1.tgz').read_bytes()
 if sha(raw)!=A4_DELIVERY_SHA256:raise ValueError('A4 delivery differs from the reviewed bytes')
 delivery=unpack(raw);manifest=json.loads(delivery['PACKAGE.json'])
 for n,h in manifest['files'].items():
  if sha(delivery[n])!=h:raise ValueError('A4 manifest pin differs: '+n)
 if sha(delivery['a/6.py'])!=A4_OPERATOR_SHA256:raise ValueError('A4 operator differs')
 return delivery,unpack(delivery['0.tgz']),bundle_of(delivery['BATCH.sh'])

def check_pin(pin,base):
 if set(pin)-PIN_KEYS:raise ValueError('Unknown export pin keys: '+','.join(sorted(set(pin)-PIN_KEYS)))
 step=pin['step']
 if type(step) is not int or step<=0:raise ValueError('Export step must be a positive integer')
 run=pin.get('run',base['run']);done=done_path(run,step)
 if run!=base['run']:
  required={'run','config_sha256','base_identity','frame_layout','lineage','preparation_sha256','prep_paths'}
  if required-set(pin):raise ValueError('Changed run requires full preparation pin: '+','.join(sorted(required-set(pin))))
 if pin['member_directory']!=f'm{step}':raise ValueError('Member directory must be m<step>')
 if not re.fullmatch(r'q8/[0-9a-f]{8}/[0-9a-f]{8}_m%d\.tar'%step,pin['object']):raise ValueError('Object must be q8/<hex8>/<run>_m<step>.tar')
 if not pin['object'].split('/')[-1].startswith(pin.get('run',base['run'])+'_'):raise ValueError('Object run differs')
 if type(pin['archive_bytes']) is not int or pin['archive_bytes']<=0:raise ValueError('Archive bytes must be positive')
 if not re.fullmatch('[0-9a-f]{64}',pin['archive_sha256']):raise ValueError('Archive sha256 must be 64 hex')
 if pin['done']!=done:
  raise ValueError('Completion receipt must be the okh7 gcs_<run>_m<step>.done path')
 if 'part_bytes' in pin and (type(pin['part_bytes']) is not int or pin['part_bytes']<=0):raise ValueError('Part bytes must be positive')
 if 'config_sha256' in pin and not re.fullmatch('[0-9a-f]{64}',pin['config_sha256']):raise ValueError('Config sha256 must be 64 hex')
 for key in ('base_identity','frame_layout','lineage'):
  if key in pin and not re.fullmatch('[A-Za-z0-9_-]+',pin[key]):raise ValueError('Invalid '+key)
 if 'preparation_sha256' in pin:
  hashes=pin['preparation_sha256']
  if not isinstance(hashes,dict) or set(hashes)!=set(PREP_NAMES) or any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in hashes.values()):
   raise ValueError('Preparation sha256 must name all three files with 64 hex hashes')
  if hashes!=base['preparation_sha256'] and 'prep_paths' not in pin:raise ValueError('Changed preparation requires prep_paths')
 if 'prep_paths' in pin:
  paths=pin['prep_paths']
  if not isinstance(paths,dict) or set(paths)!=set(PREP_NAMES):raise ValueError('Preparation paths must name all three files')
  if 'preparation_sha256' not in pin:raise ValueError('Preparation paths require preparation_sha256')
  root='/project/community/jjyeung/okh7/%s/runs/%s/inputs/'%(RUN_DIRS[run],run)
  for key,name in PREP_NAMES.items():
   pattern=re.escape(root)+(r'prepare_[0-9a-f]{32}/' if key!='data_receipt' else '')+re.escape(name)
   if not isinstance(paths[key],str) or not re.fullmatch(pattern,paths[key]):raise ValueError('Invalid preparation path: '+key)
  if paths['receipt']!=str(Path(paths['config']).parent/'prepared/s1_receipt.json'):raise ValueError('Preparation config and receipt directories differ')

def repin(delivery,payload,pin):
 cfg=json.loads(payload['9.json']);base=cfg['export_binding'];check_pin(pin,base)
 binding={**base,**{k:pin[k] for k in base if k in pin}}
 cfg['export_binding']=binding;payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
 text=delivery['a/4.py'].decode()
 for name,value in zip(FILL_PINS,(repr(pin['object']),str(pin['archive_bytes']),repr(pin['archive_sha256']))):
  text,n=re.subn(r'(?m)^%s = .*$'%name,lambda m:f'{name} = {value}',text)
  if n!=1:raise ValueError('Fill pin not found once: '+name)
 delivery['a/4.py']=text.encode()

def payload_build(payload):
 """Import the payload's own orchard_h10.build (stdlib-only) from a private copy."""
 import importlib,tempfile
 root=Path(tempfile.mkdtemp(prefix='ob_'))
 for n in ('orchard_h10/__init__.py','orchard_h10/common.py','orchard_h10/build.py'):put(root/n,payload[n])
 for name in [m for m in sys.modules if m=='orchard_h10' or m.startswith('orchard_h10.')]:del sys.modules[name]
 sys.path.insert(0,str(root))
 try:return importlib.import_module('orchard_h10.build')
 finally:sys.path.remove(str(root))

def seal(delivery,payload,bundle,token,operator):
 """build_package + build_operator + seal_delivery, in A4's byte formats."""
 build=payload_build(payload);batch=build.batch
 build.valid_token(token)
 delivery=dict(delivery);payload=dict(payload)
 cfg=json.loads(payload['9.json']);cfg['token']=token
 payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
 raw=tarbytes(payload)
 public=dict(token=token,payload_sha256=sha(raw),payload_bytes=len(raw),plan_sha256=canonical(cfg))
 delivery.update({'0.tgz':raw,'0.json':jbytes(public),'CONFIG.json':jbytes(public),'a/6.py':operator})
 boot=tarbytes({'0.py':bundle['0.py'],'0.json':delivery['0.json'],'7.py':operator})
 delivery['BATCH.sh']=batch(boot,token).encode()
 manifest=json.loads(delivery['PACKAGE.json']);manifest['token']=token
 manifest['files']={n:sha(delivery[n]) for n in manifest['files']}
 delivery['PACKAGE.json']=jbytes(manifest)
 return delivery,payload,public,cfg,tarbytes(delivery)

def verify(raw,a4_delivery,operator):
 """Reopen a sealed delivery and check every pin the Orchard scripts check."""
 d=unpack(raw);m=json.loads(d['PACKAGE.json']);v=json.loads(d['0.json'])
 assert set(d)==set(a4_delivery),'delivery member set differs'
 for n,h in m['files'].items():assert sha(d[n])==h,n
 assert m['token']==v['token'] and d['CONFIG.json']==d['0.json'] and sha(d['0.tgz'])==v['payload_sha256'] and len(d['0.tgz'])==v['payload_bytes']
 p=unpack(d['0.tgz']);cfg=json.loads(p['9.json'])
 assert canonical(cfg)==v['plan_sha256'] and cfg['token']==v['token']
 a4p=unpack(a4_delivery['0.tgz'])
 assert set(p)==set(a4p) and [n for n in p if p[n]!=a4p[n]] in (['9.json'],[])
 b=bundle_of(d['BATCH.sh']);a4b=bundle_of(a4_delivery['BATCH.sh'])
 assert set(b)=={'0.py','0.json','7.py'} and b['0.py']==a4b['0.py'] and b['0.json']==d['0.json'] and b['7.py']==d['a/6.py']==operator
 assert json.loads(d['a/1.json'])=={'pending':True} and json.loads(d['a/export.json'])=={'pending':True}
 return dict(token=v['token'],plan_sha256=v['plan_sha256'],payload_sha256=v['payload_sha256'],delivery_sha256=sha(raw),
             changed_delivery=sorted(n for n in d if d[n]!=a4_delivery[n]),
             changed_payload=sorted(n for n in p if p[n]!=a4p[n]),binding=cfg['export_binding'])

def null_fork(a4):
 """Resealing A4 with its own token and operator must reproduce its bytes."""
 delivery,payload,bundle=load_a4(a4)
 token=json.loads(delivery['0.json'])['token']
 new,_,_,_,raw=seal(delivery,payload,bundle,token,delivery['a/6.py'])
 same=[n for n in delivery if new[n]==delivery[n]]
 return dict(delivery_identical=sha(raw)==A4_DELIVERY_SHA256,members_identical=len(same)==len(delivery),
             delivery_sha256=sha(raw),members=len(delivery))

def add_dry_checks(text):
 """Embed the login-node checks; no extra staging files or sealed changes."""
 anchor='cd "$P"\nCUDA_VISIBLE_DEVICES= '
 if text.count(anchor)!=1:raise ValueError('Expected one pre-check directory change')
 resolution=('PREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n'
  '/usr/bin/python3 -I -s -B - "$P/a/1.json" "$P/a/0.json" "$PREP" > "$E/dryres.json" 2>&1 <<\'PYCODE\'\n'
  +(KIT/'dryres2.py').read_text()+'PYCODE\n')
 text=text.replace(anchor,resolution+anchor)
 anchor='/usr/bin/python3 -I -s -B - "$P" "$E" <<\'PYCODE\'\n'
 if text.count(anchor)!=1:raise ValueError('Expected one success receipt writer')
 package=('/usr/bin/python3 -I -s -B - "$P" "$E/drywork" > "$E/drypackage.json" 2>&1 <<\'PYCODE\'\n'
  +(KIT/'dry_own.py').read_text()+'PYCODE\n')
 return text.replace(anchor,package+anchor)

def scripts(a_dir,token,delivery_sha,binding,pin,walltime='05:00:00'):
 """Derive the operator scripts from A's reviewed scripts with checked substitutions."""
 a_dir=Path(a_dir);out={}
 old_token='d72cdcff1e22a';step=binding['step'];member=binding['member_directory']
 done=pin['done'] if pin else '/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m200.done'
 size=pin['archive_bytes'] if pin else 21583032320;digest=pin['archive_sha256'] if pin else '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'
 part=(pin or {}).get('part_bytes',None if pin else 5395758080)
 def sub(text,old,new,count=1):
  n=text.count(old)
  if n!=count:raise ValueError(f'Expected {count} of {old!r}, found {n}')
  return text.replace(old,new)
 for name in ('o_place.sh','o_pullfill.sh','o_pullfill_resume.sh','o_cpucheck.sh','o_sub.sh','o_fetch.sh'):
  text=(a_dir/name).read_text()
  if name=='o_place.sh':
   text,n=re.subn(r"(printf '%s  %s\\n' )[0-9a-f]{64}",lambda x:x[1]+delivery_sha,text)
   if n!=1:raise ValueError('Delivery checksum line not found once')
   text=sub(text,"b['run']=='673bc60f' and b['step']==200 and b['member_directory']=='m200'",
            f"b['run']=={binding['run']!r} and b['step']=={step} and b['member_directory']=={member!r}")
  if name.startswith('o_pullfill'):
   if name=='o_pullfill_resume.sh' and part is None:continue
   text=sub(text,'B=/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85\n','')
   text=sub(text,'test -f "$B/0.tgz"\n','')
   text=sub(text,'OBJECT=q8/8865619b/673bc60f_m200.tar',f"OBJECT={binding['object']}")
   text=sub(text,'DONE=/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m200.done',f'DONE={done}')
   text=sub(text,"int(f[1])==21583032320 and f[2]=='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'",f'int(f[1])=={size} and f[2]=={digest!r}')
   text=sub(text,'--lineage SFT --step 200',f"--lineage {binding['lineage']} --step {step}")
   if pin and 'prep_paths' in pin:
    text=sub(text,'I=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/inputs\n','')
    copies=''.join('cp "%s" "$E/%s"\n'%(pin['prep_paths'][key],dest)
                   for key,dest in (('config','7'),('receipt','8'),('data_receipt','9')))
    if name=='o_pullfill.sh':
     old=('cp "$I/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json" "$E/7"\n'
          'cp "$I/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json" "$E/8"\n'
          'cp "$I/data_receipt.json" "$E/9"\n')
     text=sub(text,old,copies)
    else:text=sub(text,'test -f "$A/0.tgz"\n','test -f "$A/0.tgz"\ncp "$DONE" "$E/5"\n'+copies)
   if name=='o_pullfill_resume.sh':text=sub(text,'= 5395758080',f'= {part}')
  text=sub(text,old_token,token,text.count(old_token) or 1)
  if '--time 05:00:00' in text:text=text.replace('--time 05:00:00','--time '+walltime)
  if name.startswith('o_pullfill'):text=add_dry_checks(text)
  out[name]=text
 return out

def item_order(payload):
 manifest=json.loads(payload['items/devs1_routed.json'])['items']
 order=json.loads(payload['9.json'])['order']
 return [r['id'] for t in CAMERA for r in manifest if r['question_type']==order[t]]

def read_plan(a_plan,a4_dir,public,cfg,delivery,bundle,operator,payload,walltime):
 mod={};exec(compile(operator,'ownread_operator','exec'),mod)
 plan=json.loads(Path(a_plan).read_text())
 ids=item_order(payload)
 binding={**cfg['export_binding'],**{k:v for k,v in zip(('archive_bytes','archive_sha256'),
          (int(re.search(r'(?m)^REVIEWED_ARCHIVE_BYTES = (\d+)$',delivery['a/4.py'].decode())[1]),
           re.search(r"(?m)^REVIEWED_ARCHIVE_SHA256 = '([0-9a-f]{64})'$",delivery['a/4.py'].decode())[1]))}}
 plan.update(arms=list(mod['ARMS']),expected=[mod['EXPECTED']],export_binding=binding,item_ids_in_execution_order=ids,
             item_sets={'dev-S1':len(ids)},memo_scope='one worker per question type and read',
             operations_file='OPERATOR.md',operator_path='7.py',operator_sha256=sha(operator),
             plan_sha256=public['plan_sha256'],read_settings=mod['descriptors'](None),
             sequence=[list(s) for s in mod['SCHEDULE']],token=public['token'],walltime=walltime)
 plan.pop('item_order_matches_baseline_read0',None)
 plan['export_identity_seal']='Delivery PACKAGE.json pins a/4.py and 0.tgz; payload 9.json carries the export binding.'
 journals=Path(a4_dir)/'ret/metadata/reads/0/metadata/journals'
 if journals.is_dir():
  a4_ids=[json.loads(l)['id'] for t in CAMERA for l in (journals/str(t)/'0/items.jsonl').read_text().splitlines() if l.strip()]
  plan['item_order_matches_a4_camera_read']=a4_ids==ids
 plan['cpu_check']={**plan['cpu_check'],'helper_sha256':sha(delivery['a/5.py']),'bootstrap_sha256':sha(bundle['0.py'])}
 return plan

def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--a4',type=Path,default=O3/'A4',help='reviewed A4 delivery directory')
 p.add_argument('--a',type=Path,default=O3/'A',help="A's directory (READ_PLAN.json and o_*.sh templates)")
 p.add_argument('--out',required=True,type=Path);p.add_argument('--token')
 p.add_argument('--work-dir',type=Path,help='fresh local directory for extracted package/src trees; output links to it')
 p.add_argument('--operator',type=Path,default=KIT/'ownread_sequence.py')
 p.add_argument('--export-pin',type=Path,help='JSON naming the 400 or 600 export; absent keeps the step-200 binding')
 p.add_argument('--time',default='05:00:00')
 a=p.parse_args(argv)
 if a.out.exists():raise ValueError('Output exists; build into a fresh directory')
 if a.work_dir and a.work_dir.exists():raise ValueError('Work directory exists; use a fresh directory')
 proof=null_fork(a.a4)
 if not (proof['delivery_identical'] and proof['members_identical']):raise ValueError('Seal recipe no longer reproduces A4')
 delivery,payload,bundle=load_a4(a.a4);a4=dict(delivery)
 pin=json.loads(a.export_pin.read_text()) if a.export_pin else None
 if pin:repin(delivery,payload,pin)
 token=a.token or secrets.choice('abcdef')+secrets.token_hex(6)
 operator=a.operator.read_bytes()
 delivery,payload,public,cfg,raw=seal(delivery,payload,bundle,token,operator)
 record=verify(raw,a4,operator)
 O=a.out;O.mkdir(parents=True)
 if a.work_dir:
  for name in ('package','src'):
   target=a.work_dir.resolve()/name;target.mkdir(parents=True)
   (O/name).symlink_to(target,target_is_directory=True)
 for n,b in delivery.items():put(O/'package'/n,b)
 for n,b in payload.items():put(O/'src'/n,b)
 put(O/'1.tgz',raw);put(O/'0.tgz',delivery['0.tgz']);put(O/'PACKAGE.json',delivery['PACKAGE.json'])
 put(O/'TOKEN',(token+'\n').encode());put(O/'tower_sequence.py',operator)
 for n in ('fetch_return.py','unpack_return.py'):put(O/n,(a.a4/n).read_bytes())
 put(O/'OPERATOR.md',(KIT/'OPERATOR.md').read_bytes())
 for n,text in scripts(a.a,token,sha(raw),cfg['export_binding'],pin,a.time).items():put(O/n,text.encode())
 put(O/'READ_PLAN.json',jbytes(read_plan(a.a/'READ_PLAN.json',a.a4,public,cfg,delivery,bundle,operator,payload,a.time)))
 diff={n:dict(a4_sha256=sha(a4[n]),sha256=sha(delivery[n]),identical=a4[n]==delivery[n]) for n in sorted(delivery)}
 build=dict(utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),token=token,job_name='a15_cot_ap'+token,
            builder_sha256=sha(Path(__file__).read_bytes()),operator_sha256=sha(operator),
            export_pin=pin,export_pin_sha256=sha(a.export_pin.read_bytes()) if pin else None,
            null_fork=proof,delivery=record,files={n:sha((O/n).read_bytes()) for n in ('1.tgz','0.tgz','PACKAGE.json','READ_PLAN.json')},
            diff_vs_a4=diff)
 put(O/'BUILD.json',jbytes(build))
 with (O.parent/'TOKEN_LEDGER.jsonl').open('a') as ledger:
  ledger.write(json.dumps(dict(utc=build['utc'],token=token,job_name=build['job_name'],build=str(O),
   read='dev-S1 camera 450 x arms tower,own; export step %d'%cfg['export_binding']['step'],
   delivery_sha256=sha(raw),plan_sha256=public['plan_sha256']),sort_keys=True)+'\n')
 print(json.dumps(dict(out=str(O),token=token,delivery_sha256=sha(raw),plan_sha256=public['plan_sha256'],
                       changed_delivery=record['changed_delivery'],changed_payload=record['changed_payload'],null_fork=proof)))
 return build

if __name__=='__main__':main()
