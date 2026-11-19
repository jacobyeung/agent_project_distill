from pathlib import Path
import ast,json,hashlib,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build17';T=L/'work/tree_r1';P=L.parent/'w16b/work/tree_r1';O=B/'proofs/preservation';O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['launch_r1/p_handover_receipt.py','student_pilot/r2_openers.py','student_pilot/r1_mix.py',
       'student_pilot/row_text_audit.py','student_pilot/r2_intake.py','student_pilot/r1_counting.py',
       'student_pilot/carrier_c1_run.py','student_pilot/carrier_c1.py','student_pilot/r2_policy.py']
equal={name:dict(sha256=sha(T/name),equal=sha(T/name)==sha(P/name)) for name in files}
assert all(v['equal'] for v in equal.values())
def functions(p):
    s=p.read_text()
    return {n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old=functions(P/'student_pilot/carrier_c1_run.py');new=functions(T/'student_pilot/carrier_c1_run.py')
names=['train','run_steps','fetch','Rows','load_model','export','checkpoint','prepare','prepared','check_plan_rows']
native={n:old[n]==new[n] for n in names};assert all(native.values())
cfg=json.loads((B/'inputs/kit_config.json').read_text())
assert cfg['r2_identity']['init']['step']==544 and cfg['init_artifact']['artifact']['sha256'].startswith('1d6eeb28')
assert cfg['camera_overrides']['weight_scale']==cfg['r1_training']['weight_scale']==.04
assert cfg['remove_files'][-2]['sha256'].startswith('02315a74') and cfg['remove_files'][-1]['sha256'].startswith('caba6a56')
out=dict(files=equal,native_functions=native,parent=cfg['r2_identity']['init'],scale=.04,
    remove_order=[p['sha256'] for p in cfg['remove_files']],
    intentional_changes=['N data sources and exclusions; procedure-only counting card/guard',
        'N persisted-file handover by SHA-256; original-path behavior preserved without persisted_files',
        'Native export initialization resolves the authenticated full-weight directory and avoids stale mirror shortcuts inside a pin scope',
        'First-batch proof accepts an absolute resumed plan; default start_step=0 unchanged',
        'Separate unsubmitted kit q proof mode'],
    inherited_not_rerun=['144000-case geometry parity sweep: input absent (/scratch/jjyeung/orch_n30/review_tree11/work/parity/geo_dump.py)'],
    qualification='No claim of full production qualification or full real-row parity. Native inference/training forward functions are byte-equal.')
(O/'RESULT.json').write_text(json.dumps(out,indent=2));print('Preserved',len(equal),'files and',len(native),'native functions')
