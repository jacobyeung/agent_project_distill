"""Local scheduler/gate stubs exercise C's PASS-only submission wrapper."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from packet_config import PINS,MEMBERS,ARCHIVE,fixture
W=Path(__file__).resolve().parent
T=Path(tempfile.mkdtemp(prefix='training_c1_',dir=W));mock=T/'bin';mock.mkdir()
# All actual Python processes use the required CPU environment.
(mock/'python3').symlink_to(sys.executable)
def exe(name,body):
 p=mock/name;p.write_text('#!/bin/bash\n'+body+'\n');p.chmod(0o700)
exe('squeue','[[ ${QUEUE_FAIL:-0} == 0 ]] || exit 9\nprintf "%s" "$QUEUE"')
exe('sacct','[[ ${HISTORY_FAIL:-0} == 0 ]] || exit 9\nif [[ " $* " == *" -j 171377 "* ]]; then printf "%s" "$DONOR"; else printf "%s" "$HISTORY"; fi')
exe('bash','[[ "$1" == s.sh ]] || exit 9\nprintf "%s\\n" "$PROOF_JOB" >> "$CALLED"\n[[ ${GATE_FAIL:-0} == 0 ]] || exit 7\nprintf "%s\\n" "$GATE_OUTPUT"')
archive=T/'p.tar';archive.write_bytes(ARCHIVE);source=fixture();proof_job='171500'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
base_env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',USER='localtest',QUEUE='',HISTORY='171500|a15_cot_ap05b8ac69|COMPLETED|0:0\n',DONOR='171377|a15_cot_ap673bc60f|COMPLETED|0:0\n',GATE_OUTPUT='Submitted batch job 171600')
cases=['history_donor_proof','history_other_c_proof','history_duplicate_proof','proof_queue_row','queued_proof_not_complete','success','equal_go','different_go','same_name_running','same_name_held','other_held','donor_held_proof','donor_running','donor_completing','donor_account_running','donor_account_pending','missing_donor_account','missing_slot','wrong_step','unverified_slot','bool_step','linked_slot','bad_proof','wrong_proof_job','old_proof_identity','missing_resume_check','history_training','history_empty','history_failed_proof','history_error','queue_error','malformed_queue','existing_marker','existing_job','existing_transcript','canary_marker','failed_gate','uncertain_gate','altered_gate','altered_sums','altered_wrapper']
if len(sys.argv)>1:cases=[x for x in cases if x in sys.argv[1:]]
for label in cases:
 root=T/label;root.mkdir(mode=0o700);b=root/Path(PINS['bundle']).name;b.mkdir(mode=0o700);k=root/Path(PINS['kit']).name;k.mkdir(mode=0o700);(k/'o').mkdir()
 for name in MEMBERS:
  p=b/name;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);os.link(source/name,p)
 os.link(archive,b/'p.tar');(b/'job.id').write_text(proof_job+'\n');(b/'sbatch.out').write_text(proof_job+';cluster\n');(b/'submission.started').write_text('LOCAL FIXTURE\n')
 (k/'SHA256SUMS.txt').write_text('LOCAL TEST MANIFEST\n')
 proof=dict(status='PASS',rc=0,job=proof_job,config_identity=PINS['identity'],checks=dict(resume_pointer=dict(status='PASS')))
 donor=root/'r/673bc60f';donor.mkdir(parents=True);record=dict(slot='A',verified=True,step=200)
 env=dict(base_env,CALLED=str(root/'called'))
 if label in ('proof_queue_row','queued_proof_not_complete'):env['QUEUE']='171500|a15_cot_ap05b8ac69|bootstrap|RUNNING|node\n'
 if label=='queued_proof_not_complete':env['HISTORY']=env['HISTORY'].replace('COMPLETED','RUNNING')
 if label=='same_name_running':env['QUEUE']='171601|a15_cot_ap05b8ac69|advanced|RUNNING|node\n'
 if label=='same_name_held':env['QUEUE']='171601|a15_cot_ap05b8ac69|advanced|PENDING|JobHeldUser\n'
 if label=='other_held':env['QUEUE']='167739|jjy_main|advanced|PENDING|JobHeldUser\n'
 if label=='donor_held_proof':env['QUEUE']='171356|a15_cot_ap673bc60f|general|PENDING|JobHeldUser\n'
 if label in ('donor_running','donor_completing'):env['QUEUE']='171377|a15_cot_ap673bc60f|advanced|'+('RUNNING' if label=='donor_running' else 'COMPLETING')+'|node\n'
 if label=='donor_account_running':env['DONOR']=env['DONOR'].replace('COMPLETED','RUNNING')
 if label=='donor_account_pending':env['DONOR']=env['DONOR'].replace('COMPLETED','PENDING')
 if label=='missing_donor_account':env['DONOR']=''
 if label=='wrong_step':record['step']=199
 if label=='bool_step':record['step']=True
 if label=='unverified_slot':record['verified']=False
 if label!='missing_slot':
  p=donor/'A.json'
  if label=='linked_slot':(root/'slot.json').write_text(json.dumps(record));p.symlink_to(root/'slot.json')
  else:p.write_text(json.dumps(record))
 if label=='bad_proof':proof['status']='FAIL'
 if label=='wrong_proof_job':proof['job']='171356'
 if label=='old_proof_identity':proof['config_identity']='0'*64
 if label=='missing_resume_check':proof['checks']={}
 (k/'o'/(proof_job+'.proof.json')).write_text(json.dumps(proof))
 if label=='history_training':env['HISTORY']+='171499|a15_cot_ap05b8ac69|FAILED|1:0\n'
 if label=='history_donor_proof':env['HISTORY']+='171356|a15_cot_ap05b8ac69|COMPLETED|0:0\n'
 if label=='history_other_c_proof':env['HISTORY']+='171501|a15_cot_ap05b8ac69|COMPLETED|0:0\n'
 if label=='history_duplicate_proof':env['HISTORY']+=env['HISTORY']
 if label=='history_empty':env['HISTORY']=''
 if label=='history_failed_proof':env['HISTORY']=env['HISTORY'].replace('COMPLETED','FAILED')
 if label=='history_error':env['HISTORY_FAIL']='1'
 if label=='queue_error':env['QUEUE_FAIL']='1'
 if label=='malformed_queue':env['QUEUE']='malformed\n'
 if label in ('existing_marker','existing_job','existing_transcript'):(b/{'existing_marker':'training.started','existing_job':'training.job.id','existing_transcript':'training.sbatch.out'}[label]).write_text('LOCAL FIXTURE\n')
 if label=='canary_marker':(k/'o'/'171499.canary.json').write_text('{}')
 if label=='failed_gate':env['GATE_FAIL']='1'
 if label=='uncertain_gate':env['GATE_OUTPUT']='UNCERTAIN LOCAL STUB'
 ids=json.loads(MEMBERS['ids.json']);go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],wrapper_sha256=sha(MEMBERS['jb.sh']),manifest_sha256=sha((k/'SHA256SUMS.txt').read_bytes()),authority='sha256:'+'a'*64)
 if label in ('equal_go','different_go'):
  if label=='different_go':go['authority']='sha256:'+'b'*64
  (b/'go.json').write_text(json.dumps(go,sort_keys=True))
 body=(W/'go_submit_6a5c7d00.sh').read_text().replace('/project/community/jjyeung/okh7',str(root))
 # Alter the expected pin only, without modifying shared hardlinked packet bytes.
 for item,member in [('altered_gate','s.sh'),('altered_sums','sums.txt'),('altered_wrapper','jb.sh')]:
  if label==item:body=body.replace(sha(MEMBERS[member]),'0'*64)
 script=root/'submit.sh';script.write_text(body)
 args=['/bin/bash',str(script),proof_job,'a'*64]
 result=subprocess.run(args,env=env,capture_output=True,text=True)
 okay=label in ('proof_queue_row','success','equal_go','other_held','donor_held_proof','donor_account_pending')
 assert (result.returncode==0)==okay,(label,result.stdout,result.stderr)
 (root/'result.txt').write_text(result.stdout+result.stderr)
 assert (root/'called').exists()==(okay or label in ('failed_gate','uncertain_gate')),label
 if okay:
  assert (b/'training.job.id').read_text().strip()=='171600'
  assert json.loads((b/'training.json').read_text())['mode']=='PASS'
  assert json.loads((b/'go.json').read_text())==go
  assert 'canary' not in json.loads((b/'go.json').read_text())
  if label=='equal_go':assert 'byte-equal' in result.stdout
  again=subprocess.run(args,env=env,capture_output=True,text=True)
  assert again.returncode and (root/'called').read_text().splitlines()==[proof_job]
 if label in ('failed_gate','uncertain_gate'):
  assert (b/'training.started').exists() and not (b/'training.job.id').exists()
  again=subprocess.run(args,env=env,capture_output=True,text=True)
  assert again.returncode and (root/'called').read_text().splitlines()==[proof_job]
 print('PASS',label,'submit' if okay else 'refuse')
for part in ('-p advanced','--gres=gpu:4','-t 24:00:00'):
 assert part in MEMBERS['s.sh'].decode() and part in MEMBERS['jb.sh'].decode()
print('PASS sealed C training pins: advanced, four GPUs, 24 hours; all commands local stubs')
print('Test artifacts:',T)
