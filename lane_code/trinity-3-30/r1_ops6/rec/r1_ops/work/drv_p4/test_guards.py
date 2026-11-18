"""Exercise partition guards with local stubs; never contact Slurm."""
import os,subprocess,tempfile
from pathlib import Path
from packet_config import PINS
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='guards_p4_',dir=W));mock=T/'bin';mock.mkdir()
def exe(n,s):
 p=mock/n;p.write_text('#!/bin/bash\n'+s);p.chmod(0o700)
exe('squeue','[[ \" $* \" != *\" -u \"* ]] || exit 12\n[[ ${TEST_QUEUE_FAIL:-0} == 0 ]] || exit 9\nprintf "%s\\n" "$TEST_QUEUE"\n')
exe('python3','printf "%s\\n" "$*" >> "$TEST_PY"\nif [[ "$*" == *" - "* ]]; then cat > /dev/null; fi\nexit 0\n')
exe('sbatch','printf "%s\\n" "$*" >> "$TEST_CALLED"\nprintf "123456;testcluster\\n"\n')
cases=[
 ('pending_general','10|a15_cot_apdeadbeef|general|PENDING',[],False),
 ('running_general','11|a15_cot_apdeadbeef|general|RUNNING',[],False),
 ('main_general','12|jjy_main|general|COMPLETING',[],False),
 ('main_pending','12|jjy_main|general|PENDING',[],False),
 ('main_advanced','12|jjy_main|advanced|RUNNING',['advanced'],False),
 ('proof_advanced','12|a15_cot_apdeadbeef|advanced|RUNNING',['advanced'],False),
 ('mixed_partition','12|jjy_main|advanced,general|PENDING',[],False),
 ('default_marker','12|jjy_main|general*|RUNNING',[],False),
 ('same_name','13|a15_cot_ap'+PINS['run']+'|advanced|RUNNING',[],False),
 ('other_partition','14|a15_cot_apdeadbeef|advanced|RUNNING',[],True),
 ('unrelated_job','15|something_else|general|RUNNING',[],True),
 ('empty','',[],True),('explicit_general','',['general'],True),
 ('explicit_advanced','',['advanced'],True),('invalid','',['preempt'],False),
 ('extra_argument','',['general','extra'],False),('queue_failure','',[],False)]
for name,queue,args,allowed in cases:
 root=T/name;root.mkdir(mode=0o700)
 bun=root/Path(PINS['bundle']).name;bun.mkdir(mode=0o700)
 (root/Path(PINS['kit']).name).mkdir(mode=0o700)
 script=root/'p.sh';script.write_text((W/'pr1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
 marker=root/'called';pylog=root/'py';env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',USER='localtest',TEST_QUEUE=queue,TEST_CALLED=str(marker),TEST_PY=str(pylog),TEST_QUEUE_FAIL='1' if name=='queue_failure' else '0')
 r=subprocess.run(['bash',str(script)]+args,env=env,capture_output=True,text=True)
 assert (r.returncode==0)==allowed,(name,r.stdout,r.stderr)
 assert marker.exists()==allowed
 if allowed:
  partition=args[0] if args else 'general'
  assert (bun/'job.id').read_text().strip()=='123456'
  assert ' -p '+partition+' ' in ' '+marker.read_text()+' '
  assert '--partition '+partition in pylog.read_text()
  again=subprocess.run(['bash',str(script)]+args,env=env,capture_output=True,text=True)
  assert again.returncode!=0 and len(marker.read_text().splitlines())==1
 print('PASS',name,'submit' if allowed else 'refuse')
print('PASS partition reaches p.py and sbatch; repeat submission refused; all commands were local stubs')
# pm1 must read the same job.id, not any copied job2.id.
exe('squeue','printf \"%s\\n\" \"$TEST_QUEUE\"\n')
root=T/'empty';bun=root/Path(PINS['bundle']).name
(bun/'job2.id').write_text('654321\n')
script=root/'m.sh';script.write_text((W/'pm1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',USER='localtest',TEST_QUEUE='',TEST_PY=str(root/'monitor_args'))
subprocess.run(['bash',str(script)],check=True,env=env,capture_output=True,text=True)
assert '123456' in (root/'monitor_args').read_text() and '654321' not in (root/'monitor_args').read_text()
print('PASS pm1 reads the proof-2 job.id')
