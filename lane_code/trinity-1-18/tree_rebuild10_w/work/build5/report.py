"""Publish the final measured outcomes; never infer a pass from a missing receipt."""
import json
from collections import Counter
from pathlib import Path

L=Path(__file__).resolve().parents[2]
def read(name):return json.loads((L/name).read_text())
suite=read('work/build5/SUITE_COMPARISON.json')
coverage=read('work/build5/CHANGED_COVERAGE.json')
delivery=read('work/build5/DELIVERY.json')
kits=read('work/build5/kits/RESULTS.json')
storage=read('work/build5/STATIC_AUDIT.json')
fixes=read('work/build5/FIXES.json')
tree=read('work/build5/proofs/suite_tree/results.json')
base=read('work/build5/proofs/suite_base/results.json')
r2=read('work/build5/proofs/suite_tree/r2/results.json')
details=read('work/build5/REPORT_DETAILS.json')
cause_notes={row['test']:row['cause'] for row in details['cause_notes']}
causes=Counter(cause_notes.get(row['test'],row['cause']) for row in suite['failures'] if row['preexisting'])
joined=read('work/build5/proofs/suite_tree/r2/PUBLISHED_JOIN.json')
assert tree['complete'] and base['complete'], 'The complete package suite is required'
cpu=coverage['classes'].get('CPU-reachable unresolved',0)
qualified=suite['regressions']==0 and not cpu and not suite['fatal'] and not suite['r2_failures'] and not suite['shared_grammar_failures']
lines=['# Build 5 report','',
       ('**CPU qualification complete; production remains blocked.**' if qualified else '**CPU qualification incomplete; production remains blocked.**'),'',
       'The delivered source reindexes admitted rows after frame resolution, reserves retained checkpoint archives, joins missing program frames through the pinned native map reader, and requires explicit frame-host receipts. No remote call, launch or GPU work was performed.','',
       '## Package suite','',
       '| Run | Passed | Pre-existing failure events | Remaining regression events | Fixed cases | Skipped |',
       '|---:|---:|---:|---:|---:|---:|',
       f"| {suite['run']} | {suite['passed']} | {suite['preexisting']} | {suite['regressions']} | {len(fixes['cases'])} | {suite['skipped']} |",'',
       'Sources: `work/build5/SUITE_COMPARISON.json`, `work/build5/FIXES.json`, and `work/build5/proofs/suite_tree/results.json`. Run/pass counts count unittest methods; failure events also include subtests and setup/import errors. Fixed cases count unique previously failing methods that pass in the final package, including harness and fixture repairs; they do not count distinct production defects. The comparison receipt lists every failure, the same test on the untouched base, and both tracebacks.','',
       'Explicit legacy test adaptations and their retained checks are recorded in `work/build5/LEGACY_ADAPTATIONS.json`. These preserve unauthenticated-reader refusals and the visual-only connector contract. The native artifact reader also handles an absent camera connector. No failure is converted into a skip or expected failure.','',
       f"R2/shared execution: {r2['tests']} run, {len(r2['passed'])} passed, {len(r2['errors'])} errors and {len(r2['failures'])} failures. Source: `work/build5/proofs/suite_tree/r2/results.json`. Shared grammar cases run against both the packaged fixture and the native validator; their identical supplied hashes are verified in `work/build5/STATIC_AUDIT.json`. The suite count includes both executions.",'',
       '| Pre-existing cause | Events |','|---|---:|']
for cause,count in causes.items():lines.append(f'| {cause} | {count} |')
lines+=['','Sources: `work/build5/SUITE_COMPARISON.json` and the traceback-supported cause notes in `work/build5/REPORT_DETAILS.json`. These failures are not counted as passes. The original comparison receipt remains unchanged.','',
        'The package contains the tree, both kits, bounded examples, the untouched comparison source and the harness. Run `bash /absolute/extracted/path/work/build5/PACKAGE_TEST.sh /absolute/path/to/delivery.tar` from an empty working directory. The runner uses the specified local Python environment and refuses subprocess/network operations inside tests. It checks temporary bytes before and after each test and overwrites completed scratch products in place with hash receipts.','',
        'A preliminary diagnostic run allowed legacy scratch files outside `work/tmp`. The identified source-local paths were made read-only without changing their contents; the record is `work/build5/proofs/artifact_locations/PROTECTION.json`. That run does not qualify temporary-location compliance. The final packaged run places its extracted sources and test working directories under `work/tmp`; its harness confines test writes to that root and each proof’s fixed output folder.','',
        'The boundary measurements also caught legacy teacher fixtures exceeding the temporary cap. The harness recorded refusals and compacted the completed scratch products before continuing. These cases fail on both source versions and remain in the pre-existing failure count; the run does not establish that temporary usage stayed below the cap at all times.','',
        '| Run | Maximum measured temporary bytes | Tests over the temporary cap |','|---|---:|---:|',
        *[f"| {entry['variant']} | {max(entry['maximum']['before_bytes'],entry['maximum']['after_bytes'])} | {len(entry['above_cap'])} |" for entry in details['temporary_sizes']],
        '', 'Sources: `work/build5/REPORT_DETAILS.json`, `work/build5/proofs/suite_tree/temporary_sizes.json`, and `work/build5/proofs/suite_base/temporary_sizes.json`. The detail receipt names every affected test. Current retained storage is recorded in `work/build5/STATIC_AUDIT.json`.','',
        '## Changed statements','','| Class | Statements |','|---|---:|']
for name,count in coverage['classes'].items():lines.append(f'| {name} | {count} |')
for name in ('CPU-reachable unresolved','frame-host','model-loader','GPU'):
    if name not in coverage['classes']:lines.append(f'| {name} | 0 |')
lines+=['','Source: `work/build5/CHANGED_COVERAGE.json`. The denominator consists of changed AST statement starts relative to the untouched base. A hit counts only when both the file digest and compiled-code fingerprint match the current source. Each unexecuted statement has its missing-input reason in that receipt. Mutation-generated code is excluded.','',
        'The prior unresolved statements are reconciled individually in `work/build5/proofs/lineage/RECONCILIATION.json`. That mapping reconstructs the previous source from its preserved diff and verifies its sealed digest. Revised materializer statements map to their replacement coverage; redundant unreachable guards after unconditional refusals are identified explicitly.','',
        '## CPU proofs and limits','',
        '- The late-refusal test runs the real intake, dense-frame verification, materializer and SQLite reader on tiny synthetic RGB. It checks orphan twins and manifest denominators, then runs the real reindexer and registered sampler over metadata with the same late-row loss. A bounded slice must refuse the production repeat limit; no full store is built. Evidence: `work/tree_r1/tests/test_r2_build5.py`, `work/build5/proofs/suite_tree/r2/REINDEX.json`.','',
        '- The checkpoint proof measures real tiny optimizer tensors and weights, includes retained archive copies in the native whole-leg budget, and uses actual filesystem readings. A test reservation leaves room for native files but makes the retained archives exceed the available space; no large file is allocated. Persistence tests use tiny generated state bytes and substitute transport responses. Evidence: `work/tree_r1/tests/test_r2_build5.py`, `work/tree_r1/tests/test_r2_build5_persistence.py`, `work/build5/proofs/suite_tree/r2/DISK.json`.','',
        f"- The frame join uses the real native gzip map reader and adapter. All {len(joined['rows'])} published missing-frame examples resolve their frame references with a synthetic schema-correct map, and their target text remains unchanged. Source: `work/build5/proofs/suite_tree/r2/PUBLISHED_JOIN.json`. The real map, RGB, scene census and final admission remain frame-host inputs. Input provenance: `work/build5/JOIN_INPUTS.json`; test: `work/tree_r1/tests/test_r2_build5.py`.",'',
        '- Native producer/reader and model proofs use synthetic RGB, a tiny processor at the pretrained input boundary, tiny random model weights and synthetic vision tensors. The real heads and frozen-tower call sites remain inside the forward path. These prove CPU mechanics, not the staged pretrained export. Evidence: `work/tree_r1/tests/test_r2_build3.py`, `work/tree_r1/tests/test_r2_data_path.py`, `work/tree_r1/tests/test_r2_models.py`, and the proof JSON files under `work/build5/proofs/suite_tree/`.','',
        '- The real host entry stages tiny archive members and inline inputs before resolving packet files. The packet reader then refuses incorrect pose bytes; no full store is built. Runtime identity bytes stand in for the absent pinned runtime. Physical staging failures write a refusing receipt. Evidence: `work/tree_r1/tests/test_r2_build5_host_order.py`, `work/build5/proofs/suite_tree/r2/HOST_ORDER.json`.','',
        '## Frame-host checklist','']
check=(L/'out/FRAME_HOST_JOB.md').read_text()
lines.append(check[check.index('| Item |'):check.index('\nReceipts use')])
lines+=['','Source: `out/FRAME_HOST_JOB.md` and `work/tree_r1/launch_r2/checklist.py`. Every required step writes a passing or refusing receipt. The full host result and receipt reuse require the complete passing set. Local tests replace external bytes and runtime identity at the stated boundaries; none qualifies the actual frame-host inputs.','',
        '## Review dispositions','',
        'The identifiers refer to `work/review1/REVIEW_VERDICT_TREE.md`. “CPU fixed” applies to the named behavior, not production readiness.','',
        '| Item | Disposition | Evidence and remaining input |','|---|---|---|',
        '| 1 | Explicit mandatory host check | `launch_r2/staging.py`, `launch_r2/stdlib_probe.py`, `launch_r2/checklist.py`; actual pinned venv, bwrap and system interpreter remain unchecked. |',
        '| 2 | Explicit mandatory host check | `launch_r2/staging.py`, `launch_r2/checklist.py`; packaged tiny-archive, hash and escape tests passed (`work/build5/proofs/suite_tree/r2/results.json`); actual parent archives remain absent. |',
        '| 3 | CPU fix; full host admission pending | `student_pilot/r2_materialize.py`, `student_pilot/r2_mix.py`, `student_pilot/r2_adapters.py`; late refusals and native joins have bounded proofs, not a full store. |',
        '| 4 | CPU disk fix and explicit transport check | `student_pilot/checkpoint_space.py`, `launch_r2/persistence.py`, `launch_r2/checklist.py`; actual durable full-state recovery remains unqualified. |',
        '| 5 | Fail-closed catalog; production blocked | `student_pilot/r2_policy.py`, `launch_r2/checklist.py`; the delivered catalog is empty until real bank files are supplied and bound. |',
        '| 6 | Preserved provenance guards | `student_pilot/r2_contract.py`; final R2 contract and mutation tests are listed in the suite receipt. |',
        '| 7 | Preserved override-free parent path | `launch_r2/parent.py`; parent configuration and fault tests are listed in the suite receipt. |',
        '| 8 | Preserved merged exclusion pin | `student_pilot/r2_scene_bindings.py`; `work/build5/STATIC_AUDIT.json` verifies the supplied pin. |',
        '| 9 | Explicit mandatory vocabulary check | `student_pilot/r2_openers.py`, `launch_r2/checklist.py`; the actual staged export and vocabulary witness are still required. |',
        '| 10 | Preserved native authorization checks | `launch_r2/bootstrap.py`; production bootstrap requires the native authorization checks. |',
        '| 11 | Kits scanned; mandatory runtime scan | `launch_r2/build.py`, `launch_r2/checklist.py`; actual native runtime outputs remain unqualified and may be refused by the scanner. |',
        '| 12 | Separate closed authorization | Each kit binds its own unsigned GO=false authorization; `work/build5/kits/RESULTS.json`. |',
        '| 13 | Bound packet and receipt checks | `launch_r2/host.py`, `launch_r2/entry.py`; receipt reuse additionally checks every mandatory host receipt. |',
        '| 14 | Preserved conservative exclusions | `student_pilot/r2_exclusions.py`; no benchmark or held-out exclusion was waived. |',
        '| 15 | Duplicate denominators preserved | `student_pilot/r2_materialize.py`; repeated-family late refusals retain their originating manifest. |',
        '| 16 | Final reader requires sampling | `student_pilot/carrier_c1_data.py`; materializer receipts bind rebuilt final indices. |',
        '| 17 | Current suite and strict coverage | `work/build5/proofs/suite_tree/results.json`, `work/build5/CHANGED_COVERAGE.json`; mutation-generated executions do not count as source coverage. |','',
        'Implementation paths in this table are relative to `work/tree_r1/`. Final test outcomes, including any failure, are authoritative in `work/build5/SUITE_COMPARISON.json`. Historical real-row results in `out/BUILD4_REPORT.md` were not rerun; missing copied proof files were not treated as evidence.','',
        '## For the second review','',
        '- Run the delivered package from an empty directory and inspect every base comparison, R2 result and shared grammar result.','- Inspect the current hash-matched coverage receipt, especially every external-input classification and excluded mutation code object.','- Review the split late-refusal proof: real bounded producer/reader behavior and exact sampler metadata are separate; full-store admission still requires the frame host.','- Supply and authenticate the real runtime, archives, map, bank files and export witness before attempting the host checklist. Inspect output-scan refusals rather than waiving job-visible leaks.','- Keep launch authorization closed until the real-byte checklist and independent review pass.','',
        'Not checked: actual frame-host Python compatibility, actual archive contents and namespace layout, real frame-map/RGB joins, full-store reconstruction and repeats, staged pretrained vocabulary, real bank membership, remote upload/restore, full trainer-state recovery, native runtime-output scan, distributed GPU execution, memory fit, speed or benchmark results.','',
        '## Artifact identity','',
        f"Package: `{delivery['path']}`; {delivery['bytes']} bytes; SHA256 `{delivery['sha256']}`. Source: `work/build5/DELIVERY.json`.",
        f"Tree seal: `{delivery['source_revision']}`. Source: `out/TREE_SEAL.json`. Inventory and diff: `out/TREE_FILES.sha256`, `out/TREE.diff`.",'']
for kit in kits:lines.append(f"Kit `{kit['kit_path']}`: `{kit['kit_sha256']}`. Source: `work/build5/kits/RESULTS.json`.")
lines+=['','Storage and supplied-pin checks: `work/build5/STATIC_AUDIT.json`. Test temporary-size measurements: `work/build5/proofs/suite_tree/temporary_sizes.json` and `work/build5/proofs/suite_base/temporary_sizes.json`.']
(L/'out/BUILD5_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(qualified=qualified,cpu_gaps=cpu,remaining_regressions=suite['regressions'])))
