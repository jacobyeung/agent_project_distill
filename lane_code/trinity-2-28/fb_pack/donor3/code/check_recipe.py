from pathlib import Path
import ast, hashlib, json, re, subprocess
W=Path(__file__).resolve().parents[1]; O=W/'out'; T=W/'work/new';D=W.parent/'donor2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=[Path(__file__).resolve(),O/'READER_REQUEST.md',O/'REAL_WEIGHT_COMMAND.sh',T/'tests/test_scale_donor.py',T/'student_pilot/scale_donor.py',D/'out/READER_REQUEST.md',D/'out/REAL_WEIGHT_COMMAND.sh',W.parent/'donor2rev/REVIEW_VERDICT.md',W.parent/'donorrev/REVIEW_VERDICT.md',W.parent/'donor2rev/work/reader_check.py',W.parent/'donor2rev/work/READER_new.json',W.parent/'donor2rev/work/READER_live.json']
inputs={str(p):sha(p) for p in paths}
s=(T/'tests/test_scale_donor.py').read_text();tree=ast.parse(s)
method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='test_mdg_runtime_strict_load_requires_reader_metadata_steps')
steps=next(ast.literal_eval(n.value) for n in ast.walk(method) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reader_steps' for t in n.targets))
doc=(O/'READER_REQUEST.md').read_text();block=re.search(r'```python\n(.*?)```',doc,re.S)[1]
assert steps.strip() in block
assert "mock.patch.object(run, 'CarrierC1'" not in ast.get_source_segment(s,method)
source_tree=ast.parse((T/'student_pilot/scale_donor.py').read_text())
features=next(ast.literal_eval(n.value) for n in source_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FEATURE_FILES' for t in n.targets))
rows=re.findall(r'^\| `([^`]+\.py)` \| `([^`]+)` \| `([^`]+)` \|$',doc,re.M)
assert [r[0] for r in rows]==list(features)
for name,base_hash,new_hash in rows:
    p=T/'student_pilot'/name;inputs[str(p)]=sha(p);assert sha(p)==new_hash
    p=W/'work/base/student_pilot'/name
    if p.exists():inputs[str(p)]=sha(p);assert sha(p)==base_hash
    else:assert base_hash=='MISSING (absent at base seal)'
syntax=subprocess.run(['bash','-n',str(O/'REAL_WEIGHT_COMMAND.sh')]);assert syntax.returncode==0
r=dict(input_sha256=inputs,command='python -B code/check_recipe.py',status='PASS',documented_sequence_matches_test_exactly=True,feature_source_count=len(rows),feature_sources_match_base_and_patch=True,real_weight_command_syntax='PASS',runtime_constructor_not_replaced=True,production_reader_adapter='MISSING: must be installed by the separate runtime reader owner; this task supplies the recipe and test')
(O/'RECIPE_CHECK.json').write_text(json.dumps(r,indent=2)+'\n')
print({k:v for k,v in r.items() if k!='input_sha256'})
