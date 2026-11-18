"""Read-only monitor and proof-fetch checks against local synthetic records."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from packet_config import PINS
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='monitor_c1_',dir=W))
root=T/'remote';root.mkdir(mode=0o700);b=root/Path(PINS['bundle']).name;b.mkdir(mode=0o700);k=root/Path(PINS['kit']).name;k.mkdir(mode=0o700);(k/'o').mkdir()
mock=T/'bin';mock.mkdir();(mock/'python3').symlink_to(sys.executable)
for name,text in [('squeue','printf "171600 a15_cot_ap05b8ac69 advanced RUNNING\\n"'),('sacct','printf "%s\\n" "$*"')]:
 p=mock/name;p.write_text('#!/bin/bash\n'+text+'\n');p.chmod(0o700)
os.link(next(W.glob('training_c1_*/p.tar')),b/'p.tar')
(b/'job.id').write_text('171500\n');(b/'training.job.id').write_text('171600\n')
(b/'training.json').write_text('{"mode":"PASS"}')
(k/'o/171500.proof.json').write_text('{"status":"PASS","job":"171500"}')
(k/'o/171500.proof.log').write_text('LOCAL PROOF LOG\n')
(k/'o/171600.err').write_text('https://storage.googleapis.com/upload/FAKE_SECRET\n')
def snapshot():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
before=snapshot()
for name in ('pm1.sh','mon.sh','f2.sh'):
 p=T/name;p.write_text((W/name).read_text().replace('/project/community/jjyeung/okh7',str(root)))
 result=subprocess.run(['/bin/bash',str(p)],env=dict(os.environ,PATH=str(mock)+':/usr/bin:/bin',USER='localtest'),capture_output=True,text=True)
 assert result.returncode==0,(name,result.stdout,result.stderr)
 assert '171500' in result.stdout
 if name=='f2.sh':assert 'LOCAL PROOF LOG' in result.stdout and '"status":"PASS"' in result.stdout
 else:assert '171600' in result.stdout and 'FAKE_SECRET' not in result.stdout
 assert snapshot()==before,'Monitor mutated its inputs'
 print('PASS',name,'read-only C status/proof fetch')
