"""Small fixture tests for move-aside, rehearsal, history, and canary guards."""
import errno,hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
from packet_config import PINS,MEMBERS,ARCHIVE,fixture,SNAP
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='controls_c3_',dir=W));bin=T/'bin';bin.mkdir();(bin/'python3').symlink_to(sys.executable)
def exe(name,body):
 p=bin/name;p.write_text('#!/bin/bash\n'+body+'\n');p.chmod(0o700)
exe('squeue','printf "%s" "$QUEUE"')
exe('sacct','if [[ " $* " == *" -j 171377 "* ]]; then printf "%s" "$DONOR"; else printf "%s" "$HISTORY"; fi')
archive=T/'p.tar';archive.write_bytes(ARCHIVE)
def setup(label):
 root=T/label;root.mkdir(mode=0o700);b=root/'i_7f1589c1';k=root/'x_7f1589c1';b.mkdir(mode=0o700);k.mkdir(mode=0o700);(k/'o').mkdir()
 for name in MEMBERS:
  p=b/name;p.parent.mkdir(parents=True,exist_ok=True);os.link(fixture()/name,p)
 os.link(archive,b/'p.tar');(k/'SHA256SUMS.txt').write_text('fixture\n')
 return root,b,k
base=dict(os.environ,PATH=str(bin)+':/usr/bin:/bin',USER='fixture',QUEUE='',DONOR='171377|a15_cot_ap673bc60f|COMPLETED|0:0\n',HISTORY='172180|a15_cot_ap05b8ac69|FAILED|1:0\n')
# Execute actual Python history guard, including the rejected no-ID attempt.
for label,history,allow in [('failed','172180|a15_cot_ap05b8ac69|FAILED|1:0',True),('wrong_state','172180|a15_cot_ap05b8ac69|COMPLETED|0:0',False),('unknown','172181|a15_cot_ap05b8ac69|FAILED|1:0',False),('missing','',False),('duplicate','172180|a15_cot_ap05b8ac69|FAILED|1:0\n'*2,False)]:
 root=T/('history_'+label);root.mkdir();b=root/'i_7f1589c1.f172180';b.mkdir();(b/'job.id').write_text('172180')
 for n in ('sbatch.out.a1_bootstrap','submission.started.a1_bootstrap','a.json.a1_bootstrap'):(b/n).write_text('')
 s=(W/'proof_history.py').read_text().replace('/project/community/jjyeung/okh7',str(root))
 r=subprocess.run([sys.executable,'-B','-c',s],env=dict(base,HISTORY=history),capture_output=True,text=True)
 assert (r.returncode==0)==allow,(label,r.stderr)
 print('PASS history',label)
# Exercise no-replace fallback with real directory renames and EINVAL injection.
s=(W/'m1.sh').read_text().split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0];s=s[:s.index("if __name__")];ns={};exec(compile(s,'m1','exec'),ns)
old=Path('fixture_c2')
oldarchive=T/'old.tar';oldarchive.write_bytes(Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_6a5c7d00/out/p_6a5c7d00.tar').read_bytes())
for label in ('valid','fallback','collision','queued_id','completed'):
 root=T/('move_'+label);root.mkdir(mode=0o700);b=root/'i_7f1589c1';k=root/'x_7f1589c1';b.mkdir(mode=0o700);k.mkdir(mode=0o700);(k/'o').mkdir()
 for name in ('sums.txt',):os.link(old/name,b/name)
 for line in (old/'sums.txt').read_text().splitlines():
  _,name=line.split('  ',1);p=b/name;p.parent.mkdir(parents=True,exist_ok=True);os.link(old/name,p)
 os.link(oldarchive,b/'p.tar')
 (b/'p0.lock').touch();(b/'job.id').write_text('172180')
 for tag in ('e0','d0'):(b/tag).mkdir();(b/tag/'rc').write_text('0')
 (k/'o/172180.proof.json').write_text(json.dumps(dict(job='172180',status='FAIL',config_identity=PINS['identity'])))
 (k/'sess.json').write_text('OLD PRIVATE CAPABILITIES')
 ns.update(O=root,B=b,K=k)
 def query(argv):
  if argv[0]=='squeue':return '172180|other|general|RUNNING' if label=='queued_id' else ''
  return '172180|a15_cot_ap05b8ac69|'+('COMPLETED' if label=='completed' else 'FAILED')+'|2026-11-18T08:31:00'
 ns['query']=query
 if label=='collision':k.with_name(k.name+'.f172180').mkdir()
 class Rename:
  def __call__(self,*args):ns['ctypes'].set_errno(errno.EINVAL);return -1
 class Lib:renameat2=Rename()
 before=(b.stat().st_ino,k.stat().st_ino)
 try:
  with patch.object(ns['ctypes'],'CDLL',return_value=Lib()) if label=='fallback' else __import__('contextlib').nullcontext():ns['main']({})
 except SystemExit:assert label not in ('valid','fallback')
 else:
  assert label in ('valid','fallback')
  assert not b.exists() and not k.exists()
  assert (b.with_name(b.name+'.f172180').stat().st_ino,k.with_name(k.name+'.f172180').stat().st_ino)==before
  assert (k.with_name(k.name+'.f172180')/'sess.json').read_text()=='OLD PRIVATE CAPABILITIES'
 print('PASS move',label)
# Actual canary wrapper, stub only scheduler and sealed submission invocation.
exe('bash', '''[[ "$1" == s.sh ]] || exit 9
[[ "$ADMISSION_JOB" == 172180 && "$ADMISSION_KIT" == "$EXPECTED_OLD" ]] || exit 8
printf '{"canary":true,"proof_job":"%s","admission_job":"172180","submission":"GATE_ACCEPTED"}' "$PROOF_JOB" > "$MARKER"
printf 'Submitted batch job 173000\\n' ''')
for label in ('held','running','wrong_partition','extra_history','bad_old','donor_running','wrong_sha','rehearsal_queued'):
 root,b,k=setup('canary_'+label);job='172900';(b/'job.id').write_text(job);(b/'sbatch.out').write_text(job+';cluster');(b/'submission.started').touch()
 donor=root/'r/673bc60f';donor.mkdir(parents=True);(donor/'A.json').write_text('{"verified":true,"step":200}')
 queue=f'{job}|a15_cot_ap05b8ac69|general|'+('RUNNING' if label=='running' else 'PENDING')+'|JobHeldUser\n'
 if label=='wrong_partition':queue=queue.replace('general','bootstrap')
 if label=='rehearsal_queued':queue+='172901|a15_cot_ap05b8ac6a|general|PENDING|Resources\n'
 history=base['HISTORY']
 if label=='extra_history':history+='171335|a15_cot_ap05b8ac69|FAILED|1:0\n'
 if label=='bad_old':history=history.replace('FAILED','COMPLETED')
 env=dict(base,QUEUE=queue,HISTORY=history,MARKER=str(k/'o'/f'{job}.canary.json'),EXPECTED_OLD=str(root/'x_7f1589c1.f172180'))
 if label=='donor_running':env['DONOR']=env['DONOR'].replace('COMPLETED','RUNNING')
 script=root/'submit.sh';script.write_text((W/'go_submit_canary_08f3a7b2.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
 authority='0'*64 if label=='wrong_sha' else '31f5e70ca014a370913115e124290805744e5947790e8d2463e5b0225130aa89'
 r=subprocess.run(['/bin/bash',str(script),job,authority],env=env,capture_output=True,text=True)
 assert (r.returncode==0)==(label in ('held','running')),(label,r.stdout,r.stderr)
 if not r.returncode:assert json.loads((b/'go.json').read_text())['canary'] is True and (b/'training.job.id').read_text().strip()=='173000'
 print('PASS canary',label)
# Match the exact packet rehearsal command, including the node-local root.
argv=next(line for line in (W/'rh1.sh').read_text().splitlines() if line.startswith('sbatch ')).split(' > ',1)[0]
expected=next(line for line in (SNAP/'CONT4.md').read_text().splitlines() if line.startswith('sbatch '))
assert argv==expected
for label,status,rc,okay in [('ok','REHEARSAL_OK',0,True),('fail','REHEARSAL_FAIL',1,False),('fake_pass','PASS',0,False),('running','REHEARSAL_RUNNING',None,False)]:
 root,b,k=setup('receipt_'+label);(b/'rehearsal.job.id').write_text('172999');(k/'o/172999.rehearsal.json').write_text(json.dumps(dict(job='172999',status=status,rc=rc,rehearsal=True,admission_executed=False)))
 p=root/'rhf.sh';p.write_text((W/'rhf.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
 r=subprocess.run(['/bin/bash',str(p)],env=base,capture_output=True,text=True);assert (r.returncode==0)==okay,(label,r.stderr)
 print('PASS rehearsal receipt',label)
print('PASS exact CONT4 rehearsal argv; all controls used local fixtures')
