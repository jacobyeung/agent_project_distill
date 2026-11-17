"""Write current findings and the exact operator boundary."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
def load(n):return json.loads((H/n).read_text())
def sha(n):return hashlib.sha256((H/n).read_bytes()).hexdigest()
inputs=load('evidence/fix7_selection/inputs.json');ids=load('ids.json');up=load('UPLOAD.json')
raw=load('evidence/derivation/d0/k/pool_selection.json');sel=load('payload/d_f232d4160d75b582.json')
manifest=load('build/fx/k/pool_manifest.json')
appendix=['Each row gives the original pin, the catalog locator, its expected Orchard location, byte count and local availability. Orchard presence has not been inspected; the tool authenticates it before use. Sizes for missing gzip files come from the pinned manifest and agree with k/0.json staged_inputs.packages[0].inventory.','',
'| Original path | SHA256 | Logical catalog path | Expected Orchard path | Bytes | Local bytes |','|---|---|---|---|---:|---|']
for v in inputs:appendix.append('| '+ ' | '.join([f"`{v['original_path']}`",f"`{v['sha256']}`",f"`{v['logical_path']}`",f"`{v['orchard']}`",str(v['bytes']),f"`{v['local']}`" if v['local'] else 'Absent from local fixture'])+' |')
(H/'evidence/fix7_selection/INPUTS.md').write_text('\n'.join(appendix)+'\n')
rows=[]
for e in manifest['sets']:
 m=e['files']['packed' if 'packed' in e['files'] else 'rows'];rows.append(f"| {e['name']} | `u/eb3429c5/{m['sha256'][:16]}.jsonl.gz` | {m['bytes']:,} | {m['rows']:,} |")
report=f'''The equality tool and deriver gate are implemented and tested. Production selection equality remains unverified because this workspace lacks all 13 source gzip files (95,354,406 compressed bytes). The packet remains BLOCKED. No production selection was relabeled, generated or approved locally.

**How the selection is produced**

`build/tree/student_pilot/s1_pool.py:268` is the CLI entry point (`python -m student_pilot.s1_pool --manifest ... --output ... --remove-files ... --tokenizer ...`). It calls `prepare(manifest_pin, output, remove_files, tokenizer_pin, room_sets)` at line 125. `Pool` authenticates the manifest, three QID membership lists and two scene-exclusion files at lines 19–41. The six removal specifications include the fourth list's defect restriction; the two empty lists are distinct logical inputs with the same SHA256 (`row_removals.py:21–52`). The source tokenizer is loaded at `s1_pool.py:96–101`; negative-zero room normalization is at lines 60–87.

`prepare` scans all 13 manifest sources in their manifest order, including deferred sources. It authenticates gzip bytes, checks size, unique QIDs, source/type counts and scene membership, applies scene/QID/label exclusions, then validates and records kept source indices in their original order (`s1_pool.py:132–209`). Its receipt records every per-source count, removal report, independent census, blocker, pin and admission flag (`s1_pool.py:210–223`). Equal source SHA256 plus equal ordered index arrays establishes equal approved QIDs and order; the tool compares both arrays and their serialized hashes. The source hash also binds excluded rows, while unchanged list pins, defect rules and recomputed counters bind exclusion/removal membership.

The pinned D0 selection is **not** the raw `prepare` receipt. The sealed raw receipt (`k/pool_selection.json`, SHA256 `{sha('evidence/derivation/d0/k/pool_selection.json')}`) selects 92,607 rows. D0 then defers `ROUTE_direct` with reason `moved_to_vqa_store`, removes its selection/retained/per_type fields, keeps its seen/after-manifest/eligible counters, and recomputes selected_rows as 83,184. `in/D0_JOB_B_PACKET.md:7` records the move; `in/REVIEW_JOB_B_R9.md:19` records the final reason spelling. The original editing script is not in this workspace. `tools/selection_check.py:58` reconstructs this exact policy transformation; applying it to the sealed raw receipt reproduces the complete pinned D0 JSON. The tool checks raw regeneration equality **before** comparing the policy-adjusted result, including counters that the D0 policy omits.

`pool_selection_aa128e6f.json` is supplied here as `payload/d_f232d4160d75b582.json`, SHA256 `{sha('payload/d_f232d4160d75b582.json')}`. Its catalog locator is the logical kit root plus `k/pool_selection_aa128e6f.json`; this is an added D0 record, not a member of the original sealed kit. The standalone tool embeds these exact reference bytes.

**What implementation() covers**

`build/tree/student_pilot/s1_pool.py:93–95` hashes `p3_provenance.source_files([s1_pool.py])`. `p3_provenance.py:58–95` walks local Python imports recursively, including imports inside function bodies and package initializers. It records the broad local static closure, not just functions that execute during selection. It does not hash third-party libraries, data, tokenizer assets or configuration; those data inputs have separate pins.

| Changed closure member | Executable change and effect on selection |
|---|---|
| `carrier_c1.py:506` | Adds pose loss in routing training. `prepare` never constructs or calls CarrierC1. |
| `carrier_c1_routing.py:442,477` | Adds faithful handling to `finish` and `encode_own`. These are its only changed definitions; selection uses unchanged alias helpers through `s1_exclusions.py:7`. |
| `carrier_c1_run.py:62,448,645,659,1019,1195,2233` | Changes config validation, stream preparation, faithful/reserve gates, batch targets and training control. `s1_pool.prepare` does not call them. |
| `h1.py:17,40,64,94` | Adds H1 settings, pose targets, metrics and stop accounting; not executed by selection. |
| `h1_faithful.py:83,111,148,197` | Adds faithful camera rendering and its preparation threshold; not executed by selection. |
| `h1_r0.py:45,85,105,118` | Filters reserve rooms in downstream preparation/admission. It can change final training membership, but does not change the pool selection. |
| `generator/derivgen_v7/derivgen/materialize.py:494` | Adds printed-value replay used by faithful camera handling, not pool validation. |

The seven changes do not alter the selector's QIDs, order, counts, exclusions/removals or blockers for identical inputs and dependencies. This is a code-path finding, not a completed production equality result. `evidence/fix7_selection/changes.json` and the three diffs authenticate the changed definitions against the retained D0 archive. The directly executed selector, packed-row validator, removals, exclusions, census and provenance modules are byte-identical. H1's expected closure digest is `2a4ef06888c59743516f5f7edad4ac3d45c6868cc5d3034ddae13654c8a6cc9c`.

**Inputs and tool**

The catalog's logical kit root is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/`. The intended login-node physical root is `/project/community/jjyeung/okh7/x_07ca49df/`, with the same `k/` and `u/` suffixes. Original Trinity locators embedded in receipts are provenance strings; the resolver uses only catalog-mapped bytes under the supplied kit. It never falls back to those old paths.

There are 38 input pin occurrences: 25 have authenticated local bytes (17,070,690 bytes, counting repeated logical inputs) under `build/fx/k/`; 13 source gzip inputs are absent locally. The local inputs include the manifest (67,752 bytes), tokenizer (12,807,982 bytes), three QID lists, two scene lists, six removal specifications and 12 raw selection-index files. `evidence/fix7_selection/INPUTS.md` lists **every full SHA256, original path, logical path, expected physical location and size**. `inputs.json` is its machine-readable version. No input must be fetched from Trinity if the catalog-listed Orchard kit files are present. Remote availability is unverified and fails closed at runtime.

| Source | Kit-relative path | Compressed bytes | Rows |
|---|---|---:|---:|
{chr(10).join(rows)}

The kit deployment record also describes the containing package as 161,976,320 bytes, SHA256 `f0e715135f4b7cd8e38c046e2dd1a0a11ea98c2de4c5dbca53ee92f1a12f3e13`, destination `u/eb3429c5` (`build/fx/k/0.json:1`, staged_inputs.packages[0]). Its old `/home` source locator was neither opened nor searched. The check requires the catalog files already staged in the kit; it does not fetch or unpack that data package.

`tools/selection_check.py:112` authenticates the source tree, redirects pin resolution to hash-checked catalog bytes, preflights **all** inputs, and calls the real H1 `prepare`. It restores an output index locator only after the newly written array and SHA256 match the original index file. It never substitutes the old implementation map. `differences` at line 47 compares recursively, including key presence, list order and JSON types; the only ignored receipt field is implementation. Raw and final equality must both pass. Exit 0 means EQUAL; exit 1 means different content; exit 2 means missing/invalid inputs or execution failure. A completed run emits `r.json` (new selection), `q.json` (equality report) and native receipts/indices/logs. A blocked run emits q.json without inventing a selection.

`build/q.sh` ({(H/'build/q.sh').stat().st_size:,} bytes) embeds the tool and pinned reference/config/code records. It verifies its compressed payload and the existing trainer archive, extracts only authenticated regular source members into a fresh private directory, and runs under bubblewrap with both logical roots, read-only kit mounts, `--unshare-net`, offline flags, one CPU thread and nice 19. It defaults to `PY_GATE=/project/community/jjyeung/latency/envs/fit/bin/python3`; native imports require torch/numpy/tokenizers. It installs nothing. New visible names are opaque; tracebacks and native source names stay in private logs. Output is `BUN/q_7b62108a/o/`, where BUN is `/project/community/jjyeung/okh7/i_1be16f28`. It refuses an existing output; preserve it and review the refusal before preparing another attempt.

The exact tool ran locally with the available pinned inputs and returned exit 2 on missing `u/eb3429c5/a67a3f6f489031d4.jsonl.gz`. `evidence/fix7_selection/production_attempt/q.json` records that refusal. Local native regeneration on synthetic inputs returned EQUAL, then DIFFERENT after a content mutation. The login-node bubblewrap invocation has not run; its bootstrap, checksum failure path, script syntax and visible names were tested locally.

**Admission audit past line 215**

All mutations and synthetic reports live only in `evidence/fix7_admission/` or `evidence/fix7_selection/`. None is included in payload or upload archives. `tests/test_fix7_admission.py:23` copies the real selection and changes only its implementation field for the isolated audit. Production rows are missing, so that test supplies a test-only relocation result and model descriptor; it authenticates the actual route-policy bytes and traces execution through line 219. It does not claim that production relocation succeeded.

| Native check | Executed result | Limit or further refusal |
|---|---|---|
| `s1_routing.build:215–219` with test-only production selection | Reached 219 | Missing actual r16 receipt, SHA256 `9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851`; recorded logical path is `/ap/5e1d07a4/f/h/r16/receipt.json` under the same logical user root. |
| `s1_routing.build:196–456`, synthetic native room/direct sources | PASS, two rows | Native relocation, division, frame/FPS metadata, row validation, census, filtering, materialization and receipt writes execute. Empty legacy database and a character processor are explicit fixtures; production tokenizer/model and RGB bytes remain untested. |
| `s1_routing.build:217,220`; `compatibility:166` | Negative tests PASS | Refuses scene blockers, heldout division and wrong legacy row count. |
| `s1_routing.build:276–277,414–455` | Negative test PASS | A one-token suffix limit defers rows and refuses materialization with `no_admitted_pool_program_rows`. |
| `s1_exclusions.totals:232` and coverage machinery | PASS on fixtures | Production source-specific coverage quotas and all-row accounting remain untested. |
| `h1_faithful.prepare_identity:197–219` | Negative test PASS | Fixture has no camera rows; native code refuses `S1 launch requires faithful identity >= 95% on the bound routing receipt`. Production camera identity rate remains unknown. |
| `h1_r0.prepare:105`, `before_admission:118` | PASS on fixtures | Real reserve-list pin authenticated; modified accounting refused. Production reserve counts/nonempty streams remain untested. |
| `source_seal.binding:81`, `check_binding:91` | PASS and negative test PASS | Wrong tree/config binding refused. |
| `s1_admission.admit:180–235`, full `run.prepare/prepared`, `b/d.effective` | Not completed | Missing parent pose/model/init assets, pointing/VQA/legacy databases and production rows prevent full preparation, faithful coverage, seals and effective-config equality. Round-6 parent refusal remains applicable. |
| RGB audit, CPU first batch, GPU first-step and optimizer preparation | Not run | Real frame/model assets, allocation, CUDA, process groups, FSDP, optimizer, resume/output binding and finite-loss checks remain required. The milestone gate is disabled and unreachable before stop 200. |

`evidence/fix7_admission/latest.json` links the exact executed results, exceptions and trace lines. Fixture failures above are tested guards, not findings that the production population necessarily fails them.

**Deriver contract and tests**

`tools/derive_kit_h1.py:581` / `payload/d.py:581` require a new selection pin to be accompanied by top-level `selection_equality: {{path, sha256}}` **and the identical pin** in `add_k["selection_equality.json"]`. The report is copied into the derived kit and sealed by its manifest. The validator recomputes candidate content and implementation digests, checks the archived code member hashes, and binds the report to the exact candidate, D0 reference, raw reference, tool hash, tree, every top-level field, ordered-index checks and complete input size inventory. It rejects missing, mismatched, negative or incomplete reports before source-kit IO. A historical D0 pin can remain only in a BLOCKED H1 artifact; READY and PREPARATION_ONLY refuse it. A report pin is an integrity binding, not independent proof of execution; independent review must inspect the regeneration outputs and provenance.

`tests/test_fix7_deriver.py` passes 19 checks, including both report acceptance and refusal, stale READY/PREPARATION_ONLY refusals, changed content, tampered report SHA, wrong tree/tool/reference, missing fields/indices/inputs, and a complete fixture derivation that seals both new pins. That integration test substitutes only the retained fixture's source-manifest authority and uses visibly TEST_ONLY evidence. It remains FIXTURE; it is not a production derivation. `tests/test_fix7_selection.py` exercises native regeneration, exact equality, changed counters, reordered arrays, missing keys and type distinctions. `tests/test_fix7_admission.py` completes the native synthetic routing audit. `tests/test_fix7_package.py` validates the opaque bootstrap, corrupt payload refusal, visible names, upload integrity and seven guarded-patch cases. Existing `test_gate_binding.py` passes. No distributed/GPU test ran.

**Operator steps**

Follow **regenerate → verify → re-derive → patch → o.sh → g.sh → review.json → z.sh derive → certify → go.json → s.sh**. These are future operator steps, not commands executed in this local task.

1. Regenerate: carry the exact `build/q.sh` body through the authorized opaque transport and verify its SHA256 below. On the Orchard login node, use the stated PY_GATE and approved BW_GATE. It reads the sealed kit and existing trainer archive; it does not submit a job. Inspect private `o/q.json` and native.log if it refuses. Missing inputs or DIFFERENT content stop this sequence.
2. Verify: require exit 0, status EQUAL, empty raw/final differences, all fields/indices equal, exact code/tree/tool hashes and SHA256 of `o/r.json` equal to q.json's selection_sha256. Rehash q.json and pin that value. Review raw outputs and the D0 direct-to-VQA policy. A hash-only relabel or test-only equality report is unacceptable.
3. Re-derive: create a new `pool_selection_<sha-prefix>.json` add_k entry pointing to the generated r.json. Replace the old aa128e6f add_k entry and the selection pin, add its logical catalog mapping, and remove the superseded f232d416 catalog mapping added by the D0 override (retain **every mapping from the sealed base catalog**). Add the exact report pin to both selection_equality and add_k/selection_equality.json. Run `validate_selection_equality(over)` with the shipped deriver before deriving. Recompute 4.json's conditional identity, PENDING review/staging pins, ids.json/config key and the native contract; use fresh unused kit and persistent-root targets. Then call `d.py SEALED_KIT FRESH_OUTPUT OVERRIDE_JSON` with BLOCKED status and verify source/dependency closure and native CPU validation. The actual new identity cannot be calculated here without the generated selection. Never promote a fixture or copy the audit's TEST_ONLY files.
4. Patch: rebuild the exact small patch and transport/sums against the live bundle after those bindings are known; retain replaced bytes and retire old identity-bound evidence. The current `build/c_patch.sh` is a tested **blocked inspection patch against the retained round-5 bundle** (backup v_6). It includes the disk-plan correction and hardened deriver, but still carries the old selection. It is not the final equality-bound deployment patch and refuses another starting state. No final production patch can be sealed before regeneration. Keep old KH/root/evidence intact.
5. Run `o.sh` to derive p, reproduce the sealed base e and authenticate staging/archive records. Its exact sealed source includes two large members absent from this workspace; complete source reproduction is an Orchard check.
6. Run `g.sh` with the approved CPU interpreter and bubblewrap. Its real faithful-camera gate must pass; a synthetic audit does not replace it.
7. Obtain a fresh independent `review.json` for the regenerated identity, contract and code. Then run `z.sh derive`; read the resulting key from compare.json, since the real review pin changes the config filename.
8. Inspect the final kit plus external records, write the actual CLEAN anon.json and run `z.sh certify`. Neither an old certificate nor this local audit certifies the new kit.
9. Verify the 44 unchanged export-session names, unused state and expiry. Bind a fresh separate go.json to the final identity, contract, wrapper hash and kit manifest. Only then run s.sh. The conditional 4.json and equality report grant no submission approval.

**Current blocked artifacts**

| Artifact | SHA256 / value |
|---|---|
| Config identity | `{ids['identity']}` (unchanged; still binds stale selection) |
| Contract | `{ids['contract']}` |
| Config key / run / proposed kit / root | `{ids['config_key']}` / `17c4ffa4` / `x_3fdda0fb` / `r/39504485` |
| Trainer archive | `{sha('payload/'+ids['trainer']['file'])}` (unchanged) |
| Regeneration script build/q.sh | `{sha('build/q.sh')}` |
| Regeneration Python | `{sha('tools/selection_check.py')}` |
| Deriver payload/d.py | `{sha('payload/d.py')}` |
| payload/sums.txt | `{sha('payload/sums.txt')}` |
| Blocked inspection patch | `{sha('build/c_patch.sh')}` ({(H/'build/c_patch.sh').stat().st_size:,} bytes) |
| Upload build/{up['archive']} | `{up['sha256']}` |

`SHA256SUMS.txt` seals the current deliverables; `evidence/fix7_selection/delivery.json` records their hashes. The regeneration script is a separate small artifact and contains no generated selection. No trainer re-upload is needed. No SSH, network, Orchard, GPU, Git, deletion, external-root search or write outside this workspace occurred.

Inherited visible logical roots in q.sh match those in g.sh. The sealed runtime still retains its original cache prefix/base-model name in `build/fx/b/c.sh:11–13,102`; the required `a15_cot_ap` job-name prefix remains unchanged. New script/output names are opaque and private.
'''
(H/'REPORT.md').write_text(report)
fix=f'''Selection semantics are unchanged by the seven H1 closure changes; production equality is still BLOCKED by 13 missing local gzip files (95,354,406 bytes).
Entry: build/tree/student_pilot/s1_pool.py:268 -> prepare:125; implementation:93 uses the static local import closure in p3_provenance.py:58, including nested imports.
Policy: tools/selection_check.py:58 exactly reproduces D0's direct-to-VQA projection (92,607 -> 83,184); raw and projected content must both match.
Changed functions: carrier_c1.py:506; carrier_c1_routing.py:442,477; carrier_c1_run.py:448,645,659; h1.py:18; h1_faithful.py:83,197; h1_r0.py:105; materialize.py:494 (all under build/tree).
None executes in pool selection; reserve filtering can change downstream training membership. Full hashes and definition diffs: evidence/fix7_selection/changes.json.
Tool: tools/selection_check.py:112 invokes native prepare and compares every content field plus ordered index bytes; only implementation is excepted, never relabeled.
Inputs: all pins/paths/sizes in evidence/fix7_selection/INPUTS.md; Orchard x_07ca49df k/ and u/eb3429c5 per catalog; 25 pin occurrences have local bytes, 13 gzip files do not.
Login package: build/q.sh, {(H/'build/q.sh').stat().st_size} bytes; private opaque names, self-checking payload/archive, bwrap logical roots, offline network namespace, nice 19, CPU PY_GATE.
Local tool: exit 2 / BLOCKED; no production replacement emitted. Native synthetic equality and changed-content refusal PASS.
| Audit past 215 | Result | Limit |
|---|---|---|
| Test-only copied selection, native build through 219 | REFUSED missing r16 receipt | Relocation/model descriptor supplied only for this isolated audit |
| Native synthetic s1_routing.build through 456 | PASS, 2 rows | Empty legacy DB, character processor, no RGB byte reads |
| Scene blocker/division/count/suffix budget | Refusals reproduced | Production populations untested |
| Census totals/source seal/reserve prepare+recheck | PASS; corruption refused | Synthetic rows, actual reserve pin |
| Faithful preparation gate | Refuses zero camera rows | Real >=95% identity gate untested |
| Full preparation/effective/RGB/CPU-first-batch/GPU checks | NOT RUN | Missing production models/streams/frames; detailed list in REPORT.md |
Deriver: tools/derive_kit_h1.py:581,639 and payload/d.py require matching candidate + SHA-pinned report, store report in add_k, reject stale READY/PREPARATION_ONLY.
Tests: 19 deriver checks including full FIXTURE derivation; native equality/mutation, routing audit, package/bootstrap/7 patch cases and existing gate binding PASS. No production proof manufactured.
Operator: regenerate -> verify -> re-derive -> patch -> o.sh -> g.sh -> review.json -> z.sh derive -> certify -> go.json -> s.sh; current patch is blocked inspection only.
q.sh SHA256 {sha('build/q.sh')}; deriver SHA256 {sha('payload/d.py')}.
Tool SHA256 {sha('tools/selection_check.py')}; payload sums SHA256 {sha('payload/sums.txt')}.
Patch SHA256 {sha('build/c_patch.sh')}; upload SHA256 {up['sha256']}.
Identity remains {ids['identity']}; final selection identity and final deployment patch await production equality. Exact delivery hashes: evidence/fix7_selection/delivery.json.
Scope: trinity-1-3, local CPU only; no SSH/network/Orchard/GPU/Git/deletion or external-root search. TEST_ONLY evidence never ships.
'''
assert len(fix.splitlines())<=25
(H/'FIX7.md').write_text(fix)
diff=f'''The packet adds a native selection regeneration tool and rejects new selection pins without their equality reports. The trainer, production selection, recipe and config identity remain unchanged; this packet is BLOCKED until production regeneration succeeds.

- `tools/selection_check.py` and `build/q.sh` regenerate from authenticated catalog inputs, compare raw and D0-projected receipts, and verify ordered index files. The standalone script is offline and below 1 MB.
- `tools/selection_guard.py`, `tools/make_deriver.py`, `tools/derive_kit_h1.py` and `payload/d.py` bind the candidate, reference, code, tool, input inventory and report. The generator uses the retained local base in evidence/fix7_before, so rebuilding needs no external source checkout.
- `tests/test_fix7_selection.py`, `tests/test_fix7_deriver.py`, `tests/test_fix7_admission.py` and `tests/test_fix7_package.py` cover regeneration, missing/invalid proofs, the complete fixture deriver, downstream native routing and transport integrity.
- `REPORT.md` and `FIX7.md` state the production blocker, exact inputs, downstream limits and operator sequence. `evidence/fix7_selection/` and `evidence/fix7_admission/` retain all audit output, including failed fixture-development attempts.
- `payload/sums.txt`, `UPLOAD.json`, transport scripts and build/c_patch.sh bind the hardened deriver. The patch remains a blocked inspection patch for the recorded live round-5 state; it is not an equality-bound deployment patch.

Current changed-member hashes are in evidence/fix7_patch_manifest.json. Full deliverable hashes are in evidence/fix7_selection/delivery.json and SHA256SUMS.txt. The original round-6 report and deriver are retained in evidence/fix7_before.
'''
(H/'DIFF.md').write_text(diff)
print('FIX7 lines',len(fix.splitlines()))
