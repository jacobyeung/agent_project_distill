"""Admit only the exact C8r policy and load the independently pinned selector."""
from .c8 import install
from .io import sha,load
import sys
from pathlib import Path


def apply(freeze,inputs):
    P=install()
    from student_pilot.s1_grounding import default_policy
    import nomdg,gravity_guard
    checks={'proposal_setting':P.SETTING,
            'fusion_policy':nomdg.FUSION,'gravity_guard':gravity_guard.identity()}
    for name,value in checks.items():
        if freeze.get(name)!=value:raise ValueError('P8 frozen value differs from C8r: '+name)
    selector=inputs['selector']
    root=Path(selector['path'])
    manifest=load(root/'MANIFEST.json')
    if sha(root/'MANIFEST.json')!=selector['sha256']:raise ValueError('selector manifest differs')
    if freeze['selector'].get('sha256')!=selector['sha256']:raise ValueError('P8 selector pin differs')
    for row in manifest['files']:
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts or sha(root/rel)!=row['sha256']:
            raise ValueError('selector source/weights differ')
    policy=freeze['candidate_policy']
    if policy.get('name')!=default_policy()['name']:
        raise ValueError('P8 changes the candidate-policy algorithm')
    weights=policy.get('weights',{})
    if sha(weights['path'])!=weights.get('sha256'):
        raise ValueError('K1-refit policy weights differ')
    if weights.get('sha256')!=manifest.get('weights_sha256'):
        raise ValueError('K1 selector manifest does not bind its policy weights')
    from student_pilot.candidate_policy import Policy
    Policy(policy,'object_abs_distance')
    # Rule values are authenticated by their frozen source pins, never rewritten locally.
    for name in ('depth_cut','box_rule','room_rule'):
        record=freeze[name]
        path=Path(inputs['rule_root'])/record['path']
        if sha(path)!=record['sha256']:raise ValueError('P8 rule differs: '+name)
    return policy
