"""Render the delivered behavior and its source-bound qualification evidence."""
from pathlib import Path
import json,hashlib,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1'
def read(p):return json.loads((L/p).read_text())
prefix='work/n1fix2/'
seal=read('out/TREE_SEAL.json');delivery=read(prefix+'DELIVERY.json');kits=read(prefix+'KIT_RESULT.json')
packet=read(prefix+'proofs/packet/results.json');comparison=read(prefix+'SUITE_COMPARISON.json')
coverage=read(prefix+'CHANGED_COVERAGE.json');gaps=read(prefix+'GAPS.json')
assert not gaps
assert all(v['outcome']=='passed' for v in packet.values())
assert comparison['r2_failures']==0
regressions=[r for r in comparison['failures'] if not r['preexisting']]
assert all('BF16' in r['cause'] for r in regressions),regressions
mutations=read(prefix+'proofs/mutations/RESULT.json')['results'];assert all(r['caught'] and not r['errors'] for r in mutations)
variants=read(prefix+'proofs/review_variants/RESULT.json');assert variants['refused_both']==111
changes=read(prefix+'DIFF_VS_BUILD9FIX.json')['files']
rows=read(prefix+'proofs/text/RESULT.json')['families'];delta=read(prefix+'proofs/row_delta/RESULT.json')
assert not any(r['changed_rows'] for r in delta['families'].values())
assert read(prefix+'proofs/package/ARCHIVE.json')['sha256']==delivery['sha256']
inference=read(prefix+'proofs/audit/INFERENCE_COMPONENTS.json')
integrity=read(prefix+'FINAL_INTEGRITY.json')
text=['# Build n1fix2\n',
'The confirmation findings are closed by the source and CPU proofs. All kits remain unsubmitted with GO=false. Production P bytes, production frame-host staging, GPU parity and product inference acceptance remain unchecked.\n',
'All relative evidence paths are rooted at `'+str(L)+'`.\n',
'| Finding | Status | Evidence |\n|---|---|---|',
'| N1a | Closed: effective optimizer settings and config scales must match before mapping | `work/tree_r1/student_pilot/r1_handover.py`; `'+prefix+'proofs/targeted/results.json`; `'+prefix+'proofs/audit/OPTIMIZER_INPUTS.json` |',
'| N1b | Closed: config contents and pinned stream receipts derive N’s target; forged declarations and matching forged mappings refuse | `work/tree_r1/student_pilot/r1_training.py`; `'+prefix+'proofs/targeted/results.json` |',
'| N1c | Closed: the native checkpoint producer binds preparation, the handover reader rejects the forgery, and continuation identity includes preparation | `work/tree_r1/student_pilot/r1_handover.py`; `'+prefix+'proofs/checkpoint/RESULT.json`; `'+prefix+'proofs/targeted/results.json` |',
'| H2/H6 | Closed: independent binding-config and artifact-config tests kill both mutations | `'+prefix+'proofs/mutations/RESULT.json` |',
'| N3 residual | Closed: gate and reader have separate normalization and patterns; every exact reviewer variant refuses | `'+prefix+'proofs/review_variants/RESULT.json`; `'+prefix+'proofs/row_delta/RESULT.json` |',
'| N5 residual | Closed for CPU input assertions: relative symlinks cannot escape; token-bound namespaces must be empty; kit states and enforces the interpreter minimum | `work/tree_r1/launch_r1/entry.py`; `work/tree_r1/launch_r1/build.py`; `'+prefix+'proofs/targeted/results.json`; `'+prefix+'proofs/faults/RESULT.json` |\n',
'## Handover contract\n',
'The optimizer comparison covers effective schedule steps, warmup, group rates and weight decay; config LM/pose scales; and complete MDG and geometry extension settings. Extension settings include LoRA rates, geometry ramps, alignment steps and GF1 rates. AdamW betas and LoRA decay are sealed constants. The audit identifies each config input and its base-source location (`'+prefix+'proofs/audit/OPTIMIZER_INPUTS.json`).\n',
'The native producer fixture admits P’s export at step 200 and resumes N at step 201. P scales absent or equal to 1.0 against N scales 0.6 refuse with a named LR mismatch. The pinned step-544 parent still starts at step 0 (`'+prefix+'proofs/targeted/results.json`; `work/tree_r1/tests/test_r2_n1fix2.py`; `work/tree_r1/tests/test_r2_build_n1.py`).\n',
'N hashes its config contents after excluding self-referential identity fields, mapping and host/review attestations. It also excludes derived preparation and authorization records, as the trainer does, so preparation cannot create a circular hash. It reads each SHA-verified stream receipt to derive database hashes. Declared identities must equal those derived values; a mapping cannot replace them (`work/tree_r1/student_pilot/r1_training.py`; `'+prefix+'proofs/target_prepared/RESULT.json`).\n',
'P must supply pinned config, binding, preparation and checkpoint complete.json bytes. The checkpoint schema and export step must match, and its embedded binding must equal the supplied binding. The binding authenticates the preparation. The legacy export hash remains compatible with P; the continuation identity additionally binds preparation. The checkpoint receipt is an input trust anchor, not an independent signature. No real P run was available (`work/tree_r1/student_pilot/r1_handover.py`; `'+prefix+'DECISIONS.md`).\n',
'The producer proofs call the base tree’s export, bind_output and checkpoint functions, then the native artifact and handover readers. Tiny seeded native weights stand in for pretrained GPU weights; local rank/barrier/broadcast/gather/FSDP publication stands in for distributed GPU collectives. Preparation metadata and the step label are synthetic. The checkpoint proof writes native shard/RNG pins and complete.json through the sealed producer. The separate RGB proof runs the real producer, intake, SQLite reader, RGB loader, routing encoder, forward and backward with synthetic RGB, tiny native weights and a lossless tokenizer/processor at the pretrained boundary (`'+prefix+'proofs/targeted/n1fix/handover/RESULT.json`; `'+prefix+'proofs/checkpoint/RESULT.json`; `'+prefix+'proofs/forward/RESULT.json`).\n',
'## Preservation and refusals\n',
'Both text checks refuse all 111 exact reviewer variants, including compatibility letters, the specified Cyrillic e and combining accent. The reader still refuses when the gate oracle and pattern table are disabled (`'+prefix+'proofs/review_variants/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix2.py`).\n',
'| Original family | Text | Reader | Intake | Evidence |\n|---|---:|---:|---:|---|']
for name,r in rows.items():
    c=r['counts'];text.append(f"| {name} | {c['text']} | {c['reader']} | {c['intake']} | `{prefix}proofs/text/RESULT.json` |")
text += ['\nNo row changed either text-admission verdict in the original slices (`'+prefix+'proofs/row_delta/RESULT.json`). Repaired-family intake counts 777, 1,476 and 8,067 are inherited full-family evidence; they are not a new full-store census (`'+prefix+'inherited/proofs/extent_admission/RESULT.json`; `'+prefix+'proofs/review_inputs/F1_prod.json`).\n',
'The exclusion list retains 601 keys and its exact pin. The admitted VQA count 203,812 is inherited from the independent full-store review. The list and division pins, original-family outcomes, current division refusal tests, and unchanged mix non-pin content are checked locally (`'+prefix+'proofs/audit/F6_PRESERVATION.json`; `'+prefix+'proofs/review_inputs/F6.json`; `'+prefix+'proofs/review_inputs/F6_routing.json`; `'+prefix+'proofs/gate_edges/RESULT.json`; `'+prefix+'proofs/audit/MIX_PRESERVATION.json`).\n',
'Text-only row proofs use unavailable-RGB metadata pins and GUESS 24 FPS when frame-rate metadata is absent. They do not claim RGB or head execution (`'+prefix+'proof_text.py`).\n',
'The host path check resolves relative paths against the job namespace, follows symlinks and refuses escapes. Token admission verifies device, inode, mode, single use and emptiness. The generated host script requires Python 3.12 or newer and checks the version before pathlib/tarfile operations. CPU namespace tests use workspace-local directories; they do not qualify production staging (`work/tree_r1/launch_r1/entry.py`; `work/tree_r1/launch_r1/build.py`; `'+prefix+'proofs/host_checks/RESULT.json`; `'+prefix+'proofs/faults/RESULT.json`).\n',
'## Mutation and suite results\n',
'| Mutant | Clean | Mutant | Evidence |\n|---|---|---|---|']
for r in mutations:text.append(f"| {r['mutant']} | PASS | CAUGHT | `{prefix}proofs/mutations/RESULT.json` |")
text += [f'\nPacket suite: {len(packet)} passed (`{prefix}proofs/packet/results.json`).\n',
'| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |\n|---|---:|---:|---:|---:|---:|---|']
for name in ('tree','base'):
    v=read(prefix+'proofs/suite_'+name+'/results.json')
    text.append(f"| {name} | {v['tests']} | {len(v['passed'])} | {len(v['failures'])} | {len(v['errors'])} | {len(v['skips'])} | `{prefix}proofs/suite_{name}/results.json` |")
text += [f'\nRegression events: {len(regressions)}; regressions beyond BF16 parity: 0; R2 failure events: {comparison["r2_failures"]}. Failure/error events include subtests and setup failures and do not sum to execution counts (`{prefix}SUITE_COMPARISON.json`).\n',
'Tree groups run from the frozen package when their source inventory changes. Base groups are resumed only after exact source, fixture and runner-equivalence checks. Group receipts bind the inputs; phase receipts bind the final source (`'+prefix+'proofs/suite_base/RESUME_RECEIPT.json`; `'+prefix+'proofs/suite_tree/*/GROUP_RECEIPT.json`; `'+prefix+'packet_RECEIPT.json`).\n',
'| Changed-statement coverage class | Statements | Evidence |\n|---|---:|---|']
for name,count in coverage['classes'].items():text.append(f'| {name} | {count} | `{prefix}CHANGED_COVERAGE.json` |')
text += ['\nCPU gaps: 0 (`'+prefix+'GAPS.json`). Coverage spans every changed Python statement head since the untouched base, excluding tests, docstrings and non-Python assets. Standard-library monitoring requires compiled-code fingerprints and exact current-file hashes. Inherited observations require matching file hashes. GPU, frame-host and model-loader classes are limitations, not execution claims (`'+prefix+'coverage.py`; `'+prefix+'coverage_current.py`).\n',
'## Artifacts\n',
f'Tree seal: `{seal["tree_sha256"]}` (`out/TREE_SEAL.json`). Source inventory and base diff: `out/TREE_FILES.sha256`, `out/TREE.diff`.\n',
f'Package: `{delivery["path"]}`; SHA256 `{delivery["sha256"]}`; {delivery["bytes"]} bytes, gzip-compressed tar (`{prefix}DELIVERY.json`).\n',
'| Kit | SHA256 | Evidence |\n|---|---|---|']
for name,r in kits.items():text.append(f'| {name} | `{r["kit_sha256"]}` | `{prefix}KIT_RESULT.json` |')
text += ['\nKits were built from empty roots, scanned and verified; GO remains false. Frozen copies are checked against the package source (`'+prefix+'proofs/package/KIT_TESTS.json`; `'+prefix+'proofs/package/ARCHIVE.json`).\n',
'## Diff against build 9fix\n',
'The following files differ from build-9fix seal `'+read(prefix+'DIFF_VS_BUILD9FIX.json')['build9fix_seal']+'`. The build-10 workspace was not touched (`'+prefix+'DIFF_VS_BUILD9FIX.json`).\n']
text += ['- `'+r['file']+'`' for r in changes]
text += ['\n## Product inference outside the weights\n',
'This build changes input admission and qualification only. The known inference components retain their exact source bytes (`'+prefix+'proofs/audit/INFERENCE_UNCHANGED.json`). The acceptance lane must judge their compatibility with the required end-to-end model.\n\nThe full conservative static import inventory is in `'+prefix+'proofs/audit/INFERENCE_COMPONENTS.json`; it also includes support/training functions. Dynamic dispatch and external dependencies remain unproven.\n',
'| Component | Source under work/tree_r1 | Operation |\n|---|---|---|']
for r in inference['known_outside_forward']:text.append(f'| `{r["component"]}` | `{r["file"]}:{r["line"]}` | {r["operation"]} |')
text += ['\n## For the confirmation review\n',
'- Check optimizer parity with absent and explicit donor scales, and reject the forged target declarations even when the mapping copies them. Inspect the base-source optimizer-input audit.\n',
'- Replay the forged preparation against the checkpoint binding. Require the actual P checkpoint, config, binding, preparation, receipt and index bytes before accepting a real handover.\n',
'- Verify the exact reviewer Unicode set in both admission checks, including reader independence, unchanged slice verdicts, relative-symlink refusal and nonempty-token refusal.\n',
'- Recompute the tree seal, package SHA and kit hashes; inspect mutation receipts, frozen group receipts, regression comparison and every coverage classification.\n',
'- Carry the existing mix and handover semantics. The mapping requirement, absolute N-plan offset and absence of optimizer state in P exports are unchanged.\n',
'- Qualify the actual production temporary namespace and staging closure, GPU behavior and deployed inference path separately. The full repaired-family and VQA censuses were not rerun. BF16 enablement remains refused.\n',
f'Workspace usage: {integrity["storage"]["workspace"]} bytes; temporary usage: {integrity["storage"]["tmp"]} bytes (`{prefix}FINAL_INTEGRITY.json`). Storage outside this workspace was not inventoried.\n',
'No launch, remote service call, network request, GPU execution, Git command or subagent was used. No file was written outside this workspace. The requested comparison section is retained because the merge build needs its file list.\n']
report='\n'.join(text)
(L/'out/BUILD_N1FIX2_REPORT.md').write_text(report)
design=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
section='\n\n## Build n1fix2\n\nThe build closes optimizer-scale, target-identity, preparation-authentication, Unicode and temporary-namespace findings. It preserves the mix and exclusions. The source seal is `'+seal['tree_sha256']+'` (`out/TREE_SEAL.json`). Kits remain GO=false. Qualification, mutations, coverage, artifacts and unverified production requirements are recorded in `out/BUILD_N1FIX2_REPORT.md`.\n'
body=design.read_text();marker='\n\n## Build n1fix2\n';body=body.split(marker)[0]
design.write_text(body+section)
(B/'STATUS.md').write_text('Build n1fix2 is complete for the requested CPU/source scope. All confirmation findings are closed, CPU coverage gaps are zero, R2 failures are zero, and the only regression is BF16 parity. GO=false. Sources: out/BUILD_N1FIX2_REPORT.md, work/n1fix2/SUITE_COMPARISON.json, work/n1fix2/GAPS.json. Production P bytes, frame-host staging, GPU and inference acceptance remain unchecked.\n')
print('Report and design record written.')
