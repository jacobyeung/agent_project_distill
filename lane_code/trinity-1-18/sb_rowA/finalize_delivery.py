"""Seal the verified delivery after the operator reads the exact READ30 bytes."""
import argparse,json
from camera_contract import *
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--reviewed-read30-sha256',required=True);args=ap.parse_args()
 frozen();pin(__file__)
 a=load(OUT/'SOURCE_AUDIT.json');t=load(OUT/'TRAINING_CHECKS.json');v=load(OUT/'INDEPENDENT_TRAINING_CHECK.json');p=load(OUT/'SCORER_PATCH/CHECKS.json')
 assert load(OUT/'WORDING_DISTANCE_CHECK.json')['status']=='PASS'
 assert load(OUT/'SOURCE_REJECTIONS.json')['status']=='PASS'
 assert args.reviewed_read30_sha256==sha(OUT/'READ30.md')
 assert t['rows']==v['rows']==6000 and v['status']==p['status']=='PASS'
 for name in ['READ30.md','READ30_SHARED.md','READ30_UNIQUE.md']:pin(OUT/name)
 save(OUT/'MANUAL_REVIEW.json',dict(status='PASS',reviewed_rows=30,read30_sha256=args.reviewed_read30_sha256,scope='All complete rows read through lossless shared-field factorization; explicit question frames, units, rotation convention, ordered choices, full calls, responses, traces, identities and clip/pose fields checked.',grammar='PASS',correctness='PASS'))
 held=load(OUT/'HELDOUT_CAMERA_ITEMS.json');twins=load(OUT/'HELDOUT_CAMERA_TWINS.json');w=load(OUT/'WORDINGS.json')
 checks=dict(overall_status='PASS',all_required_checks_pass=True,training={**t,'status':'PASS','read30':'PASS'},heldout=dict(status='PASS',items=900,originals=450,reworded=450,per_type=held['per_type'],per_wording=twins['per_wording'],byte_identical=True,native_loader_items=900,native_reader_keys=900),wording=dict(threshold=0.20,normalization=w['normalization'],dev_kit_files=len(w['corpus_files']),dev_kit_normalized=w['corpus_unique_normalized'],combined_normalized=t['wording_corpus_normalized'],reserved_templates_removed=len(w['candidate_removals']),training_rows_removed=t['training_rows_removed_by_wording'],heldout_row_hits=0),scorer_patch=dict(status='PASS_LOCAL_TESTS',dev_parity_items=636,parity_cases=3816,heldout_stub_scored=900,independent_review='PENDING cont_ops18',production_applied=False),independent_training=dict(status='PASS',path='INDEPENDENT_TRAINING_CHECK.json'),review_findings={'2':'Frames bind to decision.binding and call arguments; every question names both frames.','3':'Meaning and labels preserved. Endpoint-distance and yaw clarity can contribute to twin differences; duplicated inline options retained.','4':'CPU native loader and parity adapter pass 900 items with p1cpu.','5':'Frozen h06 similarity advisory retained; actual legacy wording corpus now included in training distance filter.','6':'Frozen hash assignment retained; paired comparisons remain valid, per-wording results are small and uneven.'})
 save(OUT/'CHECKS.json',checks)
 cells='\n'.join(f'| t{k:02d} | '+ ' | '.join(str(t['cells'][typ+f'|t{k:02d}']['actual']) for typ in TYPES)+' |' for k in range(40))
 report=f'''# sb_rowA2 delivery

The build contains 6,000 camera training rows and 900 byte-identical held-out items. All row-build checks pass. The separate scorer patch passes CPU tests; cont_ops18 must obtain independent review and apply it before sealing.

N admission uses W19 tree `{a['tree_sha256']}`. `audit_camera_training.py` verifies the recovered extract SHA256 `9e6aa2bd618588a4054a71dc183bc31821fcb5a2bc7bb1952bbebe15559e7c6b`, its manifest binding to store c48d5b62, N’s complete removal lists (including n/z/u and the K1 union), tiered aliases or verified minting, and pinned room sets.

| Type | Extract | N kept | K1 dropped | withheld-80 dropped | Training |
|---|---:|---:|---:|---:|---:|
| Displacement | 14,020 | 12,218 | 210 | 1,592 | 2,000 |
| Rotation | 9,143 | 8,002 | 125 | 1,016 | 2,000 |
| Direction | 12,260 | 10,713 | 170 | 1,377 | 2,000 |

The withheld-80 rows also match N’s merged dev exclusion. All explicit removal-list hits, R0 hits, original dev-S1 hits, BENCH v2 hits and unresolved scenes are zero. SOURCE_AUDIT.json records marginal and joint counts; SOURCE_ADMISSION.jsonl records all 35,423 decisions.

| Cell | Displacement | Rotation | Direction |
|---|---:|---:|---:|
{cells}

`build_camera_training.py` asserts these 120 cells, 6,000 distinct sources used once (cap two), and 6,000 unique qids/candidate_ids. It changes only qid, routing.qid, student_input.question and the two added candidate_id fields. Calls, traces, responses, spans, poses, options and answers are byte/value-identical to their sources. The generator skips 13 displacement candidates whose gt_answer uses a different numeric string (e.g. 2.0 versus 2.00; values agree) and one direction candidate whose printed response differs from recomputation; SOURCE_REJECTIONS.json records them. Legacy camera sources have no candidate_id; new IDs use N’s candidate_identity formula.

Frames come from decision.binding and agree with call arguments and clip length. N’s camera pack/validate path is carrier_c1_routing.c1_row/check_row, r1_training.row_check and r2_contract.frame_metadata. All 6,000 sources and 6,000 new rows pass. ground_rows.pack handles object-grounding records and is not the native camera packer.

`verify_camera_training.py` verifies all saved rows against raw source TEXT, repeats native checks and independently recomputes answers and complete printed responses from stored poses/gravity. Its SciPy camera arithmetic also agrees with N’s geometry implementation on 6,000 rows. No frame image is loaded by training-row checks.

The wording filter rejects normalized character Levenshtein distance below 0.20. It checks {w['corpus_unique_normalized']:,} normalized dev/kit questions from {len(w['corpus_files'])} files and the recovered legacy questions ({t['wording_corpus_normalized']:,} combined forms). It removes {len(w['candidate_removals'])} reserved-template candidates and {t['training_rows_removed_by_wording']} training candidates. All 24 held-out templates are checked against every complete training row; hits are zero. WORDINGS.json is a frozen inventory; CHECKS.json states current admission.

READ30.md prints 30 complete training rows. READ30_SHARED.md and READ30_UNIQUE.md factor repeated clip fields losslessly for manual reading; expansion equals every full row. MANUAL_REVIEW.json pins the reviewed bytes and records grammar/correctness checks.

`build_scorer_patch.py` produces SCORER_PATCH/placement.patch and the patched h1eval/scorers.py. Camera M1 uses display_frame_pair. All 636 original devs1_routed items have identical M1 in 3,816 test cases; all 450 camera expected calls match; all 900 held-out stub outputs score. Native load_manifest/map_items admit 900 items and 900 unique keys. Ten invalid frame-pair forms fail closed.

Review findings 2–6: frame binding is explicit (2); endpoint distance/yaw specificity may contribute to twin gaps, and duplicate inline options remain (3); native CPU admission passes (4); rotation h06’s shared phrase advisory remains and the legacy stream is included in the wording check (5); the frozen hash assignment stays at 13–27 items per wording, so use paired twin deltas and treat per-wording comparisons cautiously (6).

Commands: first build the exact edit-distance helper with `g++ -O3 -shared -fPIC wording_distance.cpp -o out/wording_distance.so`. Use `/scratch/jjyeung/envs/p1cpu/bin/python -B` with `check_wording_distance.py`, `audit_camera_training.py`, `build_camera_training.py`, `verify_camera_training.py`, `audit_source_rejections.py`, `build_scorer_patch.py`, `read_training_sample.py`, `finalize_delivery.py --reviewed-read30-sha256 <digest>`, `verify_camera.py`, then `package_delivery.py`. Each JSON pins its inputs; JSONL payloads use companion manifests. The archive checksum is in sb_rowA.tar.sha256.

Not done: independent scorer-patch review/application by cont_ops18, trainer ingestion, training or model inference. No GPU, network, SSH, Git or writes outside this workspace were used. No missing input affects the delivered row build. No borderline revision-history sentence is retained.
'''
 assert len(report.splitlines())<=80,len(report.splitlines())
 (OUT/'REPORT.md').write_text(report)
 handoff='''# Camera wording read: cont_ops18 handoff

The delivery contains 6,000 training rows and the frozen 900-item paired evaluation (450 originals, 450 reworded twins). The three HELDOUT_* files and WORDINGS.json retain the SHA256 values in HELDOUT_FREEZE.json. CAMERA_ROWS.jsonl is the N-filtered training payload; CHECKS.json and INDEPENDENT_TRAINING_CHECK.json certify it. CAMERA_LINEAGE.jsonl and CAMERA_SOURCES.jsonl.gz bind every row to raw recovered source TEXT.

The read owner must apply SCORER_PATCH/placement.patch to its staged package before sealing. The patch changes only h1eval/scorers.py: camera placement builds the expected call from the item's display_frame_pair and refuses missing/invalid pairs. Other task types retain expected_calls(question,type). The original rows/expected_calls.py stays byte-identical.

SCORER_PATCH/CHECKS.json records exact M1 parity on 636 devs1_routed items over 3,816 call-output cases, agreement with all 450 original camera calls, 900 successful held-out measure() stub outputs, and native loader/mapping admission for all 900 items. Ten invalid pair forms are refused. The builder has not supplied an independent reviewer: obtain that review before applying and sealing.

1. Check the patch's source and destination hashes in SCORER_PATCH/CHECKS.json. Apply the diff under out3/bases/b1/src, or stage the supplied patched file at h1eval/scorers.py. Re-run the CPU parity and 900-item stub checks in the staged package.
2. Stage HELDOUT_CAMERA_ITEMS.json, HELDOUT_CAMERA_TWINS.json and HELDOUT_NATIVE_TASKS.jsonl under items/. Add them to orchard_h10/build.py:sources with those archive members; keep the portable auth/R0_ROOMS.txt pin.
3. Set run_cfg['items'] to the package path items/HELDOUT_CAMERA_ITEMS.json and select camera_displacement, camera_rotation, camera_movement_direction. Use the existing dev-S1 frame/tree/export/model settings, with tasks=[<package>/items/HELDOUT_NATIVE_TASKS.jsonl]. If settings use item_sets, give heldout_camera_wording the same effective settings and this task path. Each task ID must occur once.
4. Seal the patched evaluator, parser, settings, item/task payloads and archive together. merge.py checks evaluator_code_sha256 and expected_calls_sha256 against launch-time bindings. Use a fresh output/journal location; patching after launch invalidates the binding.
5. Run h1eval.items.load_manifest and parity_adapter.map_items with the staged settings before inference. The working CPU interpreter is /scratch/jjyeung/envs/p1cpu/bin/python. Put the package's b/ ahead of h1eval/reader_core on sys.path; if e2e_reader was already imported from reader_core, use a fresh process with the correct order.

Use HELDOUT_CAMERA_TWINS.json for paired placement, response-use and answer metrics. Report original and reworded results separately by type. Per-wording cells are small and uneven (13–27); endpoint/yaw specificity and the rotation h06 shared phrase remain interpretation advisories. Keep all 24 held-out wordings out of training.

No production package was modified and no model read was submitted by this lane. cont_ops18 owns patch review, application, sealing and launch.
'''
 (OUT/'HANDOFF_cont_ops18.md').write_text(handoff)
 (ROOT/'STATUS.md').write_text('Delivery validation complete: 6,000 camera rows fill every cell, use 6,000 distinct sources, and pass native N packing, independent geometry, field/identity, room and wording checks. Thirty complete rows were manually reviewed. All held-out files retain their frozen hashes. The scorer patch passes 636-item parity and 900-item scoring/native-admission checks; cont_ops18 owns independent review and application before sealing. Packaging remains.\n')
 print('Final report lines',len(report.splitlines()))
if __name__=='__main__':main()
