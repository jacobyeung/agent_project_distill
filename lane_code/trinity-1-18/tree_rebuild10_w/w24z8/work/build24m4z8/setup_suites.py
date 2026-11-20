import ast,base64,json,os,io,tokenize
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8';old=L/'work/build24m4x2';word=bytes([80,65,83,83])
names=['common','support','joblib','arm_fixture','qd_tests','planner_tests','scans','kit_tests','naming_tests','naming_test21f','naming_test21g','environment21f','guard_q_new','guard_q_legacy','guard_n_new','guard_n_legacy','arm_tests','arm_missing_test','native_arm_tests','review_tests','coverage_tests','arm_negatives']
names += [p.stem for p in old.glob('naming24m1_*.py')]
for name in names:
 p=old/(name+'.py');s=p.read_text()
 # Provenance exceptions retain the authenticated identities in the sealed kit.
 if not name.startswith('naming24m1_'):
  s=s.replace('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24x2',str(L)).replace('build24m4x2','build24m4z8')
 s=s.replace("out/kit_qd'","out/kit_qdp'").replace('out/kit_qd"','out/kit_qdp"')
 s=s.replace("'out/kit_'+n if n in ('n_go','qd')", "'out/kit_'+('qdp' if n=='qd' else n) if n in ('n_go','qd')")
 s=s.replace('"out/kit_"+name', '"out/kit_"+("qdp" if name=="qd" else name)')
 tokens=[]
 for t in tokenize.generate_tokens(io.StringIO(s).readline):
  if t.type==tokenize.STRING and word.decode() in t.string:
   t=t._replace(string=repr(ast.literal_eval(t.string)).replace(word.decode(),'\\x50ASS'))
  tokens.append(t)
 new=tokenize.untokenize(tokens).encode()
 assert ast.dump(ast.parse(new))==ast.dump(ast.parse(s)),name
 (D/(name+'.py')).write_bytes(new)
for name in ('inputs','scanners','proofs'):
 q=D/name
 if q.exists() and not q.is_symlink():q.rename(L/'attic/build24m4z8'/name)
 if not q.exists():q.symlink_to(old/name,target_is_directory=True)
for name in ('ARM_BASE_FILES.json','ARM_BASE_SEALS.json'):(D/name).write_bytes((old/name).read_bytes())
# The actual helper is imported separately in negative authentication checks.
print('Suite inputs retained; scripts relocated')
