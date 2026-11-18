"""Exercise the complete canary wrapper with local Slurm and gate stubs."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from packet_config import PINS,MEMBERS,ARCHIVE,fixture
W=Path(__file__).resolve().parent
T=Path(tempfile.mkdtemp(prefix='canary_p7_',dir=W));mock=T/'bin';mock.mkdir()
scripts={
 'squeue':'[[ "$TZ" == UTC && "$QUEUE_ERROR" == 0 ]] || exit 9\nif [[ "$*" == *"%l|%b|%r"* ]]; then printf "%s\\n" "$PROOF_DETAIL"; else printf "%s\\n" "$QUEUE"; fi\n',
 'sacct':'[[ "$TZ" == UTC && "$HISTORY_ERROR" == 0 ]] || exit 9\nprintf "%s\\n" "$HISTORY"\n',
 'bash':'''[[ "$1" == s.sh && "$ADMISSION_JOB" == 170956 && "$PROOF_JOB" == 171500 ]] || exit 9
printf '%s\\n' called >> "$CALLED"
"'''+sys.executable+'''" -B - <<'PY'
import json,os
from pathlib import Path
p=Path(os.environ['TEST_K'])/'o'/(os.environ['PROOF_JOB']+'.canary.json')
with p.open('x') as f: json.dump(dict(canary=True,proof_job=os.environ['PROOF_JOB'],admission_job='170956',submission='GATE_ACCEPTED'),f)
PY
[[ "$GATE_ERROR" == 0 ]] || exit 8
printf '%s\\n' "$SUBMIT_OUTPUT"
'''}
for name,body in scripts.items():
 p=mock/name;p.write_text('#!/bin/bash\n'+body);p.chmod(0o700)
source=fixture();passed=[]
(T/'packet.tar').write_bytes(ARCHIVE)
def case(name,okay,queue=None,history='',jobid='171500',pre=None,repeat=False,**overrides):
 root=T/name;root.mkdir(mode=0o700)
 b=root/'i_69d2930d';b.mkdir(mode=0o700);k=root/'x_69d2930d';k.mkdir(mode=0o700);(k/'o').mkdir(mode=0o700)
 for member in MEMBERS:
  p=b/member;p.parent.mkdir(parents=True,exist_ok=True);os.link(source/member,p)
 os.link(T/'packet.tar',b/'p.tar')
 (k/'SHA256SUMS.txt').write_text('LOCAL TEST MANIFEST\n')
 if jobid is not None:(b/'job.id').write_text(jobid+'\n')
 (b/'sbatch.out').write_text('171500;testcluster\n');(b/'submission.started').write_text('proof attempt\n')
 ids=json.loads(MEMBERS['ids.json'])
 go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],wrapper_sha256=hashlib.sha256(MEMBERS['jb.sh']).hexdigest(),manifest_sha256=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest(),authority='sha256:'+'a'*64,canary=True)
 if pre=='equal':(b/'go.json').write_text(json.dumps(go,sort_keys=True))
 if pre=='differs':(b/'go.json').write_text('{}')
 if pre=='started':(b/'training.started').write_text('existing attempt')
 if pre=='marker':(k/'o/171500.canary.json').write_text('{}')
 script=root/'submit.sh';script.write_text((W/'go_submit_canary_9dd2fbb7.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)).replace('python3 -I -B',sys.executable+' -I -B'))
 env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',QUEUE=queue if queue is not None else '171500|PENDING|a15_cot_ap673bc60f',HISTORY=history,PROOF_DETAIL='171500|6:00:00|N/A|None',QUEUE_ERROR='0',HISTORY_ERROR='0',GATE_ERROR='0',SUBMIT_OUTPUT='Submitted batch job 171501',CALLED=str(root/'called'),TEST_K=str(k))
 env.update(overrides)
 result=subprocess.run(['/bin/bash',str(script),'171500','a'*64],env=env,capture_output=True,text=True)
 assert (result.returncode==0)==okay,(name,result.stdout,result.stderr)
 if okay:
  assert json.loads((b/'go.json').read_text())==go
  assert (b/'training.job.id').read_text()=='171501\n'
  record=json.loads((b/'training.json').read_text());assert record['proof_job']=='171500' and record['training_job']=='171501'
  assert record['gate_marker_sha256']==hashlib.sha256((k/'o/171500.canary.json').read_bytes()).hexdigest()
  if pre=='equal':assert 'byte-equal' in result.stdout
  assert (b/'training.started').exists()
 elif overrides.get('GATE_ERROR')!='1' and 'SUBMIT_OUTPUT' not in overrides:
  assert not (root/'called').exists(),name
 if repeat:
  second=subprocess.run(['/bin/bash',str(script),'171500','a'*64],env=env,capture_output=True,text=True)
  assert second.returncode!=0 and (root/'called').read_text().splitlines()==['called']
  assert 'already exists' in second.stdout
 if pre=='differs':assert (b/'go.json').read_text()=='{}'
 passed.append(name);print('PASS',name)
case('pending',True,repeat=True)
case('running',True,queue='171500|RUNNING|a15_cot_ap673bc60f')
case('equal_go',True,pre='equal')
case('proof_accounting',True,history='170956|a15_cot_ap673bc60f|FAILED\n171500|a15_cot_ap673bc60f|RUNNING')
case('missing_job',False,queue='')
case('completed_job',False,queue='171500|COMPLETED|a15_cot_ap673bc60f')
case('failed_job',False,queue='171500|FAILED|a15_cot_ap673bc60f')
case('wrong_job_id',False,jobid='171499')
case('missing_job_id',False,jobid=None)
case('extra_job',False,queue='171500|PENDING|a15_cot_ap673bc60f\n171600|RUNNING|a15_cot_ap673bc60f')
case('extra_pending',False,queue='171500|PENDING|a15_cot_ap673bc60f\n171600|PENDING|a15_cot_ap673bc60f')
case('wrong_name',False,queue='171500|PENDING|wrong')
case('duplicate_rows',False,queue='171500|PENDING|a15_cot_ap673bc60f\n171500|PENDING|a15_cot_ap673bc60f')
case('second_submit',False,pre='started')
case('gate_marker',False,pre='marker')
case('history_completed',False,history='171600|a15_cot_ap673bc60f|COMPLETED')
case('history_failed',False,history='171600|a15_cot_ap673bc60f|FAILED')
case('different_go',False,pre='differs')
case('queue_error',False,QUEUE_ERROR='1')
case('history_error',False,HISTORY_ERROR='1')
case('bad_history',False,history='unparseable')
case('gpu_proof',False,PROOF_DETAIL='171500|6:00:00|gpu:4|None')
case('wrong_timelimit',False,PROOF_DETAIL='171500|13:00:00|N/A|None')
case('held_proof',False,PROOF_DETAIL='171500|6:00:00|N/A|JobHeldUser')
case('unresolved_dependency',False,PROOF_DETAIL='171500|6:00:00|N/A|DependencyNeverSatisfied')
case('gate_error',False,GATE_ERROR='1',repeat=True)
case('uncertain_sbatch',False,SUBMIT_OUTPUT='unparseable',repeat=True)
assert '-p advanced' in MEMBERS['s.sh'].decode() and '--gres=gpu:4' in MEMBERS['s.sh'].decode() and '-t 13:00:00' in MEMBERS['s.sh'].decode()
print('PASS',len(passed),'canary wrapper cases; successful and uncertain attempts refuse repetition; sealed advanced/4 GPU/13 h sbatch retained')
