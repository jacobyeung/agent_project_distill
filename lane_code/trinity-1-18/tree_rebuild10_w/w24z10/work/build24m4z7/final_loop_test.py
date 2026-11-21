from pathlib import Path
import os,sys,json,importlib.util,subprocess,unittest
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z7';path=D/'archive_tests_release.py'
text=path.read_text().split('class Archive',1)[0].replace('build24m4z7/archive_suite_release','build24m4z7/final_loop_release')
scope={'__file__':str(path)};exec(compile(text,str(path),'exec'),scope)
C=scope['C'];c=scope['fixture']('loop');K=scope['K'];R=scope['D']
os.environ.update(FAKE_SINK=str(R/'sink'),STRICT_FAIL='once',STRICT_SELECT='.part02-of-04')
import shutil,time
(c.kit/'b').mkdir(exist_ok=True)
for n in ('o.py','pc.py','z.py','wh.json'):shutil.copyfile(K/'b'/n,c.kit/'b'/n)
shutil.copyfile(K/'k/g.json',c.kit/'k/g.json')
c.deadline=time.time()+10;c.archive_due=time.time()+8;c.upload_until=c.archive_due
(c.root/'t.log').write_text('q 1\n')
subprocess.run([sys.executable,'-I','-s','-B',str(K/'b/o.py'),str(c.root),'0','0','--local'],env={**os.environ,'SLURM_JOB_ID':'41'},check=True)
calls=[];original=c.copy_exit
def copy():
 calls.append(len(calls))
 if len(calls)==1:raise OSError(28,'q')
 return original()
with patch.object(C,'Copier',return_value=c),patch.object(c,'copy_exit',side_effect=copy),patch.object(sys,'argv',['pc.py',str(c.kit),str(c.root),'41','--final']):C.main()
phases=[json.loads(s)['phase'] for s in (c.spool/'final_order.jsonl').read_text().splitlines()]
assert phases.count('stop')>=2 and all(phases[i-1]=='logs' for i,p in enumerate(phases) if p=='o')
assert len(calls)>=2 and (c.state/'gcs_o.done').is_file() and (c.state/'o_copy.done').is_file()
assert (c.target/'o/41/o.tar').read_bytes()==(c.root/'o/o.tar').read_bytes()
rows=[json.loads(s) for s in (R/'sink/events.jsonl').read_text().splitlines() if json.loads(s)['http']==200 and json.loads(s)['bytes']>0];assert len(rows)==len({r['name'] for r in rows})==4
result=dict(status='PASS',copy_attempts=len(calls),passes=phases.count('stop'),phases=phases,GCS_parts=4,duplicate_objects=0,X_archive_exact=True,final_loop_actual=True)
(D/'FINAL_LOOP.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
