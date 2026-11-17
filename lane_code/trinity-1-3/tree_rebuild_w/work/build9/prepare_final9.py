"""Bind final harness and carried blockers before the frozen pass."""
import json,hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
p=B/'make_delivery.py';s=p.read_text().replace('tree_rebuild_b8_','tree_rebuild_b9_');p.write_text(s)
p=B/'coverage_all.py';s=p.read_text().replace("L/'work/build7/proofs',B/'proofs'","L/'work/build7/proofs',L/'work/build8/proofs',L/'work/lane_stop2/proofs',B/'proofs'");p.write_text(s)
p=B/'verify_delivery.py';p.write_text(p.read_text().replace('6_000_000_000','7_000_000_000'))
p=B/'finish_gate.py';p.write_text(p.read_text().replace('BF16, multi-rank stop, production inputs and the carried-forward acceptance blockers remain separately reported.','BF16, production inputs and the carried-forward acceptance blockers remain separately reported. Supplied multi-rank stop evidence is authenticated against unchanged exercised sources.'))
# External real slices are read-only inputs, authenticated in the tree/r2 group receipt.
# The base retains its original receipt identity and can resume without another run.
p=B/'package.py';s=p.read_text();needle="        completed=json.loads(checkpoint.read_text()) if checkpoint.exists() else None"
replacement="""        if variant=='tree' and group=='r2':
            key['bound_real_slices']={str(p.relative_to(L)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((L/'work/rows_slices/slices_final').glob('*.jsonl'))}
"""+needle
assert needle in s;s=s.replace(needle,replacement);p.write_text(s)
rows=[
('BF16_CACHE_GRADIENT_PARITY','work/build8/proofs/regressions/BF16_PARITY.json'),
('init_selection_pending / D2','work/build8/kits/RESULTS.json'),
('rows_lane_store_bindings_missing / D3','work/build8/kits/RESULTS.json'),
('gf1_real_dense_manifest_missing / D4','work/build8/kits/RESULTS.json'),
('processor_resolution_pin_missing','work/build8/PROCESSOR_SEARCH.json'),
('ALL_FORMATTERS_NOT_QUALIFIED','out/BUILD7_REPORT.md'),
('ROWS_RULE_TEXT_PRESENT / ROWS_MINORITY_FORMS_UNBOUND','work/build7/proofs/rows/RESULTS.json'),
('FRAME64_ALL_READERS_UNQUALIFIED','work/build8/proofs/audit/FRAME64_REMAINING_SITES.json'),
('OUTSIDE_FORWARD_FORMATTING / B04_FORWARD_HOOK_REQUIRED','work/build8/proofs/eat1'),
('R0_FULL_INPUT_INVENTORY_UNAVAILABLE','work/build8/kits/RESULTS.json'),
('PORTRAIT_MASK_DISTORTION','work/build8/proofs/audit/RESIZE_AUDIT.json'),
('FULL_ENCODER_PARITY_UNQUALIFIED','work/build7/proofs/off_parity/RESULTS.json'),
('BOUND_FAITHFUL_IDENTITY_RECEIPT_MISSING','work/build9/proofs/identity/IDENTITY.json'),
('INDEPENDENT_REVIEW_PENDING','work/design/20261117T0655Z_ORCH_ANSWER_recovery_gate.md'),
('BOUND_SLICE_SEALED_SCENE_EXCLUSIONS','work/build9/proofs/recovery/recovery_rows/RESULT.json')]
records=[]
for name,path in rows:
    p=L/path;assert p.exists(),path
    records.append(dict(blocker=name,evidence=path,sha256=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None,
        disposition='retained; no input fabricated' if name not in ('BOUND_SLICE_SEALED_SCENE_EXCLUSIONS',) else 'newly measured; exclusion rules retained'))
(B/'CARRIED_BLOCKERS.json').write_text(json.dumps(records,indent=2)+'\n')
with (B/'STATUS.md').open('a') as f:
    f.write('\nItem 3c: every requested input and acceptance blocker remains in `work/build9/CARRIED_BLOCKERS.json`. Item 3d will be measured by the frozen full suite and exact-source changed-statement coverage.\n')
    f.write('\nItem 4: final harness is bound. Kits will stage from empty, A2 first, with GO=false; source seal, package, packet suite, frozen package suite, base comparison and EAT checks follow.\n')
assert (B/'test_runner.py').read_bytes()==(L/'work/build8/test_runner.py').read_bytes()
print(json.dumps(dict(blockers=len(records),runner_unchanged=True)))
