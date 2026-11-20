from common import *
import sqlite3,copy,subprocess,importlib.util
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import file_pin
from student_pilot.carrier_c1_run import identity
from launch_r1.entry import ASSERTIONS
F=D/'census_bytes';F.mkdir()
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
rows=[json.loads(line) for line in (D/'u/d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1').read_text().splitlines()]
assert len(rows)==len({r['row_key'] for r in rows})==320
protected=[dict(qid=r['row_key'],provenance=dict(canonical_scene=r['canonical'])) for r in rows]
clean=dict(qid='clean',canonical='scannet/scene9999_00',dataset='scannet',scene='scene9999_00',target='<think>fixture observation</think>A')
def database(path,rows):
 with sqlite3.connect(path) as con:
  con.execute('create table rows(i integer primary key,row text,target text)')
  for i,row in enumerate(rows):con.execute('insert into rows values(?,?,?)',(i,json.dumps(row),'{}'))
 return file_pin(path)
records=[]
for name in ('q','n','n_go','qd'):
 k=kit(name);sys.path.insert(0,str(k/'b'))
 for module in ('cs','sv','rv','z'):sys.modules.pop(module,None)
 import cs
 for case in ('clean','protected','outside','noncanonical','unresolved'):
  root=F/(name+'_'+case);(root/'p/q').mkdir(parents=True);(root/'p/s').symlink_to(T,target_is_directory=True)
  target=root/'target';fake=root/'kit';(fake/'k').mkdir(parents=True)
  J.write(fake/'k/p.json',dict(n_root=str(target)))
  J.write(fake/'k/a.json',dict(GO=name=='n_go',discovery=name=='qd'))
  cfg=copy.deepcopy(J.load(k/'k/n.json'))
  cfg['r1_training']['proof_mode']='q' if name in ('q','qd') else 'train'
  if name in ('q','qd'):cfg['r1_training'].pop('init_policy',None)
  else:cfg['r1_training']['init_policy']='step400_export_weights_fresh_v1'
  cfg['r1_training'].pop('direction_twins',None) # This fixture covers strict Rooms; native Binding has a separate kit test.
  cfg['streams']={};prep=dict(streams={});source={}
  for stream in cs.STREAMS:
   src=([*protected,dict(clean,qid='point-clean')] if stream=='pointing' else [dict(clean,qid=stream+'-clean')])
   if case=='outside' and stream=='pointing':src[0]=dict(clean,qid=protected[0]['qid'])
   source_pin=database(root/(stream+'_source.sqlite'),src)
   receipt=J.write(root/(stream+'_source.json'),dict(database=source_pin,count=len(src)))
   source[stream]=[dict(receipt=receipt,population=source_pin,count=len(src))]
   selected=[dict(clean,qid=stream+'-clean')]
   if case=='protected' and stream=='pointing':selected.append(protected[0])
   if stream=='pointing' and case=='noncanonical':selected.append(dict(clean,qid='noncanonical',canonical=protected[0]['provenance']['canonical_scene'],provenance=dict(canonical_scene=clean['canonical'])))
   if stream=='pointing' and case=='unresolved':selected.append(dict(clean,qid='unresolved',provenance=dict(canonical_scene='unknown/token')))
   db=database(root/(stream+'.sqlite'),selected)
   cfg['streams'][stream]=J.write(root/(stream+'.json'),dict(database=db,count=len(selected)))
   prep['streams'][stream]=dict(database=db,count=len(selected),receipt=cfg['streams'][stream])
  cfg['preparation']=J.write(root/'prep.json',prep)
  sp=J.write(root/'p/q/ss.json',source)
  (root/'p/i').mkdir()
  mp=J.write(root/'p/i/staging.json',dict(entries={'ss.json':dict(sha256=sp['sha256'],bytes=(root/'p/q/ss.json').stat().st_size)}))
  J.write(root/'p/q/host.json',dict(staging_plan_sha256=mp['sha256']))
  os.environ['SLURM_JOB_ID']='91'
  refusal=None
  with scope(paths):
   try:pin=cs.publish(fake,root,cfg,'91')
   except ValueError as e:refusal=str(e)
  expected=None if case=='clean' or name=='qd' else ('R1_PROTECTED_ROOM_UNRESOLVED:pointing' if case=='unresolved' else 'R1_PROTECTED_ROOM_ROWS:pointing' if case in ('protected','noncanonical') else 'R1_PROTECTED_LIST_KEY_NOT_PROTECTED:pointing')
  assert refusal==expected,(name,case,refusal,expected)
  report=J.load(root/'c5.json')
  assert J.sha(root/'c5.json')==J.sha(target/'o/91/live/c4.json')
  if case in ('noncanonical','unresolved'):
   code='R1_PROTECTED_ROOM_UNRESOLVED:pointing' if case=='unresolved' else 'R1_PROTECTED_ROOM_ROWS:pointing'
   assert code in report['streams']['pointing']['refusals']
  if case=='clean':
   result=report['streams']['pointing']['result'];assert result['listed_keys']==result['checked_keys']==320
   assert result['source_rows']==321 and result['admitted_rows']==1
  else:
   assert report['status']==('WOULD_REFUSE' if name=='qd' else 'REFUSE')
   if case=='protected':assert report['streams']['pointing']['protected_keys']['count']==1
  records.append(dict(kit=name,case=case,refusal=refusal,status=report['status']))
  if case!='clean':continue
  # Execute actual h.py against a sealed kit with only the target path localized.
  import shutil
  sealed=root/'sealed'
  def transport(a,b):
   if Path(a).name in ('p.json','BUILD.json','SHA256SUMS.txt'):return shutil.copyfile(a,b)
   os.link(a,b);return b
  shutil.copytree(k,sealed,copy_function=transport)
  spec=J.load(sealed/'k/p.json');spec['n_root']=str(target);cap(sealed,'k/p.json',spec);reseal(sealed)
  def host(config):
   hp=J.write(root/'p/q/host.json',dict(staging_plan_sha256=mp['sha256'],status='PASS',config_identity=identity(config),assertions=dict.fromkeys(ASSERTIONS,True),loader_audit=dict(complete=True)))
   J.write(root/'p/q/RESULT.json',dict(status='ADMIT',init_milestone=400,config=J.write(root/'cfg.json',config),host_receipt=hp))
  host(cfg)
  def check(label,expected):
   p=subprocess.run([sys.executable,'-B','-s',str(sealed/'b/h.py'),str(root/'p'),str(root/(label+'.json'))],capture_output=True,text=True)
   (root/(label+'.log')).write_text(p.stdout+p.stderr)
   if expected:assert p.returncode and expected in p.stderr,(name,label,p.stderr)
   else:assert p.returncode==0,(name,label,p.stderr)
   records.append(dict(kit=name,case='h_'+label,refusal=expected))
  check('clean',None)
  original=(root/'c5.json').read_bytes()
  bad=J.load(root/'c5.json');bad['config_identity']='0'*64
  replace(root/'c5.json',json.dumps(bad))
  check('wrong_identity','R1_CENSUS_IDENTITY_DIFFERS')
  replace(root/'c5.json',original)
  (root/'c5.json').rename(root/'retained_c5.json')
  check('missing','R1_CENSUS_RECEIPT_MISSING')
  (root/'retained_c5.json').rename(root/'c5.json')
  bad=J.load(root/'c5.json');bad['streams']['pointing']['store_pins']['count']+=1
  replace(root/'c5.json',json.dumps(bad));(target/'o/91/live/c4.json').write_bytes((root/'c5.json').read_bytes());check('wrong_store','R1_CENSUS_STORE_PINS_DIFFER:pointing')
  replace(root/'c5.json',original)
  (target/'o/91/live/c4.json').write_bytes((root/'c5.json').read_bytes())
  # Preflight is diagnostic only; qd must return and reach the caller's preparation boundary.
  with scope(paths):
   extra=dict(clean,qid='unlisted',provenance=dict(canonical_scene=protected[0]['provenance']['canonical_scene']))
   extra.pop('canonical',None)
   source2=copy.deepcopy(source)
   sp=database(root/'preflight_point.sqlite',[*protected,extra,clean])
   source2['pointing']=[dict(population=sp,count=322)]
   hit=None
   try:
    cs.preflight(fake,root,cfg,source2,'91')
    (root/'preparation_reached.txt').write_text('Native preparation boundary reached after diagnostic census.\n')
   except ValueError as e:hit=str(e)
   assert (root/'preparation_reached.txt').exists()==(name=='qd'),(name,hit)
   assert hit is None if name=='qd' else hit=='R1_PROTECTED_ROOM_ROWS:pointing'
   records.append(dict(kit=name,case='preflight',refusal=hit,continues=name=='qd'))
J.write(D/'CENSUS_BYTE_TESTS.json',dict(status='PASS',records=records,shape_keys=320,native_postcondition=True,native_complete_sqlite_readers=True,boundary='Synthetic source/admitted stores and actual pinned authority/list bytes. h.py executes unmodified sealed-kit logic; no production population claim.'))
print('Census and h binding cases PASS',len(records))
