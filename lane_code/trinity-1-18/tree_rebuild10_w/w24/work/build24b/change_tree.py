from pathlib import Path
import shutil,json,hashlib,difflib
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';A=L/'attic/build24b/tree';D=L/'work/build24b'
names=['student_pilot/r1_persisted.py','student_pilot/r1_training.py','student_pilot/r1_handover.py','launch_r1/entry.py','launch_r1/production_proof.py']
for name in names:
 p=A/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();shutil.copyfile(T/name,p)
p=T/names[0];s=p.read_text()
s=s.replace("def export_only(receipt, mode=None):\n",'''INIT_POLICY = 'step400_export_weights_fresh_v1'


def init_policy(value):
    """The pinned declaration permits only fresh initialization from step 400."""
    if 'init_policy' not in value:
        return None
    if value['init_policy'] != INIT_POLICY:
        raise ValueError('P_EXPORT_INIT_POLICY_INVALID')
    if value.get('proof_mode') != 'train':
        raise ValueError('P_EXPORT_INIT_TRAIN_MODE_REQUIRED')
    if not value.get('handover_receipt') or 'persisted_files' not in value:
        raise ValueError('P_EXPORT_INIT_RECEIPT_REQUIRED')
    return INIT_POLICY


def export_only(receipt, mode=None, *, init_policy=None):
    if init_policy is not None:
        if init_policy != INIT_POLICY:
            raise ValueError('P_EXPORT_INIT_POLICY_INVALID')
        if mode != 'train':
            raise ValueError('P_EXPORT_INIT_TRAIN_MODE_REQUIRED')
        if receipt.get('schema') != 'p-export-only-v1' or type(receipt.get('step')) is not int or receipt['step'] != 400:
            raise ValueError('P_EXPORT_INIT_STEP400_ONLY')
''')
s=s.replace("    if mode != 'q' or not _proof.get():", "    if init_policy is None and (mode != 'q' or not _proof.get()):")
s=s.replace('weights=False, proof_mode=None):','weights=False, proof_mode=None, init_policy=None):')
s=s.replace('only = export_only(receipt, proof_mode)','only = export_only(receipt, proof_mode, init_policy=init_policy)')
s=s.replace("weights=weights,proof_mode=value.get('proof_mode'))", "weights=weights,proof_mode=value.get('proof_mode'),init_policy=init_policy(value))")
s=s.replace("return dict(result, status='ADMIT',absolute_resume_step=step)","return dict(result, status='ADMIT',absolute_resume_step=step,init_milestone=result['receipt']['step'])")
p.write_text(s)
p=T/names[1];s=p.read_text().replace("def validate(cfg):\n    value = cfg['r1_training']", "def validate(cfg):\n    value = cfg['r1_training']\n    from .r1_persisted import init_policy\n    init_policy(value)")
s=s.replace('from .r1_persisted import verify, scope','from .r1_persisted import verify, scope, init_policy')
s=s.replace("proof_mode=value.get('proof_mode'))", "proof_mode=value.get('proof_mode'),init_policy=init_policy(value))")
s=s.replace("    value = cfg.get('r1_training') or {}\n    if 'persisted_files'", "    value = cfg.get('r1_training') or {}\n    from .r1_persisted import init_policy\n    init_policy(value)\n    if 'persisted_files'")
s=s.replace("    return progress(cfg, artifact)['step']", "    step = progress(cfg, artifact)['step']\n    from .r1_persisted import init_policy\n    return 0 if init_policy(cfg['r1_training']) is not None else step")
p.write_text(s)
p=T/names[2];s=p.read_text().replace('from .r1_persisted import verify, scope','from .r1_persisted import verify, scope, init_policy').replace('from .r1_persisted import export_only','from .r1_persisted import export_only, init_policy')
s=s.replace("proof_mode=value.get('proof_mode'))", "proof_mode=value.get('proof_mode'),init_policy=init_policy(value))")
s=s.replace("export_only(receipt, value.get('proof_mode'))", "export_only(receipt, value.get('proof_mode'), init_policy=init_policy(value))")
p.write_text(s)
p=T/names[3];s=p.read_text().replace("    value = cfg.get('r1_training', {})\n", "    value = cfg.get('r1_training', {})\n    from student_pilot.r1_persisted import init_policy, export_only\n    policy = init_policy(value)\n",1)
s=s.replace("        if receipt.get('schema') == 'p-export-only-v1':\n            raise ValueError('P_EXPORT_ONLY_TRAINING_LAUNCH_REFUSED')", "        if policy is not None:\n            export_only(receipt, value.get('proof_mode'), init_policy=policy)\n        elif receipt.get('schema') == 'p-export-only-v1':\n            raise ValueError('P_EXPORT_ONLY_TRAINING_LAUNCH_REFUSED')")
p.write_text(s)
p=T/names[4];s=p.read_text().replace('from student_pilot.r1_persisted import verify, scope','from student_pilot.r1_persisted import verify, scope, init_policy')
s=s.replace("weights=bool(request.get('weights')),proof_mode=value.get('proof_mode'))", "weights=bool(request.get('weights')),proof_mode=value.get('proof_mode'),init_policy=init_policy(value))")
s=s.replace("        if result['absolute_resume_step'] not in (400,600):", "        result['init_milestone'] = handover['init_milestone']\n        expected_start = 0 if init_policy(cfg['r1_training']) is not None else step\n        if result['init_milestone'] not in (400,600) or result['absolute_resume_step'] != expected_start:")
p.write_text(s)
changes={};patch=[]
for name in names:
 a=(A/name).read_text();b=(T/name).read_text();compile(b,str(T/name),'exec')
 changes[name]=dict(before=hashlib.sha256(a.encode()).hexdigest(),after=hashlib.sha256(b.encode()).hexdigest())
 patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='build24/'+name,tofile='build24b/'+name))
(D/'TREE_CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n');(D/'TREE_CHANGES.diff').write_text(''.join(patch))
print('Changed',len(changes),'source files')
