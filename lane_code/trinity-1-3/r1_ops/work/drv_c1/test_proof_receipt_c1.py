"""Only successful parsable sbatch output may create job.id."""
from pathlib import Path
import os,subprocess,tempfile
from packet_config import PINS
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='receipt_c1_',dir=W));mock=T/'bin';mock.mkdir()
for name,body in {
 'sha256sum':'cat >/dev/null; exit 0',
 'squeue':'exit 0',
 'python3':'if [[ " $* " == *" - "* ]]; then cat >/dev/null; fi; exit 0',
 'sbatch':'printf "%s\\n" "$*" >> "$CALLED"; printf "%s" "$ANSWER"; exit "$RC"'
}.items():
 p=mock/name;p.write_text('#!/bin/bash\n'+body+'\n');p.chmod(0o700)
for label,answer,rc,okay in [('plain','171500\n','0',True),('cluster','171500;local\n','0',True),('zero','0\n','0',False),('human','Submitted batch job 171500\n','0',False),('multiple','171500\n171501\n','0',False),('failure','171500\n','1',False)]:
 root=T/label;root.mkdir(mode=0o700);b=root/Path(PINS['bundle']).name;b.mkdir(mode=0o700);(root/Path(PINS['kit']).name).mkdir(mode=0o700)
 script=root/'pr1.sh';script.write_text((W/'pr1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
 env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',ANSWER=answer,RC=rc,CALLED=str(root/'called'))
 result=subprocess.run(['/bin/bash',str(script)],capture_output=True,text=True,env=env)
 assert (result.returncode==0)==okay,(label,result.stdout,result.stderr)
 assert (b/'job.id').exists()==okay
 if okay:assert (b/'job.id').read_text()=='171500\n'
 assert (b/'submission.started').exists()
 assert '--parsable' in (root/'called').read_text()
 again=subprocess.run(['/bin/bash',str(script)],capture_output=True,text=True,env=env)
 assert again.returncode and len((root/'called').read_text().splitlines())==1
 print('PASS',label,'valid job.id' if okay else 'no job.id; attempt retained')
