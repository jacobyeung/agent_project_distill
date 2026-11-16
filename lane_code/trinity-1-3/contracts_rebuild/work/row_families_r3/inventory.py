"""Bounded source inventory; no imports, external roots or model assets."""
import ast,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
W=Path(__file__).resolve().parent
B=L/'work/base/work/base/tree_b01ce449'
M=json.loads((L/'out/PATCH_MANIFEST_R3.json').read_text())
files=[*sorted((B/'generator').rglob('*.py')),
       *sorted((B/'student_pilot').glob('*rows*.py')),
       *[B/p for p in ['student_pilot/carrier_c1_routing.py','student_pilot/head_programs.py','headcall/rows.py',
                       'headcall/derive.py','student_pilot/pose_samples.py','student_pilot/recording_pose.py',
                       'student_pilot/carrier_c1_data.py','student_pilot/trace_targets.py','student_pilot/grounding_train.py']]]
records=[]
for p in files:
    text=p.read_text();t=ast.parse(text)
    names=[]
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and (isinstance(n,ast.ClassDef) or any(k in n.name for k in ('render','generate','prepare','build_row','mask_target','clip_row'))):
            names.append(dict(name=n.name,line=n.lineno))
    constants={}
    for n in t.body:
        if isinstance(n,ast.Assign):
            for target in n.targets:
                if isinstance(target,ast.Name) and target.id in ('TYPES','NEW_TYPES','FAMILIES','F17','POLICY','HP_KINDS','POINTING_KINDS','ARMS'):
                    constants[target.id]=dict(line=n.lineno,source=ast.get_source_segment(text,n))
    if names or constants:
        records.append(dict(source_path=str(p),relative_path=str(p.relative_to(B)),sha256=hashlib.sha256(text.encode()).hexdigest(),directly_patched=str(p.relative_to(B)) in M['files'],entry_points=names,family_declarations=constants))
out=dict(source_tree=str(B),patch_manifest=str(L/'out/PATCH_MANIFEST_R3.json'),records=records,
         scope='All generator Python modules, student_pilot row modules, routing/head-program serializers, headcall rows, pose/recording/pointing/timestamp row builders. Encoders and model trainers are consumers, not new text row families.')
(W/'inventory.json').write_text(json.dumps(out,indent=2))
print(json.dumps(dict(source=str(W/'inventory.json'),source_files=len(records))))
