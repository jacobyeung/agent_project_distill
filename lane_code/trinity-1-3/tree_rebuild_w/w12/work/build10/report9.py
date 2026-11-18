"""Write review evidence from completed receipts without changing the sealed tree."""
import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
def read(name):return json.loads((B/name).read_text())
delivery=read('DELIVERY.json');coverage=read('CHANGED_COVERAGE.json')
comparison=read('SUITE_COMPARISON.json')
packet=read('proofs/packet/results.json');kits=read('KIT_RESULT.json')
text=read('proofs/text/RESULT.json');extent=read('proofs/extent_admission/RESULT.json')
inventory=read('proofs/audit/INFERENCE_COMPONENTS.json')
lines=[
'# Build 9fix',
'',
'The source and GO=false kits are packaged for review. Qualification remains blocked by the full VQA division proof and the discrepancies below. No Orchard or GCS call, external network access or GPU execution occurred.',
'',
'All relative evidence paths below are rooted at `/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/w10`. Inputs outside that root were read-only. The source is `work/tree_r1`; the comparison base is `work/base/tree_b01ce449`.',
'',
'| Finding | Status | Result and evidence |',
'|---|---|---|',
'| F1 | Blocked on exact acceptance counts; semantic fix implemented | Recorded head-response bytes authenticate the status exemption. Text gate, intake and independent reader refuse the real-row forgeries. The final extent gate necessarily rejects old unaudited/half-box rows. `work/build10/proofs/text/RESULT.json`, `work/build10/proofs/text/BEFORE_EXTENT_GATE.json`. |',
'| F2 | Closed | The inter-span status test catches greedy M02. M10 remains equivalent and unchanged. `work/build10/proofs/mutation_M02/RESULT.json`, `work/build10/proofs/text/MUTATION_RESULTS.json`. |',
'| F3 | Closed | Status words accept arbitrary whitespace, including Unicode whitespace, in the text gate and reader. Other text patterns retain their scope. `work/tree_r1/tests/test_r2_build9fix.py`, `work/build10/proofs/text/RESULT.json`. |',
'| F4 | Closed | Each staged kit checks the bytes and SHA of its cited mix: A0/A2 cite their bound r2 table; R1 cites its own card. `work/build10/MIX_BINDINGS.json`, `work/build10/proofs/package/KIT_TESTS.json`. |',
'| F5 | Closed for binding and admission; launch remains blocked | Repaired sources and per-row extent receipts are pinned. Intake and reader independently refuse missing, half, unknown, altered or uncertified geometry. Existing scene and repeated-call refusals remain. `work/build10/proofs/extents/RESULT.json`, `work/build10/proofs/half_refusals/RESULT.json`, `work/build10/proofs/extent_admission/RESULT.json`. |',
'| F6 | Blocked on full-store proof | The supplied removal list and production division are SHA-bound and staged through the kit builder. The CPU gate checks VQA and routing scenes. List/division and bounded native build_stream tests pass; the complete bound VQA census and complete production build_stream proof were not run. `work/build10/F6_BINDING.json`, `work/build10/proofs/division/RESULT.json`, `work/build10/proofs/division/ROUTING_SCENES.json`, `work/build10/proofs/native_scene/results.json`. |',
'',
'## Artifacts',
'',
f"- Tree seal: `{delivery['tree_seal']}` (`out/TREE_SEAL.json`).",
f"- Package: `{delivery['path']}`; SHA256 `{delivery['sha256']}`; {delivery['bytes']:,} bytes; {delivery['format']} (`work/build10/DELIVERY.json`).",
'- Source comparison and file inventory: `out/TREE.diff`, `out/TREE_FILES.sha256`.',
'- Launch permission remains GO=false (`work/build10/KIT_RESULT.json`).',
'',
'| Kit | SHA256 | Evidence |','|---|---|---|',
]
for name,value in kits.items():
    sha=value.get('kit_sha256',value.get('sha256','see receipt'))
    lines.append(f'| {name} | `{sha}` | `work/build10/KIT_RESULT.json` |')
lines += ['', '## Admission evidence', '',
'The unchanged original slices retain their text-gate counts. Final reader and intake counts below include the mandatory extent receipt. They therefore do not reproduce the old reader counts. Every count in this table comes from `work/build10/proofs/text/RESULT.json`.',
'', '| Original family | Text | Final reader | Final intake | Forgery cases refused in each path |', '|---|---:|---:|---:|---:|']
for family,row in text['families'].items():
    c=row['counts'];a=row['attacks']
    assert a['cases']==a['text_refused']==a['reader_refused']==a['intake_refused']
    lines.append(f"| {family} | {c['text']} | {c['reader']} | {c['intake']} | {a['cases']} |")
lines += ['',
'The F1-only baseline admitted 1,915 original units rows at intake, whereas the prompt requests 1,895 for that family. The baseline proof stopped at this discrepancy and is partial. No exclusion was changed to fit the requested count (`work/build10/proofs/text/BEFORE_EXTENT_GATE.json`).',
'',
'Each attack uses a real row and inserts a forged status response, with or without an authored ground call, into the target alone or into target plus events. The raw printed ground record remains the grammar authority. The reader does not rely on intake or r2_membership (`work/build10/proof_text.py`, `work/tree_r1/student_pilot/row_text_audit.py`, `work/tree_r1/student_pilot/carrier_c1_run.py`).',
'The text-only proofs supply unavailable-RGB metadata pins and, when the supplied metadata lacks a frame rate, GUESS 24 FPS. These proofs exercise admission and row reading without RGB or head execution (`work/build10/proofs/text/RESULT.json`).',
'The permanent M02 regression test passes on the clean function and fails on the in-memory greedy mutation: clean 1 test, 0 failures; mutant 1 test, 1 failure, with no errors in either run. The receipt binds both source hashes and the exact inter-span input. M10 remains equivalent and unchanged (`work/build10/proofs/mutation_M02/RESULT.json`).',
'',
'| Repaired family | Source rows | Reader | Intake | Evidence |', '|---|---:|---:|---:|---|']
for family,row in extent['families'].items():
    c=row['counts'];lines.append(f"| {family} | {c['source']} | {c['reader']} | {c['intake']} | `work/build10/proofs/extent_admission/RESULT.json` |")
lines += ['',
'Recovery intake rejects 61 rows under the existing scene exclusion and 156 under the existing repeated-call rule. Distance intake rejects 103 scene-excluded rows; units intake rejects 510. The admitted unit marginals are centimeters 2,675, feet 2,735 and inches 2,657. Full family, unit, status and dataset counts are recorded in `work/build10/proofs/extent_admission/RESULT.json`; source counts and audit/repair counts are in `work/build10/proofs/extents/RESULT.json`.',
'The bound R1 card passes the required recovery/unit presence checks, including independent zero-population refusals. Its distance cell requests 15,600 draws, while the admitted distance rows support at most 5,904 under the existing repeat ceiling; 9,696 draws require reallocation. Other post-filter cell populations and sampler indices are unbound, so full allocation remains BLOCKED (`work/build10/proofs/mix_accounting/RESULT.json`).',
'',
'The units source was streamed and never copied. The receipt binds the normalized supervision projection, qid, original line hash, per-box audit verdicts and repair hash. Frame joins have separate pins. No raster audit was rerun: this build trusts the SHA-pinned supplied audits (`work/build10/bind_extent.py`, `work/build10/inputs/extents.json`). Repaired rows are the default; filtered variants remain explicit source parameters (`work/build10/inputs/row_sources.json`).',
'',
'The removal list contains 601 unique keys outside the production train division and none in its held-out scenes. Its family counts are 468, 127 and 6 for b12_cntapp_gt_v1, vsti_rel_v4 and r1_room_traced respectively (`work/build10/proofs/division/RESULT.json`). These are checks of the supplied list, not an independent census of the full VQA store. The list SHA is `02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411`; the division SHA is `0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad` (`work/build10/F6_BINDING.json`).',
'', '## Qualification', '',
f"Packet suite: {len(packet):,} tests, {sum(r.get('outcome')=='passed' for r in packet.values()):,} passed; see per-test outcomes in `work/build10/proofs/packet/results.json`.",
'', '| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |', '|---|---:|---:|---:|---:|---:|---|']
for variant in ('tree','base'):
    result=read('proofs/suite_'+variant+'/results.json')
    lines.append(f"| {variant} | {result['tests']} | {len(result['passed'])} | {len(result['failures'])} | {len(result['errors'])} | {len(result['skips'])} | `work/build10/proofs/suite_{variant}/results.json` |")
lines += ['',
f"Comparison counts: preexisting failure events {comparison['preexisting']}; regression events {comparison['regressions']}; R2 failure events {comparison['r2_failures']} (`work/build10/SUITE_COMPARISON.json`). Counts retain scheduled executions and subtest events; they are not unique-method counts.",
f"Regressions beyond the allowed BF16 parity exception: {sum(not r['preexisting'] and 'BF16' not in r['cause'] for r in comparison['failures'])} (`work/build10/SUITE_COMPARISON.json`).",
'',
'The frozen archive, kits, fixture identity and source identity were checked; each suite group records its complete input-hash-bound receipt. Unchanged matching groups are eligible for resume (`work/build10/proofs/package/ARCHIVE.json`, `work/build10/proofs/suite_tree/*/GROUP_RECEIPT.json`, `work/build10/proofs/suite_base/*/GROUP_RECEIPT.json`).',
'The final source differs from the full-suite snapshot only inside the tool-mode test method, whose synthetic rows now carry a pinned extent certificate. The complete changed test module ran from the final archive. Other module results were retained only after verifying unchanged production source, test bodies, fixtures, runner and bound inputs. The source inventories, AST check, result hashes and retained groups are recorded in `work/build10/proofs/fixture_requalification/RESUME_RECEIPT.json`; the rerun is `work/build10/proofs/suite_tree/legacy_changed/results.json`.',
'The actual kit read-checks also reject mismatched report hashes and mismatched configuration pins in bounded synthetic metadata fixtures (`work/build10/proofs/mix_checks/RESULT.json`).',
'',
'The CPU RGB proof runs real materialize, intake, SQLite reader, RGB loading, routing encode, response masking, CarrierC1.forward and backward with the bound final recipe. It checks positive finite loss, supervised tokens and nonzero finite gradients. Stand-ins are tiny native Qwen and pose-head weights plus a lossless tokenizer/processor at the unavailable pretrained/GPU boundary; frames and the printed failure event are synthetic. This is a training-path proof, not deployed frozen-tower or product acceptance (`work/build10/proofs/forward/RESULT.json`, `work/build10/proofs/targeted9/results.json`).',
'',
'Changed-statement coverage uses standard-library sys.monitoring, compiled-code fingerprints and exact current file hashes against the untouched base. Inherited observations count only when the complete current file matches its authenticated prior receipt. Unexecuted GPU, model-loader and frame-host statements remain explicitly classified (`work/build10/CHANGED_COVERAGE.json`).',
'', '| Coverage class | Statements | Evidence |', '|---|---:|---|']
for name,count in coverage['classes'].items():lines.append(f'| {name} | {count} | `work/build10/CHANGED_COVERAGE.json` |')
if 'CPU-reachable unresolved' not in coverage['classes']:lines.append('| CPU gaps | 0 | `work/build10/CHANGED_COVERAGE.json`, `work/build10/GAPS.json` |')
lines += ['',
'CPU gaps are not counted as covered. Any remaining gaps are enumerated in `work/build10/GAPS.json` and block the requested zero-gap qualification.',
'', '## Product inference outside the weights', '',
'No answer selector, guard, fallback or rule table was added. These existing components sit outside registered weights or the model forward pass and are handed to the acceptance lane unchanged in behavior. Source line references are rooted at `work/tree_r1` (`work/build10/proofs/audit/INFERENCE_COMPONENTS.json`).',
'', '| Component | Source | Operation |', '|---|---|---|']
for row in inventory['known_outside_forward']:
    lines.append(f"| `{row['component']}` | `{row['file']}:{row['line']}` | {row['operation']} |")
lines += ['',
'The complete conservative local import inventory, with file:line and source hashes, is `work/build10/proofs/audit/INFERENCE_COMPONENTS.json`. It includes support and training imports. Dynamic dispatch and external dependency closure are unproven; this report does not certify that the listed known components exhaust the deployed inference path. The acceptance lane must establish that closure.',
'', '## For the confirmation review', '',
'- Recheck semantic response authentication against forged target-only and target-plus-event cases, including the greedy M02 mutation.',
'- Check the extent receipt projection through normalization, native production, materialization and independent reading. Reject a changed row, unknown box or unpinned receipt.',
'- Verify that each kit cites its exact bound mix bytes and that the removal list stages through normal pinned-input handling.',
'- Run the full bound VQA division census and production build_stream proof on an approved host. Confirm that the independently found outside-division key set equals the supplied removal list. The bounded proof cannot establish this.',
'- Resolve the original acceptance-count discrepancy and review the preserved recovery repeated-call refusals before accepting the requested row-count criteria.',
'- Review the BF16 exception and the unexecuted frame-host, GPU and model-loader statements in the final comparison and coverage receipts. GO remains false until required acceptance evidence exists.',
'- Judge the product inference path using the outside-weights inventory. Real pretrained weights, deployed frozen towers, GPU/BF16 parity, production frame staging and full end-to-end model acceptance were not checked in this build.',
'',
'Inherited production blockers remain in `work/build10/N1_CARRIED_BLOCKERS.json`. Weight scale and budget assumptions carried into kits remain GUESS, not benchmark-derived choices (`work/build10/stage9.py`, `work/build10/inputs/config.json`). Storage and path checks are recorded in `work/build10/STORAGE.json`, `work/build10/EXECUTABLE_PATH_SEARCH.json`, and `work/build10/PIN_AUDIT.json`.',
]
(L/'out/BUILD9FIX_REPORT.md').write_text('\n'.join(lines)+'\n')
ledger=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
section='\n\n## Build 9fix\n\nThe review artifact binds semantic response authentication, Unicode status matching, exact per-kit mix bytes, repaired-row extent receipts and the production division removal list. GO remains false. The full-store division proof and the exact original acceptance-count criteria remain unresolved. Source seal: `'+delivery['tree_seal']+'` (`out/TREE_SEAL.json`). See `out/BUILD9FIX_REPORT.md` for final suites, coverage, kit hashes, limitations and confirmation-review checks.\n'
prior=ledger.read_text();marker='\n\n## Build 9fix\n'
ledger.write_text(prior.split(marker)[0].rstrip()+section)
print(str(L/'out/BUILD9FIX_REPORT.md'))
