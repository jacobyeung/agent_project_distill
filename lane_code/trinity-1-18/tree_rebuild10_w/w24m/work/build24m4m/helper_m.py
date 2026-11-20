from common import *
import difflib,ast,re,shutil
p=L/'out/rcj/x.py';old=p.read_text()
review=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/rcjk2')
for name in ('x.py','x.diff'):shutil.copyfile(review/name,D/('reviewed_'+name))
s=(review/'x.py').read_text()
host=s[s.index('def host_root():'):s.index('def launch(')]
assert 'def host_root' not in old
new=old.replace('def launch(',host+'def launch(',1)
start=s.index("    mode = z.load(root/'mode.json')",s.index('def launch('))
end=s.index("    cmd += ['--bind', str(root), str(root)]",start)
begin=new.index("    cmd = [str(binary), '--ro-bind', '/', '/'",new.index('def launch('))
finish=new.index("    cmd += ['--bind', str(root), str(root)]",begin)
new=new[:begin]+s[start:end]+new[finish:]
# This sandbox is invoked only by mode-r publication.
needle="    cmd = [str(binary), '--ro-bind', '/', '/', '--dev-bind', '/dev', '/dev', '--proc', '/proc',"
assert new.count(needle)==1
new=new.replace(needle,"    cmd = [str(binary), *host_root(), '--dev-bind', '/dev', '/dev', '--proc', '/proc',")
def funcs(raw):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(raw).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
a,b=funcs(old),funcs(new)
assert {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}=={'host_root','launch','rdiff'}
assert b['host_root']==funcs(s)['host_root']
replace(p,new)
(D/'RCJ_DIFF.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='24m4l/x.py',tofile='24m4m/x.py')))
J.write(D/'HELPER_CHANGE.json',dict(before=J.load(D/'BASE_RCJ.json')['x.py'],after=J.sha(p),reviewed_sha256=J.sha(review/'x.py'),reviewed_diff_sha256=J.sha(review/'x.diff'),changed_functions=['host_root','launch','rdiff'],processor_children='pc.py delegates to rb.command, which already constructs an empty root; unchanged.'))
print('Helper changed only host_root, launch, rdiff; reviewed helper',J.sha(review/'x.py'))
