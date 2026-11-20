import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
# Keep fixtures and their old logs intact; all new checks write to this build.
e=L/'work/build24m4e'
for name in ('support.py','environment21f.py','scans.py','kit_tests.py','naming_tests.py','guard_q_new.py','guard_n_new.py','guard_q_legacy.py','guard_n_legacy.py','resolver_tests.py','resolver600_tests.py','resolver23_tests.py',*[f'naming24m1_{n}.py' for n in NAMES]):
 s=(e/name).read_text()
 s=s.replace(str(W/'w24e/work/build24m4e'),str(D)).replace('work/build24m4e','work/build24m4h')
 s=s.replace(str(W/'w24e/work/tree_r1'),str(T))
 # Ensure the checked implementation is this kit, not a prior helper copy.
 if name=='kit_tests.py':s=s.replace("(Path('"+str(D)+"')/'joblib.py')","(Path('"+str(D)+"')/'joblib.py')")
 (D/name).write_text(s)
for n in NAMES:
 src=e/'scanners'/n
 for f in src.iterdir():
  if f.is_file():
   dest=D/'scanners'/n/f.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
for n in ('guard_q','guard_n'):(D/n).mkdir()
(D/'joblib.py').write_bytes((kit('n')/'b/z.py').read_bytes())
# Arming retains its production scanner, which reads current kit bytes.
for name in ('arm_tests.py','review_tests.py','coverage_tests.py','arm_missing_test.py'):
 s=(L/'work/build24m4f'/name).read_text().replace('work/build24m4f','work/build24m4h')
 s=s.replace("sys.executable,\"-s\",\"-B\"", "sys.executable,\"-I\",\"-s\",\"-B\"")
 (D/name).write_text(s)
# Both native constructors must disclose the unavailable exclusion input.
p=D/'offline.py';s=p.read_text();a=s.index('with scope(paths):\n pool=');b=s.index('assert len(policy)==14',a)
s=s[:a]+'''try:
 with scope(paths):pool=s1_pool.Pool(seed['manifest'],seed['room_sets'])
 constructor=dict(status='PASS')
except ValueError as error:
 constructor=dict(status='UNAVAILABLE',refusal=str(error))
 pool=s1_pool.Pool.__new__(s1_pool.Pool)
 pool.sources={v['name']:v for v in m['sets']};pool.room_sets=seed['room_sets']
policy={n:dict(status='DEFERRED' if pool.deferred(n) else 'ELIGIBLE',reason=pool.deferred(n)) for n in pool.sources}
rb.statuses(policy,s['sources'])
'''+s[b:]
s=s.replace("policy_statuses=policy,native_prepare", "policy_statuses=policy,native_constructor=constructor,native_prepare")
replace(p,s)
# Recompute seals only after every active file has its final bytes.
seals={n:reseal(kit(n)) for n in NAMES};J.write(D/'SEALS.json',seals);print(seals)
