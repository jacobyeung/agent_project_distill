import sys,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
H=L/'work/build24m4h'
names=('support','environment21f','scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','review_tests','coverage_tests','arm_missing_test','arm_negatives','native_arm_tests','kit')
def rewrite(s):
 s=s.replace(str(W/'w24h'),str(L)).replace('work/build24m4h','work/build24m4i')
 s=re.sub(r'^sys.path\[:0\]=.*$', "sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24i/work/tree_r1']",s,flags=re.M)
 return 'from pathlib import Path\n'+s
frozen={str(W/'w24/attic/build24d/work/build24/joblib.py'):'old24c.py',str(W/'w24/work/build22/joblib.py'):'old23.py',str(W/'w24/attic/build24/joblib23.py'):'old24.py',str(W/'w24/attic/build21f/naming21.py'):'old_naming21.py'}
for src,dst in frozen.items():(D/dst).write_bytes(Path(src).read_bytes())
for name in names:
 s=rewrite((H/(name+'.py')).read_text())
 for src,dst in frozen.items():s=s.replace(src,str(D/dst))
 if name=='kit_tests':
  s=s.replace('   with scope(paths):', "   paths.update({p.name:str(p) for p in (L/'work/build24m4i/inputs').iterdir()})\n   with scope(paths):")
 (D/(name+'.py')).write_text(s)
for n in NAMES:
 s=(H/('naming24m1_'+n+'.py')).read_text()
 for a,b in J.load(D/'CONFIG_DELTA.json')['hash_replacements'].items():s=s.replace(a,b)
 (D/('naming24m1_'+n+'.py')).write_text(s)
 for p in (H/'scanners'/n).iterdir():
  if p.is_file():
   dest=D/'scanners'/n/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
for name in ('guard_q','guard_n'):(D/name).mkdir()
(D/'joblib.py').write_bytes((kit('n')/'b/z.py').read_bytes())
for name in ('resolver21e','naming_test21f','naming_test21g','naming_test21d'):
 s=rewrite((W/'w24/work/build21'/(name+'.py')).read_text())
 if name=='naming_test21f':
  s=s.replace('import naming21 as N','import naming24m1_n as N')
  s=s.replace("L/'attic/build21f/naming21.py'",'Path('+repr(str(D/'old_naming21.py'))+')')
  s=s.replace('wh=json.loads',"B=Path(__file__).resolve().parent;K=L/'work/build24/kits/q'\nwh=json.loads")
 if name=='naming_test21g':s=s.replace('import naming21 as N','import naming24m1_n as N')
 (D/(name+'.py')).write_text(s)
s=rewrite((W/'w24/out/fill_m600.py').read_text()).replace('L=Path(__file__).resolve().parents[1]','L=Path(__file__).resolve().parents[2]')
(D/'fill_m600.py').write_text(s)
p=L/'out/arm_routing.py';replace(p,p.read_text().replace('work/build24m4d','work/build24m4i'))
(D/'bootstrap.py').write_text('''import sys,runpy
from pathlib import Path
L=Path(__file__).resolve().parents[2];W=L.parent
script=Path(sys.argv[1]).resolve()
def check(event,args):
 if event=="exec":
  name=args[0].co_filename
  if name.startswith(str(W)+"/") and not name.startswith(str(L)+"/"):
   raise RuntimeError("SUPERSEDED_WORKSPACE_CODE_BLOCKED:"+name)
sys.addaudithook(check)
sys.path.insert(0,str(script.parent));sys.argv=sys.argv[1:]
runpy.run_path(str(script),run_name="__main__")
''')
s=(H/'run_suites.py').read_text().replace('work/build24m4h','work/build24m4i').replace("'arm_negatives'):","'arm_negatives','native_arm_tests'):")
(D/'run_suites.py').write_text(s)
print('SETUP',len(names),'suites and local dependency copies; host read-only, external code execution blocked')
