from common import *
# Complete the byte-equality replay after the successful native wrapper run.
s=(D/'scene_tests.py').read_text()
start=s.index("cmd=['/usr/bin/bwrap'")
tail=s[start:]
tail=tail.replace("real_run(cmd,check=True)","(root/'q').mkdir()\nsubprocess.run(cmd,check=True)")
prefix="""from common import *
import subprocess
F=D/'scene_tests';root=F/'p';physical=root/'i/sc/sc';direct=F/'native';wrapper=F/'host.py'
from student_pilot.r1_persisted import scope
from student_pilot.r2_scene_bindings import verify
control=J.load(F/'native.json');cfg=control['config']
cfg.update(r2_scene_rebuild=dict(path=str(root/'q/sc/2.json'),sha256=J.sha(physical/'2.json')),scene_coverage=J.load(physical/'2.json')['scene_coverage'])
with scope(control['paths']),scope({J.sha(p):str(p) for p in physical.rglob('*') if p.is_file()}):verify(cfg)
before='Missing scene evidence refuses in native verify'
"""
(D/'scene_continue.py').write_text(prefix+tail)
# Resume the hidden-path fixture without recreating its retained immutable inputs.
s=(D/'hidden.py').read_text()
start=s.index("resolved=J.load(base/'resolved.json')")
s=s[:start].replace("F.mkdir()","F.mkdir(exist_ok=True)").replace("shutil.copytree(base/folder,F/folder,copy_function=os.link)","assert (F/folder).is_dir()")+s[start:]
s=s.replace("resolved=J.load(base/'resolved.json')","import lzma\nresolved=json.loads(lzma.decompress((L/'attic/build24m2d/retained_xz/work/build24m2d/hidden/resolved.json.xz').read_bytes()))")
(D/'hidden_resume.py').write_text(s)
