import importlib.util,json,sys,subprocess
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parents[1];D=H.parent/'d0';sys.path.insert(0,str(H/'build/fx/b'))
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module(D/'kitfull/b/i.py','old_i');new=module(H/'build/fx/b/i.py','new_i')
with patch.object(old,'descendants',return_value=[123]),patch.object(Path,'read_bytes',side_effect=PermissionError('denied')):
 try:old.relay(456)
 except PermissionError:pass
 else:raise AssertionError('expected original PermissionError')
with patch.object(new,'descendants',return_value=[123]),patch.object(Path,'read_bytes',side_effect=PermissionError('denied')):new.relay(456)
# Run the exact shipped on_stop function against a local launch record.
b=H/'evidence/stop_bridge';(b/'k').mkdir(parents=True,exist_ok=False);(b/'o').mkdir();r=b/'run';r.mkdir()
(b/'k/launch.json').write_text(json.dumps(dict(run_directory=str(r))))
s=(H/'build/fx/b/r.sh').read_text();fn=s[s.index('on_stop() {'):s.index('trap on_stop USR1')]
sh=f'HX={b}; child=""; admission_child=""; X=""; stop_file="$HX/o/test.stop"\n'+fn+'\non_stop\n'
(b/'on_stop.sh').write_text(sh);subprocess.run(['/bin/bash',str(b/'on_stop.sh')],check=True)
assert (r/'stop.local.request').read_text()=='USR1\n'
# The same inode is visible at a different name inside a real user namespace.
alias=b/'alias';alias.mkdir()
res=subprocess.run(['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(r),str(alias),'--unshare-user','--uid',str(__import__('os').getuid()),'--gid',str(__import__('os').getgid()),'/bin/cat',str(alias/'stop.local.request')],check=True,capture_output=True,text=True)
assert res.stdout=='USR1\n'
(b/'result.json').write_text(json.dumps(dict(original_permission_error_reproduced=True,patched_relay_survives=True,exact_r_sh_marker=True,bwrap_user_namespace_sees_marker=True,distributed_signal_proof=False),indent=2)+'\n')
print('stop bridge checks passed')
