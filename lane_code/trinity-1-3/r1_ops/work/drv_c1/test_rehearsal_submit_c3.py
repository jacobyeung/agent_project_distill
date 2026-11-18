"""Check rehearsal ledger, one-shot submission, and uncertain-output refusal."""
import os,subprocess,sys,tempfile
from pathlib import Path
from packet_config import ARCHIVE
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='rehearsal_c3_',dir=W));bin=T/'bin';bin.mkdir();(bin/'python3').symlink_to(sys.executable)
for name,body in {'squeue':'printf "%s" "$QUEUE"','sbatch':'printf "%s\\n" "$*" >> "$CALLED"\nprintf "%s\\n" "$ANSWER"'}.items():
 p=bin/name;p.write_text('#!/bin/bash\n'+body+'\n');p.chmod(0o700)
archive=T/'p.tar';archive.write_bytes(ARCHIVE)
for label in ('success','uncertain','queued'):
 root=T/label;root.mkdir(mode=0o700);b=root/'i_7f1589c1';k=root/'x_7f1589c1';b.mkdir();k.mkdir();(k/'o').mkdir();os.link(archive,b/'p.tar')
 script=root/'rh1.sh';script.write_text((W/'rh1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)).replace('/usr/bin/python3 -I -B "$BUN/p.py"','true'))
 env=dict(os.environ,PATH=str(bin)+':/usr/bin:/bin',QUEUE='172180|a15_cot_ap05b8ac69|general|PENDING' if label=='queued' else '',ANSWER='Submitted batch job 172999' if label!='uncertain' else 'UNCERTAIN',CALLED=str(root/'called'))
 result=subprocess.run(['/bin/bash',str(script)],env=env,capture_output=True,text=True)
 assert (result.returncode==0)==(label=='success'),result.stderr
 assert not (b/'job.id').exists(),'rehearsal must never become full proof'
 if label=='success':assert (b/'rehearsal.job.id').read_text().strip()=='172999' and (b/'rehearsal.json').exists()
 if label=='uncertain':assert (b/'rehearsal.started').exists() and not (b/'rehearsal.job.id').exists()
 if label!='queued':
  again=subprocess.run(['/bin/bash',str(script)],env=env,capture_output=True,text=True)
  assert again.returncode and len((root/'called').read_text().splitlines())==1
 print('PASS rehearsal submission',label)
print('PASS rehearsal has a separate ledger and cannot overwrite bundle job.id')
