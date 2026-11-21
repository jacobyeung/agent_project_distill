from pathlib import Path
import os,sys,subprocess,json
J=Path.cwd();D=J/'work/build24m4z12';R=D/'wrapper_exception';R.mkdir();K=R/'k';N=R/'n';X=R/'x';N.mkdir();X.mkdir();(K/'b').mkdir(parents=True)
(K/'b/z.py').write_text("def load(p):return {}\ndef screen(*a):raise ValueError('transport https://local.invalid/private-capability')\n")
for n in ('j2.log','j2.err'):(N/n).write_text('q\n')
rows=[]
for version,path in [('before',J/'inputs/jn2.sh'),('after',J/'out/jn3.sh')]:
 s=path.read_text().split("<<'PYJ2'\n",1)[1].split('\nPYJ2',1)[0]
 # Old helper exits its loop after the first publication using a nonexistent parent.
 p=R/(version+'.py');p.write_text(s)
 args=[sys.executable,'-I','-s','-B',str(p),str(K),str(N),str(X),'41','99999999','.01']
 if version=='after':args.append('once')
 r=subprocess.run(args,capture_output=True,text=True)
 # Preserve classified output only: the injected exception contains a fake capability.
 (R/(version+'.log')).write_text('returncode='+str(r.returncode)+'\n'+('ValueError\n' if 'ValueError' in r.stderr else ''))
 rows.append(dict(version=version,returncode=r.returncode))
assert rows[0]['returncode']!=0 and rows[1]['returncode']==0
log=(N/'j2.retry.log').read_text();assert 'ValueError' in log and 'https://' not in log and 'private-capability' not in log
(R/'RESULT.json').write_text(json.dumps(dict(status='PASS',cases=rows,exception_logged=True,URL_masked=True),indent=2)+'\n');print('Wrapper Exception handling and masking PASS')
