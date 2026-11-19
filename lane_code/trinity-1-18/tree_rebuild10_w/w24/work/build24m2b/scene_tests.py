import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import subprocess,os,copy,importlib.util
from unittest.mock import patch
F=D/'scene_tests';F.mkdir();root=F/'p';root.mkdir();(root/'s').symlink_to(T,target_is_directory=True);scratch=root/'i';scratch.mkdir()
sys.path[:0]=[str(kit('q')/'b'),str(L/'work/build21')]
import sc
from student_pilot.r1_persisted import scope
from student_pilot.r2_scene_bindings import verify
cfg=J.load(L/'work/build24/proofs/capacity/400/request_config.json')
paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m1/UPLOADS_q.json')['files'] if x['opaque_name'].startswith('u/')}
paths.update(cfg['r1_training']['persisted_files'])
# Native fixture uses synthetic rows and a CPU frame-host boundary. No producer,
# selection rule, receipt writer or verification function is substituted.
wrapper=F/'host.py';wrapper.write_text('''from pathlib import Path
import sys,runpy
L=Path('''+repr(str(L))+''')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1')]
import native24,os
u=os.uname();os.uname=lambda:os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
''')
real_run=subprocess.run
calls=[]
def run(args,**kwargs):
 args=list(args);i=args.index(sys.executable);args[i+3:i+3]=[str(wrapper)]
 calls.append(args)
 return real_run(args,**kwargs)
cfg['r2_scene_rebuild']=None;cfg['scene_coverage']=None
with scope(paths):
 try:verify(cfg)
 except ValueError as e:before=str(e)
 else:raise AssertionError('missing scene evidence accepted')
with patch.object(sc.subprocess,'run',run):physical=sc.bind(cfg,paths,scratch,root/'q',kit('q'))
assert not (root/'q').exists()
newpaths={J.sha(p):str(p) for p in physical.rglob('*') if p.is_file()}
with scope(paths),scope(newpaths):verify(cfg)
# Replay exactly native24's rebuild(spec,cfg,output) call in the same logical
# output namespace; its bytes must equal the wrapper-produced receipt files.
direct=F/'native';direct.mkdir()
control=J.load(scratch/'sc.json');J.write(F/'native.json',control)
cmd=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(direct),str(root/'q'),sys.executable,'-B','-s',str(wrapper),str(kit('q')/'b/sc.py'),str(F/'native.json'),str(T)]
real_run(cmd,check=True)
a={str(p.relative_to(physical)):J.sha(p) for p in physical.rglob('*') if p.is_file()};b={str(p.relative_to(direct/'sc')):J.sha(p) for p in (direct/'sc').rglob('*') if p.is_file()};assert a==b
J.write(D/'SCENE_TESTS.json',dict(status='PASS',before=before,verify_after=True,fresh_native_root=True,native_receipt_bytes_identical=True,files=len(a),receipt_sha256=a['2.json'],scope='Retained native24 synthetic populations, native rebuild and verify; only fixture host identity is supplied.'))
print('scene native byte equality, verify before/after, fresh root PASS')
