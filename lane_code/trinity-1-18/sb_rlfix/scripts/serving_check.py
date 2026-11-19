"""Record the delivered serving evidence without inventing a missing table."""
from pathlib import Path
import inspect
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1]
cfg=P.load(root/'configs/h100_4.json');tree=P.tree(cfg['tree_root'])
P.sha(__file__)
paths=('evalpath/run.py','evalpath/runtime.py','student_pilot/carrier_c1_decode.py',
       'student_pilot/ground_profiles.py','student_pilot/tower_read.py','student_pilot/tower_scale.py',
       'student_pilot/s1_grounding.py','scripts/gpu_native_selector.py')
for name in paths:P.sha(tree/name)
from evalpath.runtime import generate
from rl_on_n.serving import load_binding
missing=None
try:load_binding(cfg['grounding'])
except ValueError as exc:missing=str(exc)
P.write(root/'out/SERVING_CHECK.json',dict(status='MISSING' if missing else 'BOUND_NOT_EXERCISED',
    command='PYTHONPATH=overlay python -B scripts/serving_check.py',
    requirements=dict(pose_source='tower',camera='frozen_g3t',lifting='frozen_g3t',
                      grounding='sam3_selector',scale='fixed_math',gap='fixed_math'),
    generic_evaluator_default_pose=inspect.signature(generate).parameters['pose_source'].default,
    generic_evaluator_grounding='s1_grounding.build_backend with mask_source=mdg (evalpath/run.py:350-357)',
    native_selector_evidence='ground_profiles.build_profile supports svp_sam3 and native_selector; this alone does not identify the deployed claimed arm',
    missing=[dict(name='claimed-arm serving table',expected_location='configs/h100_{4,8}.json:grounding.serving_table.path',path_supplied=False),
             dict(name='deployed evaluator adapter',expected_location='configs/h100_{4,8}.json:grounding.evaluator_adapter.path',path_supplied=False)],
    refusal=missing,claimed_arm_parity='MISSING; no source table or evaluator adapter was supplied'))
print('Serving check:',missing or 'BOUND_NOT_EXERCISED')
