from common import *
import subprocess
F=D/'scene_tests';root=F/'p';physical=root/'i/sc/sc';direct=F/'native';wrapper=F/'host.py'
from student_pilot.r1_persisted import scope
from student_pilot.r2_scene_bindings import verify
control=J.load(F/'native.json');cfg=control['config']
cfg.update(r2_scene_rebuild=dict(path=str(root/'q/sc/2.json'),sha256=J.sha(physical/'2.json')),scene_coverage=J.load(physical/'2.json')['scene_coverage'])
with scope(control['paths']),scope({J.sha(p):str(p) for p in physical.rglob('*') if p.is_file()}):verify(cfg)
before='Missing scene evidence refuses in native verify'
cmd=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(direct),str(root/'q'),sys.executable,'-B','-s',str(wrapper),str(kit('q')/'b/sc.py'),str(F/'native.json'),str(T)]
(root/'q').mkdir()
subprocess.run(cmd,check=True)
a={str(p.relative_to(physical)):J.sha(p) for p in physical.rglob('*') if p.is_file()};b={str(p.relative_to(direct/'sc')):J.sha(p) for p in (direct/'sc').rglob('*') if p.is_file()};assert a==b
J.write(D/'SCENE_TESTS.json',dict(status='PASS',before=before,verify_after=True,fresh_native_root=True,native_receipt_bytes_identical=True,files=len(a),receipt_sha256=a['2.json'],scope='Retained native24 synthetic populations, native rebuild and verify; only fixture host identity is supplied.'))
print('scene native byte equality, verify before/after, fresh root PASS')
