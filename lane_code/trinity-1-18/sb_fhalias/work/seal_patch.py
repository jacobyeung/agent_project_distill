"""Hash both copies and the read-only source, then emit the minimal patch."""
from pathlib import Path
import difflib,hashlib,json
W=Path(__file__).resolve().parents[1];S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
b=inventory(W/'work/tree_before');a=inventory(W/'work/tree_after');s=inventory(S)
assert s==b,'Read-only source and before copy differ'
assert b.keys()==a.keys()
changed=[n for n in b if b[n]!=a[n]]
assert changed==['student_pilot/job_env.py','student_pilot/r2_intake.py','student_pilot/r2_materialize.py'],changed
patch=''.join(''.join(difflib.unified_diff((W/'work/tree_before'/n).read_text().splitlines(True),(W/'work/tree_after'/n).read_text().splitlines(True),fromfile='tree_before/'+n,tofile='tree_after/'+n)) for n in changed)
(W/'out/ALIAS.patch').write_text(patch)
for name,files in [('before',b),('after',a)]:
 (W/'out'/('TREE_'+name.upper()+'.sha256')).write_text(''.join(h+'  '+n+'\n' for n,h in files.items()))
inputs={str(S/n):h for n,h in s.items()}
inputs[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
for n in ('out/TREE_BEFORE.sha256','out/TREE_AFTER.sha256','out/ALIAS.patch'):
 inputs[str(W/n)]=sha(W/n)
(W/'out/CHANGED_FILES.json').write_text(json.dumps(dict(input_sha256=inputs,source_matches_before=True,file_count=len(b),changed=[dict(path=n,before=b[n],after=a[n]) for n in changed],requires_new_tree_seal=True),indent=2)+'\n')
print(json.dumps(dict(files=len(b),changed=changed),indent=2))
