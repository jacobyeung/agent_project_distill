"""Run driver guard branches locally with fake Slurm commands; never contact Slurm."""
import os,subprocess,tempfile
from pathlib import Path
from packet_config import PINS
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='guards_',dir=W));mock=T/'bin';mock.mkdir()
def exe(n,s):p=mock/n;p.write_text('#!/bin/bash\n'+s);p.chmod(0o700)
exe('squeue','printf "%s\\n" "$TEST_QUEUE"\n')
exe('python3','if [[ "$*" == *" - "* ]]; then cat > /dev/null; fi\nexit 0\n')
exe('sbatch','printf "called\\n" >> "$TEST_CALLED"\nprintf "123456;testcluster\\n"\n')
cases=[('pending_advanced','10|a15_cot_apdeadbeef|advanced|PENDING',False),('same_name_general','11|a15_cot_ap26cc98b7|general|RUNNING',False),('pending_general','12|a15_cot_apdeadbeef|general|PENDING',True),('running_advanced','13|a15_cot_apdeadbeef|advanced|RUNNING',True),('empty','',True)]
for name,queue,allowed in cases:
 root=T/name;root.mkdir(mode=0o700);(root/'i_c5f3847d').mkdir(mode=0o700);(root/'x_c5f3847d').mkdir(mode=0o700)
 script=root/'p.sh';script.write_text((W/'pr1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
 marker=root/'called';env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',USER='localtest',TEST_QUEUE=queue,TEST_CALLED=str(marker))
 r=subprocess.run(['bash',str(script)],env=env,capture_output=True,text=True)
 assert (r.returncode==0)==allowed,(name,r.stdout,r.stderr)
 assert marker.exists()==allowed
 if allowed:
  assert (root/'i_c5f3847d/job.id').read_text().strip()=='123456'
  again=subprocess.run(['bash',str(script)],env=env,capture_output=True,text=True)
  assert again.returncode!=0 and marker.read_text()=='called\n'
 print('PASS',name,'submit' if allowed else 'refuse')
print('PASS repeat submissions refused; every sbatch was a local stub')
