from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix'
def read(p):return json.loads((B/p).read_text())
seal=json.loads((L/'out/TREE_SEAL.json').read_text());delivery=read('DELIVERY.json');kits=read('KIT_RESULT.json')
coverage=read('CHANGED_COVERAGE.json');gaps=read('GAPS.json')
tree=read('proofs/suite_tree/results.json');base=read('proofs/suite_base/results.json')
r2=read('proofs/suite_tree/r2_final/results.json')
comparison=read('SUITE_COMPARISON.json')
packet=read('proofs/packet/results.json');changes=read('DIFF_VS_BUILD9FIX.json')
inference=read('proofs/audit/INFERENCE_COMPONENTS.json')
text=read('proofs/text/RESULT.json')
out=['# Build n1fix', '',
     'The source and unsubmitted kits implement the review fixes. GO remains false. Production P exports, production frame-host staging, GPU parity and product inference acceptance were not checked.', '',
     'Every relative evidence path below is rooted at `'+str(L)+'`. The comparison base is `work/base/tree_b01ce449`.', '',
     '| Finding | Status | Evidence |','|---|---|---|',
     '| N1 | Closed for the sealed-format CPU fixture; real handover awaits P run bytes and a declared mapping where identities differ | `work/n1fix/proofs/suite_tree/r2/results.json`, `work/n1fix/proofs/edge_final/n1fix/handover/RESULT.json`, `work/tree_r1/student_pilot/r1_handover.py` |',
     '| N2 | Closed; the absent-scene, own-probability and room-frame mutants are caught | `work/n1fix/proofs/mutations/RESULT.json` |',
     '| N3 | Closed; the text gate and independent reader reject the specified invisible separators | `work/tree_r1/tests/test_r2_n1fix.py`, `work/n1fix/proofs/suite_tree/r2/results.json` |',
     '| N4 | Closed; the R1 reader applies the R0 reservation without b7_inputs | `work/tree_r1/student_pilot/carrier_c1_run.py:1105`, `work/n1fix/proofs/suite_tree/r2/results.json` |',
     '| N5 | Closed for input assertions; production host proof remains unavailable | `work/tree_r1/launch_r1/entry.py`, `work/n1fix/proofs/kit_scope/RESULT.json`, `work/n1fix/proofs/suite_tree/r2/results.json` |', '',
     '## Artifacts', '',
     '- Tree seal: `'+seal['tree_sha256']+'` (`out/TREE_SEAL.json`).',
     '- Package: `'+delivery['path']+'`; SHA256 `'+delivery['sha256']+'`; '+str(delivery['bytes'])+' bytes, gzip-compressed tar (`work/n1fix/DELIVERY.json`).',
     '- Source comparison and inventory: `out/TREE.diff`, `out/TREE_FILES.sha256`.', '',
     '| Kit | SHA256 | Evidence |','|---|---|---|']
for name,value in kits.items():out.append('| '+name+' | `'+value['kit_sha256']+'` | `work/n1fix/KIT_RESULT.json` |')
out += ['', 'Each kit was built from an empty directory, scanned and verified by its native builder. The packaged source and kits are checked in `work/n1fix/proofs/package/ARCHIVE.json` and `work/n1fix/proofs/package/KIT_TESTS.json`.', '',
        '## What P records and what continuation derives', '',
        'The sealed export writes artifact schema, absolute step, config identity, source metadata when configured, and pins for the LM manifest and heads. It writes no sampler progress. The sealed preparation writes the config identity, stream receipt/database pins, post-filter counts and optional index-file pins, plus the recipe. The run writes binding.json and attempt records; metrics contain step-indexed rank records. Checkpoints write complete.json with the binding, step, shard and RNG pins. Config snapshots and checkpoint-embedded configs are conditional on the geometry-online path; they are not universal outputs (`work/base/tree_b01ce449/student_pilot/carrier_c1_run.py:598`, `:1773`, `:1896`, `:1959`, `:2325`, `:2810`).', '',
        'N requires SHA-pinned P config, binding and preparation files. It checks the config against the identity in P’s export, follows P’s config-pinned stream receipts to derive store hashes, and verifies the preparation against the run binding. The row-plan identity hashes P’s counts in stream order, index-file hashes, mode, mix, world size, offset and the sealed sampler’s fixed seed. The native sampler replays the consumed prefix to derive per-stream positions and the next-plan hash. Missing records produce named file blockers; unsupported sampler variants refuse (`work/tree_r1/student_pilot/r1_handover.py`).', '',
        'Differences between P and N require a SHA-bound handover_mapping in N’s config. The mapping must bind the export SHA, absolute step, complete derived source identity and complete target identity. It does not supply sampler positions. The LR schedule must still match, and replayed positions must equal N’s required absolute positions. Operator continuation_receipt and inline r1_progress values cannot establish admission (`work/tree_r1/student_pilot/r1_training.py:101`, `work/tree_r1/student_pilot/r1_handover.py`).', '',
        'The CPU fixture invokes the base tree’s own export and bind_output functions and the native artifact reader. It admits at step 200, resumes at step 201 and checks the LR against a separately written cosine formula. The existing full-plan/resumed-plan comparison checks N’s row-plan offset. The SHA-pinned step-544 parent still starts the new schedule at step 0 (`work/tree_r1/tests/test_r2_n1fix.py`, `work/tree_r1/tests/test_r2_build_n1.py`, `work/n1fix/proofs/suite_tree/r2/results.json`). The supported sampler body matches the base AST, and independently executing the base function reproduces the current plans (`work/n1fix/proofs/prepared_guards/SAMPLER_IDENTITY.json`).', '',
        'The export proof substitutes a seeded tiny native model for pretrained GPU weights and local rank/barrier/FSDP publication for distributed GPU collectives. P’s run metadata is synthetic. The RGB proof runs the real producer, intake, SQLite reader, RGB loader, routing encode, forward and backward; its pretrained/GPU boundary uses tiny native weights and a lossless tokenizer/processor, with synthetic RGB. Neither proof certifies deployed pretrained towers or product inference (`work/n1fix/proofs/edge_final/n1fix/handover/RESULT.json`, `work/n1fix/proofs/forward/RESULT.json`).', '',
        '## Mutation and preservation evidence', '',
        'M09, M12 and M07 each pass on clean code and fail under their reviewed mutation, without mutant-run errors. M01 remains equivalent on the reviewed real rows and is unchanged (`work/n1fix/proofs/mutations/RESULT.json`, `work/n1fix/proofs/review_inputs/REVIEW_VERDICT_TREE_N1.md`).', '',
        '| Original family | Text | Reader | Intake | Evidence |','|---|---:|---:|---:|---|']
for name,row in text['families'].items():
    c=row.get('counts',row)
    out.append('| '+name+' | '+str(c['text'])+' | '+str(c['reader'])+' | '+str(c['intake'])+' | `work/n1fix/proofs/text/RESULT.json` |')
out += ['', 'The repaired-family intake counts remain the reviewed 777, 1,476 and 8,067 for recovery, distance and units. These are inherited full-family results, not a new full-store census. The extent receipt and repaired-source admission logic are unchanged (`work/n1fix/inherited/proofs/extent_admission/RESULT.json`, `work/n1fix/proofs/review_inputs/REVIEW_VERDICT_TREE_N1.md`, `work/n1fix/DIFF_VS_BUILD9FIX.json`).', '',
        'The division and exclusion list retain their pinned bytes. The list has 601 keys; the independent review reports 203,812 admitted VQA rows and zero R0 hits among 204,413 input rows. This build does not rerun the full-store scan (`work/n1fix/inherited/proofs/division/RESULT.json`, `work/n1fix/proofs/review_inputs/F6.json`, `work/n1fix/proofs/review_inputs/R0_V7.json`).', '',
        'Text-only real-row checks use unavailable-RGB metadata pins and GUESS 24 FPS when source metadata lacks a frame rate. They do not claim frame or head execution (`work/n1fix/proof_text.py`).', '',
        'The host gate requires a fresh directory under the job’s temporary namespace, confines declared input paths to it, sets temporary/cache roots there and refuses namespace reuse. The local unit test simulates the namespace under this workspace; production /tmp isolation and complete staging were not exercised. Runtime binaries remain explicit resolved-and-hashed system dependencies (`work/tree_r1/launch_r1/entry.py`, `work/tree_r1/tests/test_r2_n1fix.py`).', '',
        '## Qualification', '',
        'Packet suite: '+str(len(packet))+' tests, '+str(sum(v.get('outcome')=='passed' for v in packet.values()))+' passed (`work/n1fix/proofs/packet/results.json`).', '',
        'Final frozen R2 group: '+str(r2['tests'])+' executions, '+str(len(r2['failures']))+' failures and '+str(len(r2['errors']))+' errors (`work/n1fix/proofs/suite_tree/r2_final/results.json`).', '',
        '| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |',
        '|---|---:|---:|---:|---:|---:|---|']
for name,value in [('tree',tree),('base',base)]:
    out.append('| '+name+' | '+' | '.join(str(x) for x in (value['tests'],len(value['passed']),len(value['failures']),len(value['errors']),len(value['skips'])))+' | `work/n1fix/proofs/suite_'+name+'/results.json` |')
out += ['', 'Failure and error counts include subtests and setup/import errors, so these events do not sum to the execution count (`work/n1fix/SUITE_COMPARISON.json`). The base groups are reused only after exact source and fixture inventories match and the runner differs solely in its local harness path. Changed tree groups ran from the frozen archive (`work/n1fix/proofs/suite_base/RESUME_RECEIPT.json`, `work/n1fix/proofs/suite_tree/*/GROUP_RECEIPT.json`).', '',
        'Regression events: '+str(comparison['regressions'])+'; R2 failure events: '+str(comparison['r2_failures'])+'; regressions beyond BF16 parity: '+str(sum(not r['preexisting'] and 'BF16' not in r['cause'] for r in comparison['failures']))+' (`work/n1fix/SUITE_COMPARISON.json`).', '',
        '| Changed-statement coverage class | Statements | Evidence |','|---|---:|---|']
for name,count in coverage['classes'].items():out.append('| '+name+' | '+str(count)+' | `work/n1fix/CHANGED_COVERAGE.json` |')
out += ['', 'CPU gaps: '+str(len(gaps))+' (`work/n1fix/GAPS.json`). Coverage measures changed Python statement heads against the base; it excludes the tree’s tests/ directory, docstrings and non-Python assets. Standard-library monitoring requires compiled-code fingerprints and exact source hashes. Inherited observations require an exact current-file hash; GPU, frame-host and model-loader classifications do not count as execution (`work/n1fix/coverage.py`, `work/n1fix/coverage_current.py`).', '',
        '## Diff against build 9fix', '',
        'Build 10 must take these source changes from this workspace. No file in its workspace was touched (`work/n1fix/DIFF_VS_BUILD9FIX.json`).', '']
out += ['- `'+r['file']+'`' for r in changes]
out += ['', '## Product inference outside the weights', '',
        'No answer selector, rule table, guard or fallback was added to product inference. The following known components remain outside registered weights or forward execution. The conservative static import inventory also contains support and training imports; dynamic dispatch and external dependencies remain unproven (`work/n1fix/proofs/audit/INFERENCE_COMPONENTS.json`).', '',
        '| Component | Source under work/tree_r1 | Operation |','|---|---|---|']
for row in inference['known_outside_forward']:out.append('| `'+row['component']+'` | `'+row['file']+':'+str(row['line'])+'` | '+row['operation']+' |')
out += ['', '## For the confirmation review', '',
        '- Reproduce the sealed-format export proof and reject the forged receipt. Inspect config-to-export binding, source receipt hashes, deterministic replay, the explicit mapping and the independent LR assertion.',
        '- Review a real P export with its config, binding and preparation before admitting a handover. No production P bytes were available here.',
        '- Recheck the invisible-status, R0 reader and fresh-temporary-namespace refusals. Verify the production staging flow in its actual job namespace before accepting the host assertion.',
        '- Check the mutation receipts, frozen suite comparison, coverage classifications and package/source hashes. Review any CPU gap listed in GAPS.json.',
        '- Carry the preserved F1–F6 evidence and the orchestrator’s distance-cell ruling. This build does not change the mix or rerun complete-store preparation.',
        '- Have the acceptance lane establish the deployed inference closure. GPU parity, production model/frame-host preparation and product inference acceptance remain unchecked. BF16 enablement remains refused after the recorded CPU parity failure (`work/n1fix/SUITE_COMPARISON.json`).', '',
        'No launch, remote service call, GPU execution or write outside this workspace occurred.', '']
report='\n'.join(out).replace('proofs/edge_final/n1fix/handover/RESULT.json','proofs/suite_tree/r2_final/n1fix/handover/RESULT.json').replace('proofs/suite_tree/r2/results.json','proofs/suite_tree/r2_final/results.json')
report=report.replace('The host gate requires a fresh directory', 'The kit entry rejects roots outside /tmp before creating files and creates a fresh input namespace with create_job_tmp. The host gate accepts its process-local, one-use token, which binds the directory device and inode. It requires a fresh directory')
(L/'out/BUILD_N1FIX_REPORT.md').write_text(report)
record=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
current=record.read_text();heading='\n## Build n1fix\n'
section='\nThe sealed source implements donor-byte continuation checks, the reviewed refusal tests, invisible-status detection, R0 reader reservation and fresh temporary-namespace assertions. Kits remain GO=false. The artifact identity, suite outcomes, coverage and production limitations are recorded in `BUILD_N1FIX_REPORT.md` and `work/n1fix/DELIVERY.json`.\n'
if heading not in current:record.write_text(current+heading+section)
(B/'STATUS.md').write_text('# Build n1fix status\n\nSource, GO=false kits, package and report are delivered. See ../../out/BUILD_N1FIX_REPORT.md. Production handover, frame-host execution and product inference acceptance remain unqualified. CPU gaps: '+str(len(gaps))+' (GAPS.json).\n')
print(str(L/'out/BUILD_N1FIX_REPORT.md'))
