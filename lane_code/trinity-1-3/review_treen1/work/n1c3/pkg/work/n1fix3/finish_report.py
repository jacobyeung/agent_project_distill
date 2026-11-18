from pathlib import Path
import hashlib,json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';P=B/'proofs'
def read(name):return json.loads((B/name).read_text())
seal=json.loads((L/'out/TREE_SEAL.json').read_text());delivery=read('DELIVERY.json')
comparison=read('SUITE_COMPARISON.json');coverage=read('CHANGED_COVERAGE.json');gaps=read('GAPS.json')
assert not gaps,gaps
assert comparison['r2_failures']==0 and comparison['fatal'] is None
regressions=[r for r in comparison['failures'] if not r['preexisting']]
assert all('bf16' in (r['test']+r['tree_error']).lower() or 'bfloat16' in r['tree_error'].lower() for r in regressions),regressions
packet=read('proofs/packet/results.json');assert all(v['outcome']=='passed' for v in packet.values())
mutants=read('proofs/mutations/RESULT.json')['results']
assert len(mutants)==19 and all(r['clean_pass'] and (r['caught'] or r['equivalent']) for r in mutants)
text=read('proofs/text/RESULT.json')['families'];review=read('proofs/review_inputs/F1_prod.json')
for name,row in text.items():assert row['counts']==review[name]['counts'],name
assert not any(v['changed_rows'] for v in read('proofs/row_delta/RESULT.json')['families'].values())
kits=read('KIT_RESULT.json');diff=read('DIFF_VS_N1FIX2.json');inference=read('proofs/audit/INFERENCE_COMPONENTS.json')
tree=read('proofs/suite_tree/results.json');base=read('proofs/suite_base/results.json')
assert delivery['tree_seal']==seal['tree_sha256']
def storage(root):
    total=0;pending=[root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if entry.is_symlink():continue
                if entry.is_dir(follow_symlinks=False):pending.append(entry.path)
                elif entry.is_file(follow_symlinks=False):total+=entry.stat().st_size
    return total
usage=dict(workspace_bytes=storage(L),temporary_bytes=storage(L/'work/tmp'),measured_before_report_write=True)
assert usage['workspace_bytes']<=8*1024**3 and usage['temporary_bytes']<=200_000_000
(B/'FINAL_INTEGRITY.json').write_text(json.dumps(usage,indent=2))
lines=['# Build n1fix3','',
'The P-to-N initialization gap is closed in the source and CPU proofs. The sealed producer still lacks an authenticated checkpoint-completion anchor. All kits have GO=false; no job was submitted.',
'',f'All evidence paths are relative to `{L}`.','',
'| Requested item | Status | Evidence |','|---|---|---|',
'| 1. Effective optimizer groups and initialization | Closed: mismatched depth initialization, inherited head initialization and unverifiable initializer bytes refuse before mapping. Native grouping records names, tensor and scalar counts, initial rates, weight decay and frozen modules. | `work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix3/proofs/suite_tree/r2/results.json`; native group tables under `work/n1fix3/proofs/suite_tree/r2/n1fix/` |',
'| 2. Surviving mutations | Closed: the required non-equivalent mutations are caught by passing clean tests. | `work/n1fix3/proofs/mutations/RESULT.json` |',
'| 3. Completion anchor | Blocked by sealed producer bytes: an operator can forge both binding and complete.json. P must publish a trusted hash-bound handover receipt or include the completion pin in its authenticated export. | `work/n1fix3/proofs/checkpoint_limit/RESULT.json`; `work/n1fix3/proofs/review_inputs/N1.json` |',
'| 3. Unicode variants and room count | Closed: the specified extra variants refuse in both independent checks, with unchanged original-slice verdicts. The room reader count is zero. | `work/n1fix3/proofs/suite_tree/r2/results.json`; `work/n1fix3/proofs/row_delta/RESULT.json`; `work/n1fix3/proofs/text/RESULT.json` |','',
'## Handover behavior','',
'The early contract compares exact depth initializer pins, including paths, and reads head_init from each hash-verified initialization artifact. Missing initializer bytes refuse with P_EXPORT_HEAD_INIT_UNVERIFIED. Initialization mismatches refuse with named P_EXPORT_LR_SCHEDULE_MISMATCH reasons. The mapping cannot override these checks. Equivalent depth pins at different paths conservatively refuse; the default is recorded in DECISIONS.md (`work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix3/DECISIONS.md`).',
'',
'Before optimizer creation, the training hook calls the native parameter_groups builder for each config and records every member name and count, rate, decay, frozen parameter and frozen module. It reuses the loaded topology only after initialization controls match. The native inherited-head helper supplies the same membership rule used by initialization. The CPU proof independently runs the untouched base group builder and real depth/head initialization functions to measure the two reported differences (`work/n1fix3/proofs/audit/OPTIMIZER_INPUTS.json`; native TABLES.json files under `work/n1fix3/proofs/suite_tree/r2/n1fix/`).',
'',
'The matching fixture admits the export at step 200; the pinned 1d6eeb28 parent at step 544 still starts a new schedule at step 0. The tiny producer fixture has no Stage-1 initialization on either side; a separate test supplies the mismatched N initializer. Production P configuration and weights were unavailable (`work/n1fix3/proofs/suite_tree/r2/results.json`; `work/tree_r1/tests/test_r2_n1fix.py`; `work/tree_r1/tests/test_r2_n1fix3.py`).',
'',
'P must write handover.json with the export artifact, complete.json, checkpoint shard, config and preparation hashes, and publish that receipt through a trusted run record. Hashes contained only inside an operator-supplied completion file cannot authenticate that same file. This build preserves the sealed format and makes no stronger authenticity claim (`work/n1fix3/proofs/checkpoint_limit/RESULT.json`).',
'',
'## CPU proof and preservation','',
'The producer proofs run the base export, bind_output and checkpoint functions and the native readers. Tiny native CPU weights replace pretrained GPU weights; local rank, barrier, gather and FSDP publication stand in for distributed GPU collectives. Config preparation and step labels are synthetic. The RGB proof runs the real materializer, intake, SQLite reader, RGB loader, encoder, forward and backward with synthetic RGB and a tiny native model and tokenizer at the pretrained boundary (`work/n1fix3/proofs/checkpoint/RESULT.json`; `work/n1fix3/proofs/forward/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix3.py`).',
'',
'Separate refusal tests use malformed synthetic metadata, a native CPU rehearsal source receipt, a temporary namespace override and an injected late-file race. The table-mismatch unit case injects unequal tables to exercise its refusal. These cases make no forward-pass claim (`work/n1fix3/proofs/contract_closure/RESULT.json`; `work/n1fix3/proofs/prepared_guards/RESULT.json`; `work/n1fix3/proofs/faults/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix3.py`).',
'',
'| Original family | Text | Reader | Intake | Evidence |','|---|---:|---:|---:|---|']
for name,row in text.items():
    c=row['counts'];lines.append(f"| {name} | {c['text']} | {c['reader']} | {c['intake']} | `work/n1fix3/proofs/text/RESULT.json` |")
lines+=['','The repaired-family intake counts remain inherited full-family evidence; they were not recounted as complete stores. The exclusion list and scene gate retain their bytes. The admitted VQA count remains inherited reviewer evidence (`work/n1fix3/proofs/review_inputs/F1_prod.json`; `work/n1fix3/proofs/audit/F6_PRESERVATION.json`; `work/n1fix3/proofs/review_inputs/F6_routing.json`).',
'','Text-only proofs use unavailable-RGB metadata and GUESS 24 FPS where metadata is absent. These proofs do not claim real RGB or head execution (`work/n1fix3/proof_text.py`).',
'','## Mutation results','','| Mutant | Clean | Mutant | Evidence |','|---|---|---|---|']
for r in mutants:lines.append(f"| {r['mutant']} | PASS | {'CAUGHT' if r['caught'] else 'Equivalent; survives'} | `work/n1fix3/proofs/mutations/RESULT.json` |")
lines+=['','M01 is equivalent for the authenticated response path; X13 substitutes a declared value already checked for equality. Neither survivor provides a new admission path (`work/n1fix3/proofs/mutations/RESULT.json`; `work/n1fix3/proofs/review_inputs/MUTANTS.json`).',
'','## Qualification','',f"Packet suite: {len(packet)} passed (`work/n1fix3/proofs/packet/results.json`).",'',
'| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |','|---|---:|---:|---:|---:|---:|---|']
for name,v in [('tree',tree),('base',base)]:lines.append(f"| {name} | {v['tests']} | {len(v['passed'])} | {len(v['failures'])} | {len(v['errors'])} | {len(v['skips'])} | `work/n1fix3/proofs/suite_{name}/results.json` |")
lines += ['',f"Regression events: {len(regressions)}; regressions beyond BF16 parity: 0; R2 failure events: 0. Failure/error events include subtests and setup failures (`work/n1fix3/SUITE_COMPARISON.json`).",'',
'The frozen package supplied the tree groups. Base groups resumed only after exact source, fixture and runner-equivalence checks. The receipts bind those inputs; unchanged groups were not rerun (`work/n1fix3/proofs/suite_base/RESUME_RECEIPT.json`; `work/n1fix3/proofs/suite_tree/*/GROUP_RECEIPT.json`).','',
'| Changed-statement class | Statements | Evidence |','|---|---:|---|']
for name,count in coverage['classes'].items():lines.append(f'| {name} | {count} | `work/n1fix3/CHANGED_COVERAGE.json` |')
lines+=['','CPU gaps: 0. Coverage spans changed Python statement heads against the untouched base, excluding tests, docstrings and non-Python assets. Standard-library monitoring requires matching compiled-code fingerprints and current-file hashes. Inherited observations require exact file hashes. GPU, frame-host and model-loader classes are limitations (`work/n1fix3/CHANGED_COVERAGE.json`; `work/n1fix3/GAPS.json`).','',
'## Artifacts','',f"Tree seal: `{seal['tree_sha256']}` (`out/TREE_SEAL.json`). Inventory and base diff: `out/TREE_FILES.sha256`, `out/TREE.diff`.",'',
f"Package: `{delivery['path']}`; SHA256 `{delivery['sha256']}`; {delivery['bytes']} bytes; gzip-compressed tar (`work/n1fix3/DELIVERY.json`).",'',
'| Kit | SHA256 | Evidence |','|---|---|---|']
for name,v in kits.items():lines.append(f"| {name} | `{v['kit_sha256']}` | `work/n1fix3/KIT_RESULT.json` |")
lines+=['','Every kit was staged from an empty root, scanned and verified. GO=false. The extracted kit and source hashes were verified against the frozen package (`work/n1fix3/proofs/package/KIT_TESTS.json`; `work/n1fix3/proofs/package/ARCHIVE.json`).','',
'## Diff against build n1fix2','',
'The merge must take the following source files. The complete hashes and original seal are in `work/n1fix3/DIFF_VS_N1FIX2.json`.','']
lines+=['- `'+r['file']+'`' for r in diff['changed_files']]
lines+=['','The harness, inputs and proof files under work/n1fix3 and the requested output artifacts also changed. No other workspace was written. The source-file comparison is retained because the merge explicitly requires it.','',
'## Product inference outside the weights','',
'The known inference components below retain their exact source bytes. This build adds only training/input checks and tests; it does not qualify the existing inference design. The conservative import inventory lists file:line locations for all local functions, methods and literal tables in that closure, including support and training code (`work/n1fix3/proofs/audit/INFERENCE_COMPONENTS.json`; `work/n1fix3/proofs/audit/INFERENCE_UNCHANGED.json`).','',
'| Component | File:line under work/tree_r1 | Operation |','|---|---|---|']
for row in inference['known_outside_forward']:lines.append(f"| `{row['component']}` | `{row['file']}:{row['line']}` | {row['operation']} |")
lines+=['','Dynamic dispatch, external dependencies and the actual deployed forward path were not checked. The acceptance lane must establish their completeness and compliance with the end-to-end requirement.','',
'## For the confirmation review','',
'- Replay both initialization mismatches and the missing initializer case; inspect the native group tables and the untouched-base grouping comparison.',
'- Confirm the matching continuation and pinned-parent start behavior, and the mutation assertions for extension settings, checkpoint step, format characters and interpreter version.',
'- Treat completion authentication as a producer requirement. Do not accept an operator-supplied completion pin as an independent trust anchor.',
'- Recompute the seal, package SHA and kit hashes; inspect frozen-group receipts, the base comparison and coverage classifications.',
'- Verify both Unicode checks independently and compare the bounded real-row counts, including the room reader column.',
'- Qualify real production P bytes, frame-host staging, GPU behavior and deployed inference separately. Full stores were not materialized; full repaired-family and VQA censuses were not rerun. BF16 parity remains unresolved.',
'',f"Before the report write, workspace usage was {usage['workspace_bytes']} bytes and temporary usage was {usage['temporary_bytes']} bytes (`work/n1fix3/FINAL_INTEGRITY.json`). Other workspaces were not inventoried.",
'','No launch, remote service, network, GPU, Git, SSH or subagent was used. All writes stayed inside this workspace.','']
report='\n'.join(lines);(L/'out/BUILD_N1FIX3_REPORT.md').write_text(report)
record=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
with record.open('a') as stream:stream.write('\n\n## Build n1fix3\n\n'+report.split('\n',2)[2])
(B/'STATUS.md').write_text('Build n1fix3 is complete for the requested CPU/source scope. Initialization mismatches refuse; required non-equivalent mutants are caught; CPU coverage gaps and non-BF16 regressions are zero. The sealed completion-authentication limit is documented. GO=false. Evidence: out/BUILD_N1FIX3_REPORT.md and work/n1fix3/SUITE_COMPARISON.json.\n')
print(json.dumps(dict(report='out/BUILD_N1FIX3_REPORT.md',seal=seal['tree_sha256'],package=delivery['path'])))
