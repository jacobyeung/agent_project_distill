import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';T=L/'work/tree_r1'
old=json.loads((L/'work/build8/proofs/suite_tree/r2/GROUP_RECEIPT.json').read_text())['inputs']['source']
now=json.loads((L/'out/TREE_SEAL.json').read_text())['files']
changed={name:dict(before=old.get(name),after=now.get(name)) for name in sorted(set(old)|set(now)) if old.get(name)!=now.get(name)}
inv=json.loads((B/'proofs/audit/INFERENCE_COMPONENTS.json').read_text())
unchanged={r['file'] for r in inv['known_outside_forward']}
assert all(old[n]==now[n] for n in unchanged)
protected=['student_pilot/r2_dev_merged.json','student_pilot/r2_withheld.json','student_pilot/r0_scenes.json',
           'student_pilot/gf1_cache.py','tests/test_gf1_cache.py','launch_s1/b/wh.json']
assert all(old[n]==now[n] for n in protected)
(B/'CHANGE_SCOPE.json').write_text(json.dumps(dict(changed_since_build8=changed,
    known_outside_forward_files_unchanged=sorted(unchanged),protected_inputs_and_original_bf16_assertion_unchanged=protected),indent=2)+'\n')
print(json.dumps(dict(changed_files=len(changed),known_inference_files_unchanged=True,protected_inputs_unchanged=True)))
for p in (B/'report9.py',B/'weighted_cpu.py'):
    compile(p.read_bytes(),str(p),'exec')
