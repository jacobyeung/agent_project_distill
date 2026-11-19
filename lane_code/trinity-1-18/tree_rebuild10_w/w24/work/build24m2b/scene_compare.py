from common import *
import subprocess
F=D/'scene_tests';root=F/'p';scratch=root/'i';physical=scratch/'sc/sc';wrapper=F/'host.py';real_run=subprocess.run
before='missing scene pin refused';(root/'q').mkdir()
direct=F/'native';direct.mkdir(exist_ok=True)
control=J.load(scratch/'sc.json');J.write(F/'native.json',control)
cmd=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(direct),str(root/'q'),sys.executable,'-B','-s',str(wrapper),str(D/'scene_tests/direct.py'),str(F/'native.json'),str(T)]
real_run(cmd,check=True)
a={str(p.relative_to(physical)):J.sha(p) for p in physical.rglob('*') if p.is_file()};b={str(p.relative_to(direct/'sc')):J.sha(p) for p in (direct/'sc').rglob('*') if p.is_file()};assert a==b
J.write(D/'SCENE_TESTS.json',dict(status='PASS',before=before,verify_after=True,fresh_native_root=True,native_receipt_bytes_identical=True,files=len(a),receipt_sha256=a['2.json'],scope='Retained native24 synthetic populations, native rebuild and verify; only fixture host identity is supplied.'))
print('scene native byte equality, verify before/after, fresh root PASS')
