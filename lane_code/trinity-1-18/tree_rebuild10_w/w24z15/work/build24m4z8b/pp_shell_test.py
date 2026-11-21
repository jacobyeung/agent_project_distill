import os,json,subprocess,sys
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b';F=D/'pp_shell';F.mkdir();X=F/'x';X.mkdir();N=F/'tmp';N.mkdir()
# Only the expensive helper is replaced; the delivered shell executes unchanged
# apart from relocating its fixed shared root into this private fixture.
(X/'j7.py').write_text('import sys,json,shutil\nif sys.argv[1]=="b":print(shutil.which("bwrap"));sys.exit(0)\nfrom pathlib import Path\np=Path(sys.argv[3]);p.mkdir(parents=True,exist_ok=True);(p/"p0.json").write_text(json.dumps(dict(mode="q",completed=False,fixture=True)))\nsys.exit(1)\n')
s=(L/'out/pp/pp.sh').read_text().replace('/project/community/jjyeung/okh7/x_22c714e1',str(X))
p=F/'pp.sh';p.write_text(s)
r=subprocess.run(['bash',str(p)],env={**os.environ,'SLURM_JOB_ID':'123','SLURM_TMPDIR':str(N),'J7_NICE':'1'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(D/'PP_SHELL.log').write_text(r.stdout)
assert r.returncode==1,r.stdout
v=json.loads((X/'o/123/p0.json').read_bytes());assert v['mode']=='q' and v['completed'] is False
assert (N/'p_22c714e1_123/p0.log').exists()
(D/'PP_SHELL.json').write_text(json.dumps(dict(status='OK',returncode=1,published_failure=True,shared_bytes=(X/'o/123/p0.json').stat().st_size,scope='Actual delivered shell with only X relocated and the planner helper replaced by an explicit failure fixture.'))+'\n')
print('CPU shell publishes its helper outcome and preserves failure exit')
