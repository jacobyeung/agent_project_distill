from pathlib import Path
import hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';O=L/'work/merge11/proofs/n1/kit_scope';O.mkdir(exist_ok=True)
entry=L/'work/merge11/kits/r1/b/a.py';target=L/'work/tmp/outside_job_namespace'
assert not target.exists()
records=[]
for mode,error in [('p','E06'),('t','E03')]:
    result=subprocess.run([sys.executable,'-I','-s','-B',str(entry),mode,str(target)],
                          cwd=entry.parents[1],capture_output=True,text=True)
    if result.returncode<0:raise SystemExit('Kit process killed; stop without retry.')
    assert result.returncode and error in result.stderr and not target.exists(),result.stderr
    records.append(dict(mode=mode,expected=error,returncode=result.returncode,stderr=result.stderr,root_created=False))
(O/'RESULT.json').write_text(json.dumps(dict(entry_sha256=hashlib.sha256(entry.read_bytes()).hexdigest(),
    cases=records,scope='Actual staged entry refuses an external namespace before any filesystem creation; training remains unauthorized.'),indent=2)+'\n')
print(json.dumps(records))
