import json,subprocess,shutil,sys
from pathlib import Path
D=Path.cwd()/'work/build24m4z8b';F=D/'mount_probe';F.mkdir();a=F/'a';b=F/'b';a.mkdir();b.mkdir()
code='from pathlib import Path;import sys;p=Path(sys.argv[1]);(p/"p0").write_text("local")'
r=subprocess.run([shutil.which('bwrap'),'--bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(a),str(b),sys.executable,'-I','-s','-B','-c',code,str(b)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(D/'MOUNT_PROBE.log').write_text(r.stdout)
assert r.returncode==0,r.stdout
assert (a/'p0').read_text()=='local' and not (b/'p0').exists()
(D/'MOUNT_PROBE.json').write_text(json.dumps(dict(status='OK',real_bwrap=True,remote_path_writes_redirected=True,returncode=r.returncode))+'\n')
print('Publication mount redirects writes to local storage')
