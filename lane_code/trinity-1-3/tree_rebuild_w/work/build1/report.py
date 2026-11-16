"""Build a reader-facing report from retained proof receipts."""
import json
from pathlib import Path
import re

L = Path(__file__).resolve().parents[2]
O, T = L/'out', L/'work/tree_r1'
def read(name):
    return json.loads((O/name).read_text())
def source(name, needle):
    lines = (T/name).read_text().splitlines()
    n = next(i for i, line in enumerate(lines, 1) if needle in line)
    return f'`work/tree_r1/{name}:{n}`'

tests, coverage, seal, proof = (read(n) for n in ('TEST_RESULTS.json', 'COVERAGE.json', 'TREE_SEAL.json', 'CPU_PATH_PROOF.json'))
if tests['errors'] or tests['failures']:
    raise ValueError('New tests have not passed')
classified = {}
for name, record in coverage.items():
    gaps = []
    for line in record['uncovered']:
        if name != 'student_pilot/r2_materialize.py':
            raise ValueError('Unclassified CPU statement: '+name+':'+str(line))
        gaps.append(dict(line=line, classification='frame-host', reason='Full-store mode is prohibited on Trinity and requires explicit frame-host admission.'))
    classified[name] = {**record, 'unexecuted_classes': gaps}
(O/'COVERAGE_CLASSIFIED.json').write_text(json.dumps(classified, indent=2)+'\n')

legacy = {}
for log in ('tests5.log', 'regression_final.log'):
    current = None
    for line in (L/'work/build1'/log).read_text().splitlines():
        match = re.match(r'(test_\w+) \(([^)]+)\) \.\.\. (.*)', line)
        if match:
            current = match[2]
            if current.startswith('tests.test_r2_'):
                current = None
            ending = match[3]
        else:
            ending = line
        if current and (ending in ('ok', 'ERROR', 'FAIL') or ending.startswith('skipped')):
            legacy[current] = dict(status=ending, source='work/build1/'+log)
            current = None
(O/'LEGACY_RESULTS.json').write_text(json.dumps(legacy, indent=2)+'\n')
passed = sum(v['status'] == 'ok' for v in legacy.values())
skipped = sum(v['status'].startswith('skipped') for v in legacy.values())
failed = [k for k,v in legacy.items() if v['status'] in ('ERROR', 'FAIL')]
total = sum(v['changed_statements'] for v in coverage.values())
executed = sum(v['executed'] for v in coverage.values())
prod = {k:v for k,v in coverage.items() if k.startswith('student_pilot/')}
prod_total = sum(v['changed_statements'] for v in prod.values())
prod_hit = sum(v['executed'] for v in prod.values())
family_proof = read('FAMILY_ENCODER_PROOF.json')
mh0, mh1 = proof['materialize_hashes_before'], proof['materialize_hashes_after']
rh0, rh1 = proof['reader_hashes_before'], proof['reader_hashes_after']

report = f'''# Build 1 report

The bounded contract and data path are implemented and pass the new CPU suite. This is a fixture proof, not real-data admission or authorization to launch. The shared row validator, real family manifests, Orchard stores and export metadata remain unavailable.

## Delivered behavior

| Item | Implementation and evidence |
|---|---|
| Init binding | The accepted artifact, parent run and kit, source seal, step and surviving configuration prefix are constants in {source('student_pilot/r2_contract.py', 'INIT =')}. Preparation checks supplied export metadata, the actual configuration's init pin, code seal, mixture digest and membership. Exact parent-run resume refuses; a distinct warm-start run passes. Test: {source('tests/test_r2_data_path.py', 'def test_init_')} |
| Direct targets | One validator implements explicit line kinds, grounded numeric provenance, bounded Locate references, counts, arithmetic, numeric answers and all requested refusals. Rules and replacement point: {source('student_pilot/trace_grammar.py', 'RULES =')}; `out/GRAMMAR_RULES.json`; `work/tree_r1/student_pilot/R2_DATA_PATH.md`. The validator deliberately accepts a conservative syntax; it cannot establish visual truth from metadata. |
| Program targets | Ground and camera events enter native rendering and masked suffix encoding. Room size is direct. Unit arithmetic uses printed values and declared conversion constants. Failed-call continuations require Locate evidence and cannot call again. Every response block must coincide with a masked event span. Sources: {source('student_pilot/trace_grammar.py', 'def validate_program')}, {source('student_pilot/r2_contract.py', 'def event_row')}, {source('student_pilot/carrier_c1_routing.py', 'def encode(processor')}. |
| Intake | The documented module command reads pinned family envelopes, validates rows, binds scene coverage and all supplied exclusion records, carries upstream receipts, and reports counts/reasons in JSON and text. It excludes rooms missing source-row/frame lineage and rejects unfiltered ID collisions. Sources: {source('student_pilot/r2_intake.py', 'def intake')}, {source('student_pilot/r2_exclusions.py', 'SEALED =')}, {source('student_pilot/r2_materialize.py', 'def materialize')}. |
| Native stores | The producer writes VQA, routing, pose and pointing SQLite rows plus membership and dense RGB metadata. The native reader verifies row, target and stream membership. Missing bytes or dense sources produce a recorded frame-host boundary with no store receipt. Sources: {source('student_pilot/r2_adapters.py', 'def normalize')}, {source('student_pilot/r2_materialize.py', 'def materialize')}, {source('student_pilot/carrier_c1_run.py', 'self.r2_admission =')}. |
| Frame identity | Root mapping precedes frame authentication. A bounded process memo authenticates device/inode/size/mtime identities and refuses stale content or races. Dense clips use ordered source ordinals and content hashes, while rows retain their clocks and paths; pose prefixes are expanded. Sources: {source('student_pilot/r2_frames.py', 'def resolve_frame')}, {source('student_pilot/r2_dense.py', 'def build_training')}. |
| Dense rule | Training imports evaluation's exact nested-index selector. The clock, alias and multi-store fixtures compare selections and content identities; the decoder test uses an actual locally generated video. Sources: {source('student_pilot/r2_dense.py', 'from .dense_eval')}, {source('tests/test_r2_data_path.py', 'def test_content_clocks')}, {source('tests/test_r2_dense_decode.py', 'def test_real_video')}. |

## CPU results

The new suite passes {tests['tests']} tests, with no failures, errors or skips (`out/TEST_RESULTS.json`; `work/build1/final_validation.log`). Native intake, materialization, preparation, membership reads and encoding run end to end. The native model forward produces finite losses for each of the {len(proof['families'])} streams (`out/CPU_PATH_PROOF.json`). Another {len(family_proof['rows'])} semantic-family fixtures reach their native encoders (`out/FAMILY_ENCODER_PROOF.json`).

The inference-boundary stand-ins are the tiny lossless processor/tokenizer and randomly initialized tiny native Qwen/CarrierC1 weights. The native preparation proof uses tiny model metadata behind the base's explicit CPU rehearsal gate and synthetic export metadata containing the supplied identity; it does not load or authenticate the unavailable export bytes ({source('tests/test_r2_preparation.py', 'def test_native_preparation')}). RGB images are explicitly synthetic; no real image, checkpoint, database or cache was copied. The file-race mutation injects a real timestamp change during authentication, and the storage-cap mutation scales its limit down for the test. Neither replaces a producer or reader in the end-to-end proof. These tests do not establish pretrained-tokenizer parity, visual-label correctness or GPU fit.

The existing tests record {passed} passes, {skipped} skips and {len(failed)} remaining failure (`out/LEGACY_RESULTS.json`). The remaining failure is the native Qwen video-processor test: installed transformers calls undefined `tvF`. It also fails on the untouched base (`out/BASELINE_TEST_RESULTS.json`, `work/build1/baseline.log`). Missing staged assets and forbidden local sockets account for the skips. The base-comparison parity test passes after binding its base path to the supplied lane copy (`work/build1/regression_final.log`). The entire repository suite was not run.

| Refusal | Proof source |
|---|---|
| Old format, missing trace, wrong unit, wrong scene, stale row pin | {source('tests/test_r2_data_path.py', 'def test_intake_mutations')} |
| Empty think, bare answer restatement, filler-only steps | {source('tests/test_r2_data_path.py', 'def test_all_required_mutations')} |
| Glued units, number words, unsupported numbers | `out/MUTATIONS.json`; {source('tests/test_r2_refusals.py', 'def test_grammar_arithmetic')} |
| Seconds, exhaustive frame lists, absence claims | `out/MUTATIONS.json` |
| Direct calls/responses; program types offered as direct; room calls | {source('tests/test_r2_data_path.py', 'def test_program_refuses')} |
| Unmasked response embedded as prose; bad conversion; repeated failed call | {source('tests/test_r2_families.py', 'def test_ground_event_fail')} |
| Unknown scene coverage; changed exclusions; bad upstream receipts | {source('tests/test_r2_refusals.py', 'def test_scene_and_upstream')} |
| Unfiltered route collision; full store on local node | {source('tests/test_r2_data_path.py', 'def test_marker_full_store')} |
| Changed frame content, hash mismatch and hashing race | {source('tests/test_r2_data_path.py', 'def test_frame_memo')}; {source('tests/test_r2_refusals.py', 'def test_mapping_paths')} |

## Hash work and storage

The fixture materialization made {mh1['requests']-mh0['requests']} authentication requests but performed {mh1['hashes']-mh0['hashes']} content hashes. The subsequent reader/encoder proof made {rh1['requests']-rh0['requests']} requests and performed {rh1['hashes']-rh0['hashes']} additional hashes (`out/CPU_PATH_PROOF.json`). Sparse reads reused dense authentication. Distinct physical file identities must still be verified even if they declare the same content hash. Real-job and real-training-step hash counts remain unmeasured.

The harness measured {tests['tmp_bytes']} temporary bytes and {tests['lane_bytes']} lane bytes at the end of the new suite (`out/TEST_RESULTS.json`). It checks temporary size before and after each test, limits file size, retains artifacts, hides CUDA, and blocks network and deletion operations (`work/build1/run_tests.py`, `work/build1/TEST.sh`). No write over the brief's large-write boundary was needed.

## Changed-statement coverage

The standard-library line tracer counts AST statements whose source spans intersect the unified changes, including multiline statements. It measured {executed}/{total} changed statements across trainer code and tests; production code contributes {prod_hit}/{prod_total} (`out/COVERAGE.json`). All locally reachable changed production statements ran. The remaining {total-executed} statements belong to full-store admission on the separate frame host; the Trinity guard prohibits executing that branch here (`out/COVERAGE_CLASSIFIED.json`). CPU-only, model-loader and GPU classes have no unexecuted changed statements. This does not claim coverage of unchanged model loaders or GPU code.

| File | Executed / changed statements | Unexecuted class |
|---|---:|---|
'''
for name, value in coverage.items():
    report += f"| `{name}` | {value['executed']}/{value['changed_statements']} | {'frame-host' if value['uncovered'] else 'none'} |\n"
report += f'''
Every coverage count in this table comes from `out/COVERAGE.json`.

## Open integration and defaults

- Shared grammar and real manifests: the versioned envelope and conservative validator are defaults, documented in `R2_DATA_PATH.md`. Reconcile them with the rows lane before real admission. Unknown formats and unknown overlap refuse.
- Real-row proof: `work/build1/REAL_ROW_PROOF.sh <rows_dir> <sealed_meta_dir>` expects a pinned complete family inventory at `sealed_meta_dir/REAL_ROW_INPUTS.json`. Its absent-input invocation refused as required (`work/build1/real_row_missing.log`). The fixture invocation of that same producer is explicitly synthetic. No real-row result is claimed.
- Real frames and export: verify the supplied Orchard export metadata and each family's native pins on their host. The surviving parent configuration identity remains a prefix. Dense source manifests and all pose sources must be present. Real dense coverage and real exclusion counts were not checked.
- Full materialization: the code admits it only off Trinity with an explicit frame-host flag. The later frame-host job must supply resource guards and exercise the unexecuted branch; no full store was created here.
- Component policy, withheld rooms, kit construction, configurations, mixture, external contract patches, the frame-host job/card and launch remain outside this build.

## Artifacts

`work/tree_r1` is the updated tree. `out/TREE.diff` is the unified diff; `out/TREE_FILES.sha256` lists every source-file hash. The native inventory and digest yield tree seal `{seal['tree_sha256']}` (`out/TREE_SEAL.json`). The same native digest confirms the read-only base is unchanged (`out/TREE_SEAL.json`). `out/GRAMMAR_RULES.json` records the replacement boundary's rule identity.
'''
(O/'BUILD1_REPORT.md').write_text(report)

design = O/'DESIGN_RECORD_tree_rebuild_20261115.md'
if not design.exists():
    design.write_text('# Trainer-tree design record\n')
with design.open('a') as handle:
    handle.write('''
## Build 1

**Question.** How can the next-leg tree admit honest traces and construct native trainer inputs before the real row and frame stores arrive?

**Answer.** Use one versioned grammar and manifest boundary, bind the accepted init at preparation, preserve native masked event encoding, and authenticate final row/target membership in the trainer. Build dense membership from content and source ordinals while retaining each row's clock. Missing frame material stops at an explicit host boundary.

**Reasons and evidence.** The recovered review failures concern raw logical reads, scene aliases, clocks, masked responses and missing exclusion receipts. The implemented paths and their exact source locations are in `BUILD1_REPORT.md`; retained tests, mutations and coverage are in `TEST_RESULTS.json`, `MUTATIONS.json`, `CPU_PATH_PROOF.json`, `FAMILY_ENCODER_PROOF.json` and `COVERAGE_CLASSIFIED.json`.

**Options rejected.** Flat direct targets containing responses would supervise external values. Path- or canonical-name-based dense identity would split identical content. Unknown scene overlap or missing upstream receipts would erase exclusions. An exact parent-run resume would hide changed code or mixture. A silent frame fixture would misrepresent a real-data proof. The implementation refuses each alternative.

**Defaults and risks.** The shared validator and real-row envelopes are unavailable, so the documented conservative syntax and versioned envelope are integration defaults. Metadata cannot prove visual relations. Native ground-event continuations rely on the admitted row lineage and printed response provenance; they do not claim a newly checked geometry backend. Full-store admission requires a separate frame host. The installed native video processor has a failure reproduced on the untouched base. These limits are disclosed in `BUILD1_REPORT.md`.

**Tests that settle the open points.** Reconcile the shared validator against the retained mutation corpus; publish the complete pinned family inventory; run `work/build1/REAL_ROW_PROOF.sh` on those inputs; then run native CPU admission with the real root map and export metadata on the frame host. Exercise full-store resource guards there before any GPU admission.

**Status.** The bounded build and synthetic CPU proofs are delivered. Real-row, frame-host and pretrained-model validation remain pending; no training or launch was performed. Exact counts, seal identities and source paths are in `BUILD1_REPORT.md`.
''' if '\n## Build 1\n' not in design.read_text() else '')
(L/'work/build1/STATUS.md').write_text('''# Build 1 status

The bounded contract and data path are delivered. The new CPU suite passes; final evidence is in `out/BUILD1_REPORT.md`, `out/TEST_RESULTS.json` and `out/COVERAGE_CLASSIFIED.json`.

The source tree, unified diff, per-file hashes, native tree seal, grammar rules and design record are written. The read-only base seal is unchanged (`out/TREE_SEAL.json`).

Real rows, frames and Orchard export metadata were unavailable. The real-row script refuses absent inputs. Full-store admission remains unexecuted behind the frame-host gate. The native video-processor dependency failure reproduces on the untouched base. No launch, GPU, network, Git, subagent or deletion ran.
''')
print(json.dumps(dict(new_tests=tests['tests'], legacy_passed=passed, legacy_skipped=skipped,
                     legacy_failed=failed, changed_statements=total, executed=executed, tree_sha256=seal['tree_sha256']), indent=2))
