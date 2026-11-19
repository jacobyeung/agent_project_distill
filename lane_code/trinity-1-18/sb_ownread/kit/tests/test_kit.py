"""Kit tests. Run tests/cpu_proof.py first; PROOF names its work directory."""
import copy,difflib,hashlib,json,os,re,shutil,subprocess,sys,tarfile
from pathlib import Path
import pytest

KIT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(KIT))
import build_ownread as B
import ownread
sys.path.insert(0,str(KIT/'tests'))
import check_build

O3=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
A4,A=O3/'A4',O3/'A'
BUILD=Path(os.environ.get('BUILD',KIT.parent/'out/pkg/b200'))
PROOF=Path(os.environ.get('PROOF',KIT.parent/'work/proofc'))
PY36='/usr/bin/python3'
PIN400=dict(step=400,member_directory='m400',object='q8/8865619b/673bc60f_m400.tar',archive_bytes=21583040512,
            archive_sha256='a'*64,done='/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m400.done')

def sha(b):return hashlib.sha256(b).hexdigest()
def build(tmp,*extra):
 out=tmp/'b';B.main(['--a4',str(A4),'--a',str(A),'--out',str(out),*extra]);return out

def test_null_fork_reproduces_a4():
 proof=B.null_fork(A4)
 assert proof=={'delivery_identical':True,'members_identical':True,'delivery_sha256':B.A4_DELIVERY_SHA256,'members':15}

def test_proof_build_seal():
 d,p,b=B.load_a4(A4);raw=(BUILD/'1.tgz').read_bytes();op=(BUILD/'tower_sequence.py').read_bytes()
 record=B.verify(raw,d,op)
 assert record['changed_payload']==['9.json']
 assert record['changed_delivery']==['0.json','0.tgz','BATCH.sh','CONFIG.json','PACKAGE.json','a/6.py']
 new=B.unpack(raw)
 for n,v in new.items():assert (BUILD/'package'/n).read_bytes()==v,n
 cfg,old=json.loads(B.unpack(new['0.tgz'])['9.json']),json.loads(p['9.json'])
 assert {k for k in cfg if cfg[k]!=old[k]}=={'token'}

def test_repin_with_a4_values_is_exact(tmp_path):
 pin=dict(step=200,member_directory='m200',object='q8/8865619b/673bc60f_m200.tar',archive_bytes=21583032320,
          archive_sha256='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b',
          done='/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m200.done',part_bytes=5395758080)
 (tmp_path/'pin.json').write_text(json.dumps(pin))
 out=build(tmp_path,'--token',(BUILD/'TOKEN').read_text().strip(),'--export-pin',str(tmp_path/'pin.json'))
 assert (out/'1.tgz').read_bytes()==(BUILD/'1.tgz').read_bytes()
 for n in ('o_place.sh','o_pullfill.sh','o_pullfill_resume.sh','o_cpucheck.sh','o_sub.sh','o_fetch.sh'):
  assert (out/n).read_bytes()==(BUILD/n).read_bytes(),n

def test_repin_400(tmp_path):
 (tmp_path/'pin.json').write_text(json.dumps(PIN400))
 out=build(tmp_path,'--export-pin',str(tmp_path/'pin.json'))
 d=B.unpack((out/'1.tgz').read_bytes());a4=B.unpack((A4/'1.tgz').read_bytes())
 lines=[l for l in difflib.unified_diff(a4['a/4.py'].decode().splitlines(),d['a/4.py'].decode().splitlines(),n=0) if l[:1] in '+-' and l[:3] not in ('+++','---')]
 assert lines==["-REVIEWED_OBJECT = 'q8/8865619b/673bc60f_m200.tar'","-REVIEWED_ARCHIVE_BYTES = 21583032320",
   "-REVIEWED_ARCHIVE_SHA256 = '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'",
   "+REVIEWED_OBJECT = 'q8/8865619b/673bc60f_m400.tar'","+REVIEWED_ARCHIVE_BYTES = 21583040512","+REVIEWED_ARCHIVE_SHA256 = '"+'a'*64+"'"]
 b=json.loads(B.unpack(d['0.tgz'])['9.json'])['export_binding'];old=json.loads(B.unpack(a4['0.tgz'])['9.json'])['export_binding']
 assert {k for k in b if b[k]!=old[k]}=={'step','member_directory','object'} and b['step']==400
 place=(out/'o_place.sh').read_text();fill=(out/'o_pullfill.sh').read_text()
 assert "b['step']==400 and b['member_directory']=='m400'" in place
 assert 'OBJECT=q8/8865619b/673bc60f_m400.tar' in fill and 'gcs_673bc60f_m400.done' in fill and '--step 400' in fill
 assert "int(f[1])==21583040512 and f[2]=='"+'a'*64 in fill
 assert 'm200' not in fill+place and not (out/'o_pullfill_resume.sh').exists()
 plan=json.loads((out/'READ_PLAN.json').read_text());assert plan['export_binding']['step']==400 and plan['export_binding']['archive_sha256']=='a'*64
 (tmp_path/'4.py').write_bytes(d['a/4.py'])
 subprocess.run([PY36,'-m','py_compile',str(tmp_path/'4.py')],check=True)
 ledger=[json.loads(l) for l in (tmp_path/'TOKEN_LEDGER.jsonl').read_text().splitlines()]
 assert ledger[-1]['token']==(out/'TOKEN').read_text().strip() and 'step 400' in ledger[-1]['read']
 r=check_build.check(out);assert r['step']==400 and r['fill_pins_changed'] and r['binding_changed']==['member_directory','object','step']

def test_check_build_proof():
 r=check_build.check(BUILD)
 assert r['step']==200 and not r['fill_pins_changed'] and r['binding_changed']==[] and r['changed_payload']==['9.json']

@pytest.mark.parametrize('change,message',[
 (dict(member_directory='m401'),'Member directory'),(dict(object='q8/8865619b/673bc60f_m200.tar'),'Object must'),
 (dict(done='/tmp/x_m400.done'),'Completion receipt'),(dict(extra=1),'Unknown export pin'),
 (dict(archive_sha256='xyz'),'64 hex'),(dict(step='400'),'positive integer')])
def test_pin_validation(change,message):
 d,p,_=B.load_a4(A4);pin={**PIN400,**change}
 with pytest.raises(ValueError,match=message):B.repin(d,p,pin)

def test_scripts_parse():
 for s in sorted(BUILD.glob('o_*.sh')):
  subprocess.run(['bash','-n',str(s)],check=True)
  text=s.read_text()
  for i,code in enumerate(re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE\n",text,re.S)):
   compile(code,f'{s.name}:{i}','exec')
   subprocess.run([PY36,'-c',f'compile({code!r},"x","exec")'],check=True)
 for n in ('package/3.py','package/a/4.py','package/a/7.py','fetch_return.py','unpack_return.py'):
  subprocess.run([PY36,'-c',f'compile(open({str(BUILD/n)!r}).read(),"x","exec")'],check=True)

def test_operator_diff_is_the_two_arm_read():
 old=(A4/'tower_sequence.py').read_text().splitlines();new=(BUILD/'tower_sequence.py').read_text().splitlines()
 changed=[l for l in difflib.unified_diff(old,new,n=0) if l[:1] in '+-' and l[:3] not in ('+++','---')]
 assert len(changed)<70
 mod={};exec(compile((BUILD/'tower_sequence.py').read_text(),'op','exec'),mod)
 assert mod['SCHEDULE']==((0,0),(0,1),(0,2)) and mod['ARMS']==['tower','own'] and mod['EXPECTED']==900
 spec=mod['descriptors'](None)[0];a4={};exec(compile('\n'.join(old),'a4','exec'),a4);s4=a4['descriptors'](None)[0]
 for k in ('modes','stage1_select_rule','save_own_depth','perception_memo','perception_memo_modules','perception_memo_verify_ids'):assert spec[k]==s4[k],k
 assert spec['types']==[0,1,2] and spec['arms']==['tower','own']

def test_verify_delivery_ported():
 """out3 verify_delivery.py checks that apply to a fork of A4."""
 d=B.unpack((BUILD/'1.tgz').read_bytes());p=B.unpack(d['0.tgz']);old=B.unpack(B.unpack((A4/'1.tgz').read_bytes())['0.tgz'])
 cfg=json.loads(p['9.json']);public=json.loads(d['0.json']);plan=json.loads((BUILD/'READ_PLAN.json').read_text())
 assert d['0.tgz']==(BUILD/'0.tgz').read_bytes() and d['PACKAGE.json']==(BUILD/'PACKAGE.json').read_bytes()
 assert p['9.json']==(BUILD/'src/9.json').read_bytes()
 for n,pin in cfg['payload_pins'].items():assert pin==dict(bytes=len(p[n]),sha256=sha(p[n])),n
 for n in p:
  if n!='9.json':assert old[n]==p[n],n
 assert plan['token']==public['token']==cfg['token']==(BUILD/'TOKEN').read_text().strip() and re.fullmatch('[a-f][0-9a-f]{12}',cfg['token'])
 a4=B.unpack((A4/'1.tgz').read_bytes())
 assert d['a/4.py']==a4['a/4.py'] and d['a/5.py']==a4['a/5.py'] and d['a/6.py']==(BUILD/'tower_sequence.py').read_bytes()
 manifest=json.loads(p['items/devs1_routed.json']);types=[cfg['order'][i] for i in plan['read_settings'][0]['types']]
 ids=[it['id'] for t in types for it in sorted(manifest['items'],key=lambda x:x['id']) if it['question_type']==t]
 assert ids==plan['item_ids_in_execution_order'] and len(ids)==450
 assert cfg['budget_gpu_seconds']==18000 and plan['walltime']=='05:00:00'
 helpers=['src/8.py','src/orchard_h10/common.py','src/orchard_h10/export_pins.py','src/orchard_h10/job.py','src/orchard_h10/vendor/export_stage.py',
          'src/orchard_h10/vendor/orchard_job.py','src/orchard_h10/vendor/orchard_launcher.py','src/orchard_h10/vendor/orchard_results.py',
          'package/a/4.py','package/a/5.py','tower_sequence.py','package/3.py','fetch_return.py','unpack_return.py']
 code='import sys\nfrom pathlib import Path\nfor p in sys.argv[1:]:compile(Path(p).read_bytes(),p,"exec")\nprint(sys.version.split()[0])'
 r=subprocess.run([PY36,'-I','-s','-B','-c',code]+[str(BUILD/n) for n in helpers],capture_output=True,text=True)
 assert r.returncode==0 and r.stdout.strip()=='3.6.8',r.stderr
 line=next(s for s in (BUILD/'o_place.sh').read_text().splitlines() if s.startswith('[[ "$D"'))
 for val,ok in [('/project/community/jjyeung/okh7/a15_cot_ap0123af',True),('/project/community/jjyeung/okh7/a15_cot_apbad/name',False),
                ('/project/community/jjyeung/okh7/a15_cot_apXYZ',False),('/tmp/a15_cot_ap0123af',False)]:
  assert (subprocess.run(['bash','-c',line],env=dict(os.environ,D=val)).returncode==0)==ok
 pull=(BUILD/'o_pullfill.sh').read_text();assert pull.count('gsutil -o Boto:num_retries=0')==1 and 'for i in 0 1 2 3; do' in pull
 import ast
 node=ast.parse(next(s for s in pull.splitlines() if s.startswith('assert int(f[1])')))
 for n,h,ok in [(21583032320,'795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b',True),(21583032320,'795ef9ef'+'0'*56,False),(1,'0'*64,False)]:
  try:exec(compile(node,'done guard','exec'),{'f':['q8/8865619b/673bc60f_m200.tar',str(n),h]});passed=True
  except AssertionError:passed=False
  assert passed==ok

def test_plan_matches_a4_camera_order():
 plan=json.loads((BUILD/'READ_PLAN.json').read_text())
 assert plan['item_order_matches_a4_camera_read'] is True and plan['item_sets']=={'dev-S1':450} and plan['expected']==[900]
 assert plan['operator_sha256']==sha((BUILD/'tower_sequence.py').read_bytes())==sha((BUILD/'package/a/6.py').read_bytes())

def test_vendor_and_refs():
 out3s=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops16/work/c15/r1route/out3s')
 assert (KIT/'vendor/score_r5.py').read_bytes()==(out3s/'score_r5.py').read_bytes()
 assert (KIT/'vendor/tower_pair.py').read_bytes()==(out3s/'A/tower_pair.py').read_bytes()
 refs,rows=ownread.references()
 assert {k:len(v) for k,v in rows.items()}=={'tower200':450,'tower544':450,'own544':450}
 for name,r in refs.items():
  for j in r['source_journals']:
   if Path(j['path']).exists():assert sha(Path(j['path']).read_bytes())==j['sha256']

def strict(tmp_path):
 src=PROOF/'ret_strict'
 if not src.is_dir():pytest.skip('run tests/cpu_proof.py first')
 dest=tmp_path/'ret';shutil.copytree(src,dest);return dest

def journal(root,t):return root/'metadata/reads/0/metadata/journals'/str(t)/'0/items.jsonl'

def test_scorer_accepts_strict(tmp_path):
 r=ownread.score(strict(tmp_path),BUILD,False)
 assert r['all_complete'] and r['types']['camera_movement_direction']['own_minus_tower']['value']==pytest.approx(-19.333333,abs=1e-4)

def drop_own(root,t):
 p=journal(root,t);p.write_text(''.join(l+'\n' for l in p.read_text().splitlines() if json.loads(l)['arm']!='own'))

def cli(root,out,*extra):
 return subprocess.run([sys.executable,'-B',str(KIT/'ownread.py'),'--root',str(root),'--package',str(BUILD),'--out',str(out),*extra],
                       capture_output=True,text=True)

def test_scorer_refuses_partial_return(tmp_path):
 root=strict(tmp_path);drop_own(root,0)
 refs,_=ownread.references()
 with pytest.raises(ValueError,match=r'Incomplete paired set \(camera_displacement tower 150/150, own 0/150\)'):ownread.load(root,BUILD,refs,False)
 with pytest.raises(ValueError,match='Incomplete paired set'):ownread.score(root,BUILD,False)
 r=cli(root,tmp_path/'score')
 assert r.returncode==2 and r.stdout=='' and r.stderr.startswith('ownread refused: Incomplete paired set') and r.stderr.count('\n')==1
 assert not (tmp_path/'score').exists()

def test_scorer_refuses_missing_journal_rows(tmp_path):
 root=strict(tmp_path);journal(root,2).write_text('')
 with pytest.raises(ValueError,match=r'camera_movement_direction tower 0/150, own 0/150'):ownread.score(root,BUILD,False)

def test_allow_partial_is_diagnostic(tmp_path):
 root=strict(tmp_path);drop_own(root,0)
 r=cli(root,tmp_path/'score','--allow-partial');assert r.returncode==0,r.stderr
 lines=r.stdout.splitlines();assert len(lines)>20 and all(l.startswith('PARTIAL') for l in lines)
 assert (tmp_path/'score/ownread.txt').read_text()==r.stdout
 v=json.loads((tmp_path/'score/ownread.json').read_text())
 assert v['partial'] is True and v['all_complete'] is False and v['all_within_bar_point'] is None and v['all_within_bar_interval'] is None
 t=v['types']['camera_displacement'];assert t['own_n']==0 and t['tower_n']==150 and t['within_bar_interval'] is None
 assert v['types']['camera_rotation']['complete'] is True

def test_allow_partial_withholds_decision_on_complete_return(tmp_path):
 r=ownread.score(strict(tmp_path),BUILD,False,allow_partial=True)
 assert r['all_complete'] and r['partial'] and r['all_within_bar_point'] is None and r['all_within_bar_interval'] is None
 assert all(l.startswith('PARTIAL') for l in ownread.text(r).splitlines())

def test_strict_return_is_not_partial(tmp_path):
 r=cli(strict(tmp_path),tmp_path/'score');assert r.returncode==0,r.stderr
 assert 'PARTIAL' not in r.stdout and json.loads((tmp_path/'score/ownread.json').read_text())['partial'] is False

def edit_json(p,change):
 v=json.loads(p.read_text());change(v);p.write_text(json.dumps(v))

def move_row(root):
 """Move one planned type-1 row into type 0's journal."""
 src,dst=journal(root,1),journal(root,0);rows=src.read_text().splitlines()
 src.write_text(''.join(l+'\n' for l in rows[1:]));dst.write_text(dst.read_text()+rows[0]+'\n')

def env_of(root,t):return journal(root,t).parent/'environment.json'

def reorder(b):b['ids']=b['ids'][::-1]

def add_unplanned_journal(root):
 d=journal(root,3).parent;d.mkdir(parents=True)
 for n in ('environment.json','items.jsonl'):(d/n).write_bytes((journal(root,0).parent/n).read_bytes())

def change_inputs(root,rebind):
 p=root/'metadata/INPUTS.json';edit_json(p,lambda v:v['archives'][0].update(sha256='0'*64))
 if rebind:
  v=json.loads(p.read_text());edit_json(root/'metadata/IDENTITY.json',lambda i:i.update(inputs=ownread.canonical({k:x for k,x in v.items() if k!='resume'})))

@pytest.mark.parametrize('case,message',[
 ('archive_pin','Export binding differs: archive_sha256'),
 ('room','Pair metadata differs'),
 ('mixed_export','Mixed journals'),
 ('journal_ids','Journal ids differ from its planned members: 0/0'),
 ('ids_other_type','Journal ids differ from its planned members: 0/0'),
 ('ids_reordered','Journal ids differ from its planned members: 0/0'),
 ('ids_extra','Journal ids differ from its planned members: 0/0'),
 ('row_outside_ids','Row outside its journal ids: 0/0'),
 ('shard','Journal shard differs from its directory: 0/0'),
 ('unplanned_journal','Unplanned journal: 3/0'),
 ('inputs_identity','Return inputs differ from its identity'),
 ('inputs_archive','Input export archive differs from the plan')])
@pytest.mark.parametrize('allow_partial',[False,True])
def test_scorer_refuses_mismatched_metadata(tmp_path,case,message,allow_partial):
 root=strict(tmp_path);p=journal(root,0)
 if case=='archive_pin':edit_json(root/'metadata/EXPORT_PIN.json',lambda v:v.update(archive_sha256='0'*64))
 if case=='room':
  rows=p.read_text().splitlines();v=json.loads(rows[0]);v['room_key']='deliberate-mismatch';rows[0]=json.dumps(v);p.write_text('\n'.join(rows)+'\n')
 if case=='mixed_export':edit_json(env_of(root,0),lambda v:v['binding'].update(export_sha256='0'*64))
 if case=='journal_ids':edit_json(env_of(root,0),lambda v:v['binding'].update(ids=[]))
 if case=='ids_other_type':
  other=json.loads(env_of(root,1).read_text())['binding']['ids'];edit_json(env_of(root,0),lambda v:v['binding'].update(ids=other))
 if case=='ids_reordered':edit_json(env_of(root,0),lambda v:reorder(v['binding']))
 if case=='ids_extra':
  other=json.loads(env_of(root,1).read_text())['binding']['ids'];edit_json(env_of(root,0),lambda v:v['binding'].update(ids=v['binding']['ids']+other[:1]))
 if case=='row_outside_ids':move_row(root)
 if case=='shard':edit_json(env_of(root,0),lambda v:v['binding'].update(shard='0/2'))
 if case=='unplanned_journal':add_unplanned_journal(root)
 if case in ('inputs_identity','inputs_archive'):change_inputs(root,case=='inputs_archive')
 refs,_=ownread.references()
 with pytest.raises(ValueError,match=re.escape(message)):ownread.load(root,BUILD,refs,False,**({'allow_partial':True} if allow_partial else {}))
 if not allow_partial:
  r=cli(root,tmp_path/'score');assert r.returncode==2 and r.stderr=='ownread refused: '+message+'\n' and not (tmp_path/'score').exists()

@pytest.mark.parametrize('edit,message',[
 ('duplicate','Duplicate'),('arm','wrong-arm'),('tail','Uncommitted tail'),('settings','Journal binding differs: settings_sha256'),('arms','Journal binding differs: arms')])
def test_scorer_refusals(tmp_path,edit,message):
 root=strict(tmp_path);p=journal(root,0);text=p.read_text();env=p.parent/'environment.json'
 if edit=='duplicate':p.write_text(text+text.splitlines()[0]+'\n')
 if edit=='arm':
  r=json.loads(text.splitlines()[0]);r['arm']='donor';p.write_text(json.dumps(r)+'\n'+text)
 if edit=='tail':p.write_text(text.rstrip('\n'))
 if edit in ('settings','arms'):
  e=json.loads(env.read_text())
  if edit=='settings':e['settings']['perception_memo']='off';e['binding']['settings_sha256']=ownread.canonical(e['settings'])
  else:e['binding']['arms']=['tower']
  env.write_text(json.dumps(e))
 with pytest.raises(ValueError,match=message):ownread.score(root,BUILD,False)
