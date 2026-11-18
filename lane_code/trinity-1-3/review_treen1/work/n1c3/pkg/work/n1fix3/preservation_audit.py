from pathlib import Path
import ast,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';T=L/'work/tree_r1';O=B/'proofs/audit'
O.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
old=inventory(B/'original');now=inventory(T)
changed=[n for n in sorted(set(old)|set(now)) if old.get(n)!=now.get(n)]
(B/'DIFF_VS_N1FIX2.json').write_text(json.dumps(dict(old_seal=digest(old),current_seal=digest(now),
    changed_files=[dict(file=n,before=old.get(n),after=now.get(n)) for n in changed]),indent=2))
assert digest(old)=='f1ec0cd9fdb9c791e7a78246b50c0b501f3d8edbdbad3dfcd2d6c6e6db3ea35e'
prior=json.loads((B/'inherited/proofs/audit/INFERENCE_COMPONENTS.json').read_text())
(O/'INFERENCE_COMPONENTS.json').write_text(json.dumps(prior))
records=[]
for row in prior['known_outside_forward']:
    name=row['file'];assert now[name]==old[name],name
    records.append(dict(file=name,component=row['component'],line=row['line'],sha256=now[name],unchanged=True))
(O/'INFERENCE_UNCHANGED.json').write_text(json.dumps(records,indent=2))
cfg=json.loads((B/'inputs/config.json').read_text())
source=Path(cfg['r2_scene_exclusion_list']['path']) if 'r2_scene_exclusion_list' in cfg else B/'inputs/02315a74ed90.json'
raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'
f6=json.loads((B/'proofs/review_inputs/F6.json').read_text())
(O/'F6_PRESERVATION.json').write_text(json.dumps(dict(list_source=str(source.relative_to(L)),
    sha256=hashlib.sha256(raw).hexdigest(),reviewed_keys=f6['kit_list_keys'],
    inherited_admitted=f6['vqa_with_list']['admitted'],inherited_source='work/n1fix3/proofs/review_inputs/F6.json',
    current_full_census=False,gate_source_unchanged=now['student_pilot/scene_division_gate.py']==old['student_pilot/scene_division_gate.py']),indent=2))
def without_paths(v):
    if isinstance(v,dict):return {k:without_paths(x) for k,x in v.items() if k!='path'}
    if isinstance(v,list):return [without_paths(x) for x in v]
    return v
before=json.loads((L/'work/n1fix2/inputs/mix.json').read_text());after=json.loads((B/'inputs/mix.json').read_text())
assert without_paths(before)==without_paths(after)
(O/'MIX_PRESERVATION.json').write_text(json.dumps(dict(unchanged_except_local_pin_paths=True,
    before='work/n1fix2/inputs/mix.json',after='work/n1fix3/inputs/mix.json'),indent=2))
base=L/'work/base/tree_b01ce449'
records=[]
for file,functions in [('student_pilot/carrier_c1.py',('parameter_groups','load_depth_stage1')),
                       ('student_pilot/carrier_c1_run.py',('init_from_artifact','export','identity','checkpoint'))]:
    p=base/file;parsed=ast.parse(p.read_text())
    for n in parsed.body:
        if isinstance(n,ast.FunctionDef) and n.name in functions:
            records.append(dict(function=n.name,file=str(p.relative_to(L)),line=n.lineno,end_line=n.end_lineno,
                file_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'OPTIMIZER_INPUTS.json').write_text(json.dumps(dict(native_functions=records,
    comparison='Native parameter_groups, live named_parameters and named_modules determine names, tensor counts, scalar counts, initial rates, decay and frozen modules. Initialization parity is checked before the live topology is reused for both configurations. Native initialization differences are independently measured in the CPU producer proof.',
    proof='work/n1fix3/proofs/targeted/n1fix/native_group_tables/TABLES.json'),indent=2))
print(json.dumps(dict(changed_files=changed,base_runner_equivalent=
    (L/'work/build9fix/test_runner.py').read_text().replace('work/build9fix','work/n1fix3')==(B/'test_runner.py').read_text())))
