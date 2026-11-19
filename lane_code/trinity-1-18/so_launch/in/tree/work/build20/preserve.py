from pathlib import Path
import ast,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build20';T=L/'work/tree_r1';P=L.parent/'w19/work/tree_r1';O=B/'proofs/preservation';O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['launch_r1/p_handover_receipt.py','launch_r1/p_export_receipt.py','student_pilot/r2_openers.py',
 'student_pilot/r1_mix.py','student_pilot/row_text_audit.py','student_pilot/r2_intake.py','student_pilot/r1_counting.py','student_pilot/carrier_c1.py']
equal={n:dict(sha256=sha(T/n),equal=sha(T/n)==sha(P/n)) for n in names};assert all(v['equal'] for v in equal.values())
def functions(p):
    s=p.read_text();return {n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old=functions(P/'student_pilot/carrier_c1_run.py');new=functions(T/'student_pilot/carrier_c1_run.py')
native={n:old[n]==new[n] for n in ('train','run_steps','fetch','Rows','load_model','checkpoint','prepared','check_plan_rows')};assert all(native.values())
cfg=json.loads((B/'inputs/kit_config.json').read_text());prior=json.loads((L/'work/build19/inputs/kit_config.json').read_text())
keys=('r2_identity','init_artifact','camera_overrides','remove_files','exclusions','dev_scene_exclusions','benchmark_scene_exclusions','routing_opener_init')
unchanged={k:cfg[k]==prior[k] for k in keys};assert all(unchanged.values())
(O/'RESULT.json').write_text(json.dumps(dict(files=equal,native_functions=native,config=unchanged,parent=cfg['r2_identity']['init'],weight_scale=cfg['camera_overrides']['weight_scale']),indent=2))
