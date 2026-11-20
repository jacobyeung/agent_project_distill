from common import *
body="""The pointing list and its dependent receipts are implemented. This blocker applies to cleaning pose mixtures after a future pose-role delta.

The delta tool adds the pose list to all four configurations, stages its exact bytes, preserves stream isolation, updates removal_order, and reseals the kits. Native in-job pool, room-audit, scene, target-filter and preparation producers regenerate their dependent receipts.

Tree 24l4r does not provide a native producer that removes arbitrary listed pose rows from a c1-pose-mix-v1 source. carrier_c1_run.prepare calls c1_pose_mix.prepare and the existing scene-exclusion selection; neither consumes protected pose keys as a filtering rule. The existing removal checks refuse residual listed rows. row_removals.filter_jsonl cannot produce the required pose SQLite receipt and mixture selection.

A pose list produced from protected rows still admitted by the discovery census therefore cannot make that pose store clean through this kit alone. The native preparation/removal check or the bound post-condition will refuse. The pose fixture proves binding, staging, resealing, native stream isolation and the post-condition on explicitly selected fixture rows; it does not prove native pose materialization.

Completing pose cleanup needs a native pose materialization/selection producer, followed by native dependent-receipt regeneration, or an independently authenticated clean pose source. The authorized 24l4r tree patch and the planned pointing/VQA-only 24l4s swap do not supply that producer. No tree, admission, legality or verifier change was made.
"""
replace(L/'out/REMOVAL_RECEIPTS_BLOCKER.md',body)
p=L/'out/bind_protected.py';s=p.read_text()
s=s.replace("dependent_receipts='Regenerated in each fresh job by native pool prepare, room census, scene rebuild, stream materialization/target-filter and preparation; final census is rebound by h.py.',","""dependent_receipts='Regenerated in each fresh job by native pool prepare, room census, scene rebuild, stream materialization/target-filter and preparation; final census is rebound by h.py.',
            pose_cleanup=('BLOCKED_IF_PROTECTED_POSE_ROWS_REMAIN' if stream=='pose' else 'Not requested'),
            pose_cleanup_blocker=('out/REMOVAL_RECEIPTS_BLOCKER.md' if stream=='pose' else None),""")
replace(p,s,0o755)
J.write(D/'POSE_DELTA_LIMITATION.json',dict(status='BLOCKED_IF_PROTECTED_POSE_ROWS_REMAIN',binding_tool_built=True,native_pose_filter_built=False,tree_unchanged=True,blocker='out/REMOVAL_RECEIPTS_BLOCKER.md',scope='Future pose deltas; pointing and routing materialization use existing native producers.'))
print('Pose cleanup limitation documented; native gates unchanged')
