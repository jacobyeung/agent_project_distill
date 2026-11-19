"""Write the bounded delivery report from verified build evidence."""
from pathlib import Path
import datetime,json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21'
def read(p):return json.loads(p.read_text())
tree=read(L/'out/TREE_SEAL.json');kit=read(D/'KIT_INTEGRITY.json')
c=read(D/'proofs/census/CENSUS.json');plan=read(D/'proofs/census/PLAN_RUN.json')
cap=read(D/'proofs/capacity/VERIFIED.json');direction=read(D/'DIRECTION_AUDIT.json')
assert cap['600']['tree_sha256']==tree['tree_sha256']
rem=read(D/'REMOVAL_CENSUS.json');coverage=read(D/'COVERAGE.json')
delivery=read(D/'DELIVERY.json') if (D/'DELIVERY.json').exists() else {}
lines=[
'NO-GO for production: the preserved resolver accepts step 400, and kit q lacks native routing manifests. GO remains false.',
'',
'Build 22 binds the removal list, camera slice, direction twins, absence proofs, and pose record. The final tree admits the CPU fixture at step 600. The exact N pose-index proof and production store audit remain pending.',
'',
f"Report UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}. Host: trinity-1-18. No network, SSH, GPU, Git, or other agents were used.",
'',
'| Item | Result | Evidence / remaining boundary |',
'|---|---|---|',
'| 0 | Done | Own decoded kit request in the actual bwrap view; completed 12:07Z. `LOOKAHEAD_KITQ.json`; 15-line `out/LOOKAHEAD_KITQ.md`. |',
'| 1 | Done | Appended the pinned 109-key list after all 11 existing entries; absent, reordered, duplicated, and altered lists refuse. |',
'| 2 | Bound; intake restriction | All 6,000 camera rows are pinned; 1,728 pass slice intake, 280 hit room exclusions, and 3,992 fail shared grammar. Separate card cell and ceiling; 24 held-out wordings checked with planted rows. |',
'| 3 | Implemented; host audit pending | All 7,971 twins authenticated with N digests and source rooms. STORE exception and source-key K1 filtering tested. The production augmented database has not been materialized here. |',
'| 4 | First boundary | No reviewed RESULT at the accessible named handover paths. Neither optional weights nor relative-count rows are bound. |',
'| 5 | Done | Two NOT_PRESENT slots require configuration, native-builder, and authenticated state-inventory proofs. Other DEFERRED barriers remain. |',
'| 6 | Record bound; index proof pending | Exact pose record attached to data_rows_r2. All 23 qids hit N exclusions; exact N admitted pose indices are unavailable. |',
'| 7 | Done, with inherited launch boundary | Resolver and view code unchanged; helper-mutation scanner refuses; regenerated kit and decoded scan pass. Preserved resolver refuses milestone 600. |',
f"| 8 | Required fixture done; production census partial | Full CPU first batches at {', '.join(sorted(cap))}. Fresh VQA, twin, and routing-slice census; pose/pointing/base-routing counts explicitly inherited. |",
'| 9 | Done | Focused suites, new mutation tests, kit tests, and capacity refusal twins pass; archive verified member by member. |',
'',
'All paths below are relative to `work/build22/` unless stated otherwise. Long tables remain in JSON.',
'',
'| Stage | Reached / refusal | Classification |',
'|---|---|---|',
'| Actual bwrap view | `/usr/bin/true` succeeds with the build-21g view fix | Passed |',
'| GPU guard | E42 on this CPU host | Stand-in boundary |',
'| Own kit request | Source extraction and counting-card validation succeed; `R1_PROOF_NATIVE_ROUTING_REQUIRED` follows | Kit/tree defect: no native routing manifests |',
'| Preserved resolver with step-600 DONE | E20 | Inherited kit contract: resolver authenticates step 400 |',
'| Native capacity 600 | ADMIT; persisted export/checkpoint and all-rank full forward | CPU fixture, with boundary stand-ins |',
('| Native capacity 400 | ADMIT; persisted export and all-rank full forward | CPU fixture, with boundary stand-ins |' if '400' in cap else '| Native capacity 400 | Optional rerun omitted on the final tree | Final verification prioritizes milestone 600 |'),
'',
'The fixture substitutes a tiny Qwen model, synthetic RGB and stores, and the processor/frame-host boundary. Native preparation, row readers, sampling, persisted handover, and full forward paths execute. It uses build 21’s original removal set; the new population bindings are tested separately.',
'',
'| VQA family | Before naming removal | After naming removal | New removals | Final eligible, including twins |',
'|---|---:|---:|---:|---:|']
for name,row in sorted(rem['families'].items()):
 if name=='totals':continue
 lines.append(f"| {name} | {row.get('before',0):,} | {row.get('after',0):,} | {row.get('before',0)-row.get('after',0):,} | {c['vqa']['eligible_by_cell'].get(name,0):,} |")
lines += ['', 'The removal list matches all 109 rows; 107 are additional removals and two were already excluded. `LIST_CENSUS.json` records every family’s first matching list and all overlapping list matches.', '',
'| Routing slice | Input rows | Native intake admitted | Eligible |', '|---|---:|---:|---:|']
for name,row in c['slices'].items():
 n=row['counts'];lines.append(f"| {name} | {n.get('read',0):,} | {n.get('intake_admitted',0):,} | {n.get('eligible',0):,} |")
lines += ['',
'The scanned population contains 204,413 v7 rows and 7,971 twins. It has zero held-out-wording hits, zero unremoved K1 hits, zero unresolved rooms, and zero twin/source room mismatches. The source contains 4,959 K1 keys; the bound union removes them. `AUGMENTED_CENSUS.json` authenticates the prospective population, not a production database hash.',
f"The 1,000-step census plan has {plan['total_draws']:,} draws and maximum repetition {plan['largest_repeat']}. Camera wordings have {plan['cells']['camera_wording']['eligible']:,} eligible rows, {plan['cells']['camera_wording']['draws']:,} draws, and ceiling {plan['cells']['camera_wording']['ceiling']} rows/step. `proofs/census/PLAN_RUN.json` contains every card cell.",
f"Direction has {direction['eligible']:,} eligible rows and {direction['draws']:,} planned draws. `DIRECTION_AUDIT.json` includes draws per row, including zero-draw rows, and front/back/other shares per clause and difficulty. N’s digest differs from raw Unicode serialization on {direction['unicode_digest_differences']} twins. The production loader now emits the same breakdown when it runs.",
'',
'| Direction input clause / difficulty | Front | Back | Other |', '|---|---:|---:|---:|']
for row in direction['input_shares']:
 lines.append(f"| {row['clause']} / {row['difficulty']} | {row['front']['count']:,} ({row['front']['share']:.3%}) | {row['back']['count']:,} ({row['back']['share']:.3%}) | {row['other']['count']:,} ({row['other']['share']:.3%}) |")
lines += ['',
'Production pose, pointing, and the base routing stores are unavailable locally. Their plan counts are inherited and are not a fresh production census. `proofs/census/CENSUS.json` marks them. Slice census stand-ins supply frame metadata only; exact production RGB/coverage manifests remain required.',
'The camera review checked the existing native row validators and passed all 6,000. The slice path additionally applies the unchanged R2 grammar and exclusion envelope. Those checks retain 1,728 rows. `proofs/census/REFUSALS.json` carries examples; no legality or exclusion rule was relaxed to admit the remainder.',
'',
'| Milestone | Rank 0 first loss | Rank 1 | Rank 2 | Rank 3 | Forward records | Refusal twins |',
'|---|---:|---:|---:|---:|---:|---:|']
for step in (s for s in ('600','400') if s in cap):
 row=cap[step];loss=row['first_losses'];lines.append('| '+step+' | '+' | '.join(f'{loss[str(i)]:.8f}' for i in range(4))+f" | {row['records']} | {row['twins']} |")
lines += ['',
f"Every rank runs pose, VQA, routing, and pointing through the full forward pass; all {sum(r['records'] for r in cap.values())} recorded losses are finite. `proofs/capacity/600/q/f.json` holds each stream’s loss. The checkpoint is rebuilt at `proofs/capacity/600/checkpoint`; the package carries metadata and fixture prerequisites, not generated stores or model payloads.",
'',
f"Tests: 127 focused tests; {read(D/'proofs/new_tests/TESTS.json')['tests']} new tests; {read(D/'KIT_TESTS.json')['tests']} rebuilt-kit tests; five inherited scanner/resolver/naming suites; {sum(r['twins'] for r in cap.values())} capacity refusal twins. Details: `REGRESSIONS.json`, `proofs/new_tests/TESTS.json`, `KIT_TESTS.json`, and `work/build21/FINAL_CHECKS.json`.",
f"Changed-statement execution coverage: {coverage['covered']}/{coverage['total']} ({coverage['covered']/coverage['total']:.1%}), using only matching source hashes. `COVERAGE.json` lists uncovered statements. This is not a claim of full production-path coverage.",
'The independent review must assess admission items 3 and 5 and the packed-camera intake adapter. `REVIEW.md`, `TREE_CHANGES.diff`, and failing-before tests identify each change. No swarm_opt2 launch or mode-p patch was added.',
'',
f"Tree seal: `{tree['tree_sha256']}`.",
f"Kit q seal: `{kit['kit_q_seal']}`.",
f"Upload set: {kit['uploads']} files, {kit['upload_bytes']:,} bytes. Versus build 21e: {kit['diff_counts']['added']} added, {kit['diff_counts']['changed']} changed at the same name, {kit['diff_counts']['removed']} removed. Exact files and pins: `UPLOAD_DIFF.json` and `UPLOADS.json`.",
'The regenerated staged set includes the camera rows/wordings, twins/binding/source map/aliases, naming removal, pose record, revised card/config, and sealed tree. The resolver and bwrap view retain their original hashes.',
'`proofs/operator/RESULT.json` lists unavailable static pins, including stale nested provenance references. The builder stages a local file only when its SHA-256 matches; the rebuilt-kit tests require every new launch-binding input in the staging map.',
'']
if delivery:
 lines += [f"Package: `{delivery['package']}` ({delivery['compression']}, {delivery['bytes']:,} bytes; {delivery['members']:,} verified members).",
 f"Package SHA-256: `{delivery['sha256']}`.",
 f"Package seal: `{delivery['package_seal']}`.",
 f"The tar deduplicates {delivery.get('immutable_upload_hardlinks',0)} immutable hash-addressed upload aliases with hard links. It preserves all upload paths and verifies their logical bytes; source code and editable inputs remain separate files.",
 f"Additional fixture prerequisites: {delivery['fixture_prerequisite_bytes']:,} bytes. The fixture resolves inherited metadata through the packaged hash map. Workspace: {delivery['workspace_bytes']:,} bytes, below 6 GB. The external CPU environment remains `/scratch/jjyeung/envs/p1cpu`.",
 'The report and `DELIVERY.json` remain outside the archive to avoid a circular checksum. Reproduce with `CAPACITY_TWINS=1 CAPACITY_STEPS=600 nice -n 10 bash work/build21/run.sh work/build22/native22.py`; the runner enforces eight threads, offline mode, and a 20 GB virtual-memory limit.']
else:lines.append('Package checksum pending archive creation.')
assert len(lines)<200,len(lines)
(L/'out/BUILD22_REPORT.md').write_text('\n'.join(lines)+'\n')
print('Report lines',len(lines))
