"""Write the review report from current proof receipts, retaining failed gates."""
from pathlib import Path
from collections import defaultdict
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
def read(name):return json.loads((B/name).read_text())
def evidence(name):return '`work/build10/'+name+'`'
delivery=read('DELIVERY.json');kits=read('KIT_RESULT.json');comparison=read('SUITE_COMPARISON.json')
coverage=read('CHANGED_COVERAGE.json');hcoverage=read('HARNESS_COVERAGE.json');packet=read('proofs/packet/results.json')
eat=read('EAT1_SUMMARY.json');groups=read('EAT1_GROUP_EVIDENCE.json');patch=read('PATCH.json')
inventory=read('proofs/audit/INFERENCE_COMPONENTS.json');parity=read('proofs/parity/BYTE_PARITY.json')
out=[]
def p(s=''):out.append(s)
p('# Build 10')
p()
p('The candidate source, kits and archive are ready for review with **GO=false**. The build does **not** pass the requested acceptance gate. Bound-row numeric parity lacks the raw producer inputs, the computation migration remains partial, and b04 rejects its routed items at its sealed validator check. The EAT-1 reports are failures, including the report whose A2 clause says PASS. Sources: '+evidence('STEPS.json')+', '+evidence('EAT1_SUMMARY.json')+', '+evidence('proofs/parity/BYTE_PARITY.json')+'.')
p()
p('## Items and groups')
p()
p('| Item/group | Disposition | Remaining requirement and evidence |')
p('|---|---|---|')
rows=[
('0 / G8','Implemented; qualification blocked','The fixed_math role requires a registered module with no parameters, declared inputs/outputs, and persistent buffers matched to SHA-authenticated artifact tensors. The native syscall witness remains blocked by PTRACE_TRACEME denial. `work/build10/proofs/g8/test.log`, `work/build10/proofs/g8_available/RESULT.json`, `work/build10/HARNESS_COVERAGE.json`.'),
('1 / G1','Partial; blocked','Depth readout and map production enter forward. Stencil, percentile, clipping, spread-floor and ray constants are buffers. Point-depth helper constants, public-coordinate transforms and legacy readout branches remain outside the migrated module. Full bound-row operands are missing. `work/tree_r1/student_pilot/fixed_readout.py`, `work/build10/proofs/g1/RESULT.json`, `work/build10/EAT1_GROUP_EVIDENCE.json`.'),
('1 / G2','Implemented serving callback; blocked acceptance','Yaw and turn conversion/wrapping run through the registered heading module. The standalone geometry branch remains and the scanner still reports it. Original reader and fixture numeric parity pass; bound raw pose inputs are missing. `work/build10/proofs/g2/RESULT.json`, `work/build10/proofs/parity_build7/RESULT.json`.'),
('1 / G3','Implemented; bound-row proof blocked','Availability uses an artifact threshold buffer; a conflicting runtime threshold refuses. The availability boundary/reload test passes. Bound producer rotations are missing. `work/build10/proofs/g3/RESULT.json`, `work/build10/proofs/parity/NESTED_OPERANDS.json`.'),
('1 / G4','Partial; not closed','Frame-count and readout configuration are exported and used by readers. The standalone calculator precision remains unchanged, and token-grid integration is incomplete. This is unimplemented scope, not a missing-input pass. Complete frame-count reader qualification is also absent. `work/build10/DECISIONS.md`, `work/build10/proofs/g4/RESULT.json`, `work/tree_r1/trace_format/calculator.py:60`.'),
('1 / G5','Implemented; EAT-1 still blocked','The artifact declares call budgets. Exceeding a budget or failing to fit a whole tool response raises instead of truncating. EAT-1 still flags decoder attributes outside forward. `work/build10/proofs/g5/RESULT.json`, `work/build10/EAT1_GROUP_EVIDENCE.json`.'),
('1 / G6','Manifest binding closed; clause not closed','Production and tiny-reader manifests bind preprocessing and vendor source files as tower files. The copied harness still flags executed helper arithmetic; no new exemption was added. `work/build10/proofs/g6/RESULT.json`, `work/build10/eat1/adapters/build10_manifest.py`, `work/build10/EAT1_GROUP_EVIDENCE.json`.'),
('1 / G7','Partial; A4 blockers retained','Out-of-range calls raise without response tokens. Ground dispatch uses ground_route. Statuses without an owning registered head output remain named findings; no head output or suppression was invented. The compatibility property still references the existing fallback field. `work/build10/proofs/g7/RESULT.json`, `work/build10/EAT1_GROUP_EVIDENCE.json`.'),
('2 / byte parity','Blocked on bound producer inputs','Every available original-reader numeric response and the geometric unit fixture passes. The bound slices contain no raw pose/depth/FoV operands. No row bytes changed; no answer-derived operands were used. `work/build10/proofs/parity_build7/RESULT.json`, `work/build10/proofs/parity_tree/RESULT.json`, `work/build10/proofs/parity/NESTED_OPERANDS.json`.'),
('3 / readers','Executed; acceptance blocked','Native readers fail EAT-1. b04 has a sealed_validate_mismatch on tool-bearing items; its A2/A6 passes do not validate those routes. `work/build10/EAT1_SUMMARY.json`, `work/build10/EAT1_GROUP_EVIDENCE.json`.'),
('4 / final pass','Packaged; qualification blocked','The archive, source seal, GO=false kits, packet suite and frozen source/base suites have receipts. Remaining regression and coverage counts appear below. `work/build10/DELIVERY.json`, `work/build10/proofs/package/ARCHIVE.json`, `work/build10/SUITE_COMPARISON.json`.')]
for row in rows:p('| '+' | '.join(row)+' |')
p()
p('The readout modules preserve the original NumPy/Python operation order inside registered torch modules. They transfer tensors to CPU and do not establish a tensor-only GPU implementation. This choice preserves tested response bytes; it does not close the remaining migration or real-row gates. Source: '+evidence('DECISIONS.md')+'.')
p()
p('## Artifacts and bindings')
p()
p(f'- Tree seal: `{delivery["tree_seal"]}`. Source: `out/TREE_SEAL.json`.')
p(f'- Archive: `{delivery["path"]}`, {delivery["bytes"]} bytes, SHA256 `{delivery["sha256"]}`. Source: '+evidence('DELIVERY.json')+'.')
p(f'- Harness patch: `{patch["path"]}`, SHA256 `{patch["sha256"]}`. Source: '+evidence('PATCH.json')+'.')
p('- Source diff and inventory: `out/TREE.diff`, `out/TREE_FILES.sha256`. The untouched comparison base remains under `work/base/tree_b01ce449`.')
p()
p('| Kit | SHA256 | Admission | Evidence |')
p('|---|---|---|---|')
for arm in ('a2','a0','r1'):
    p(f'| {arm} | `{kits[arm]["kit_sha256"]}` | GO=false | '+evidence('KIT_RESULT.json')+' |')
p()
p('Each kit binds the exact mix bytes cited by its report. The removal-list pin and source seal pass the final binding audit. The inherited semantic tool-response exemption, full-extent admission, scene exclusions, division gate, R1 initialization choices, S2-off setting and own-probability setting remain binding. Sources: '+evidence('FINAL_BINDING_AUDIT.json')+', '+evidence('PIN_AUDIT.json')+', '+evidence('KIT_RESULT.json')+', `../w9f/out/BUILD9FIX_REPORT.md`.')
p()
p('The supplied harness archive and inherited package hashes were verified in place. All model-input entries of the b04 input hash list match. Its self-entry contains the empty-file digest and does not match the populated list; that entry is not a model input. Source: '+evidence('SUPPLIED_HASHES.json')+'.')
p('The harness baseline source matches the supplied archive. The patch is relative to that unchanged source copy. Source: '+evidence('HARNESS_BASELINE.json')+'.')
p()
p('## Byte parity')
p()
p('Counts below are recomputed response texts, not comparisons of stored text with itself. Build 7 replay loads its original weights and frames in place, verifies every original tensor, and adds only the new registered buffers. Sources: '+evidence('proofs/parity_build7/RESULT.json')+', '+evidence('proofs/parity_tree/RESULT.json')+', '+evidence('proofs/parity/NUMERIC_PARITY.json')+'.')
p()
p('| Input family | Response kind | Checked | Identical | Different | Evidence |')
p('|---|---|---:|---:|---:|---|')
for label,file in [('Build 7 original readers','proofs/parity_build7/RESULT.json'),('Existing geometric test fixture','proofs/parity_tree/RESULT.json'),('Seeded synthetic head outputs','proofs/parity/NUMERIC_PARITY.json')]:
    for kind,c in read(file)['counts'].items():p(f'| {label} | {kind} | {c["checked"]} | {c["identical"]} | {c["different"]} | {evidence(file)} |')
p()
p('Bound-slice counts include every occurrence of the named tool-response kinds. Missing raw geometry prevents recomputation; zero differences here is **not** a parity pass. External geometry stores were not read. Full external derivgen review-pool fixtures were not available. Heading availability, ground and gap do not gain a real-row parity claim from the synthetic tests. Sources: '+evidence('proofs/parity/BYTE_PARITY.json')+', '+evidence('proofs/parity/NESTED_OPERANDS.json')+'.')
p('Some rows contain independent world-box audit operands. They do not supply the original producer camera/reference transform, depth or provider-selection inputs needed to replay the serving response through the new modules. Those operands were not inferred from the printed response. Source: '+evidence('proofs/parity/BOX_OPERAND_EXAMPLES.json')+'.')
p('The build 7 response inventory also stores printed bodies and counts, without the missing producer inputs. The separate tiny-reader inputs were replayed in place. Source: '+evidence('proofs/parity/BUILD7_INPUT_AUDIT.json')+'.')
p()
p('| Bound slice | Kind | Bound | Checked | Identical | Different | Blocked | Evidence |')
p('|---|---|---:|---:|---:|---:|---:|---|')
for family in parity['families']:
    name=str(Path(family['source']).relative_to(L.parent/'work/rows_slices'))
    for kind,c in family['response_kinds'].items():
        p(f'| {name} | {kind} | {c["bound"]} | {c["checked"]} | {c["identical"]} | {c["different"]} | {c["blocked"]} | {evidence("proofs/parity/BYTE_PARITY.json")} |')
p()
p('## EAT-1 clauses')
p()
p('These are the harness verdicts, not product acceptance. All final reports have claim_grade=false. The native adapters use the tiny native model fixtures and a registered scripted LM policy; GF-1 uses the tiny frozen tower plus seeded fusion-weight noise. b04 uses its supplied trained heads and captured tower-boundary fixture outputs with a generated tiny LM. Real pretrained RGB inference and deployed GPU towers were not checked. Sources: '+evidence('EAT1_SUMMARY.json')+', '+evidence('b04_artifact10.py')+', '+evidence('proofs/eat1/b04/MOUNTS.json')+'.')
p()
p('| Reader | Clause | Result | Evidence and finding |')
p('|---|---|---|---|')
for name in ('gf1','c8r','b04'):
    for clause,r in eat[name]['clauses'].items():
        p(f'| {name} | {clause} | {r["status"]} | {r["summary"].replace("|","/")}; '+evidence(f'proofs/eat1/{name}/run/EAT1_REPORT.json')+' |')
p()
p('The b04 adapter is the staged `eat1_adapter/b04_tiny.py` from the supplied b04 code, not the harness toy adapter. The supplied later settings/manifests were read as evidence; they do not authorize changing the sealed validator. Its validator check fails before routed output. The raw item errors and original b04 report are linked in '+evidence('EAT1_GROUP_EVIDENCE.json')+'. A lower finding count after an early error or a harness-version change is not an improvement claim.')
p('Verification of the b04 artifact requires its recorded read-only head-file mounts. `work/build10/launch_b04_local10.py` reconstructs those mounts from the supplied inputs; the proof folder retains mount placeholders. Source: '+evidence('proofs/eat1/b04/MOUNTS.json')+'.')
p()
p('The static A4 blockers remain below. Accounting literals remain reported as well; this build adds no suppression for them. Dynamic reader errors are listed separately. Source: '+evidence('EAT1_GROUP_EVIDENCE.json')+'.')
p()
p('| Reader | A4 blocker | File:line | Detail |')
p('|---|---|---|---|')
for name in ('gf1','c8r','b04'):
    for values in groups[name]['groups'].values():
        for row in values:
            if row['clause']!='A4' or not row.get('file'):continue
            file=Path(row['file'])
            label=str(file.relative_to(L)) if file.is_relative_to(L) else str(file)
            p(f'| {name} | {row.get("rule","A4")} | `{label}:{row.get("line",1)}` | {row.get("detail","").replace("|","/")} |')
p()
p('The unchanged b04 `reader_contract` compiles a pinned geometry validator with its terminal up-axis check omitted. These routed items stop at the preceding hash check. This existing behavior remains for the acceptance review; it was not changed here. Source: `work/build10/b04_stage/e2e_reader/geometry.py:23`.')
pin=read('B04_VALIDATOR_PIN.json')
p(f'The b04 validator expects `{pin["expected"]}` and reads `{pin["actual"]}`. The current validator file is byte-identical to build 9fix. Source: '+evidence('B04_VALIDATOR_PIN.json')+'.')
p()
p('| Reader | Error | Items | Evidence |')
p('|---|---|---:|---|')
for name in ('gf1','c8r','b04'):
    for err,count in groups[name].get('errors',{}).items():p(f'| {name} | {err} | {count} | '+evidence(f'proofs/eat1/{name}/run/ITEMS.jsonl')+' |')
p()
p('Before/after findings below count reported offender records grouped by source function/file. They are a review index, not a normalized metric. Native “before” uses the older build 8 harness; b04 “before” uses its own v9 report. G8 changes the claim checker rather than a product call-path group. Source: '+evidence('EAT1_GROUP_EVIDENCE.json')+'.')
p()
p('| Reader | Group | Before A3 / A4 | After A3 / A4 | Evidence |')
p('|---|---|---|---|---|')
for name in ('gf1','c8r','b04'):
    for group in ['G1','G2','G3','G4','G5','G6','G7','Other / expanded v7 scope']:
        a=groups[name+'_before']['counts'].get(group,{});b=groups[name]['counts'].get(group,{})
        p(f'| {name} | {group} | {a.get("A3",0)} / {a.get("A4",0)} | {b.get("A3",0)} / {b.get("A4",0)} | '+evidence('EAT1_GROUP_EVIDENCE.json')+' |')
p()
p('Only these b04 source lines changed; all other staged source bytes match their recorded source hashes. TOK, SCALE and SELECTOR derive from DATA. Source: '+evidence('B04_STAGING.json')+'.')
p()
for row in read('B04_STAGING.json')['changed_lines']:
    p(f'- `{row["file"]}:{row["line"]}`: `{row["before"]}` → `{row["after"]}`.')
p()
p('## Suites and CPU proof')
p()
p('| Suite | Run | Passed | Pre-existing failure events | Regression events | R2 failure events | Evidence |')
p('|---|---:|---:|---:|---:|---:|---|')
passed=sum(v['outcome']=='passed' for v in packet.values())
p(f'| Packet | {len(packet)} | {passed} | 0 | {len(packet)-passed} | 0 | '+evidence('proofs/packet/results.json')+' |')
p(f'| Frozen tree versus base | {comparison["run"]} | {comparison["passed"]} | {comparison["preexisting"]} | {comparison["regressions"]} | {comparison["r2_failures"]} | '+evidence('SUITE_COMPARISON.json')+' |')
base_result=read('proofs/suite_base/results.json')
p(f'| Untouched base | {base_result["tests"]} | {len(base_result["passed"])} | See paired classification | Not applicable | Not applicable | '+evidence('proofs/suite_base/results.json')+' |')
p()
p('Run/pass counts retain scheduled executions. Failure counts include subtests and import/setup errors and need not sum to the execution count. A failure is pre-existing only when the paired base cause matches or the unchanged unsupported-reader guard is authenticated. Sources: '+evidence('SUITE_COMPARISON.json')+', '+evidence('LEGACY_GUARDS.json')+'.')
p('The comparison matches normalized cause categories for each test; its receipt retains both raw traces so the reviewer can inspect that classification. Source: '+evidence('compare.py')+'.')
for r in comparison['failures']:
    if not r['preexisting']:p('- Regression event: `'+r['test']+'`: '+r['cause']+'. Source: '+evidence('SUITE_COMPARISON.json')+'.')
p()
p('Completed suite groups retain source/fixture/runner/input hash receipts. The initial inherited receipts were not reused across changed source or runner hashes. Final qualification reruns the complete changed test modules from the final archive and reuses only unchanged test bodies, production source, fixtures, runner and bound inputs. The repaired parity methods use a valid turn call; the dedicated refusal tests and C8r invalid-frame input remain. Sources: '+evidence('RESUME_AUDIT.json')+', '+evidence('proofs/fixture_requalification/RESUME_RECEIPT.json')+', '+evidence('proofs/package/ARCHIVE.json')+'.')
cpu=read('proofs/forward/RESULT.json')
p()
p(f'The CPU producer-to-reader proof is {cpu["status"]}: loss {cpu["loss"]}, supervised tokens {cpu["supervised_tokens"]}, nonzero finite gradient tensors {cpu["nonzero_finite_gradient_tensors"]}. '+cpu['standins']+' '+cpu['limitations']+' Source: '+evidence('proofs/forward/RESULT.json')+'.')
p()
p('## Changed-statement coverage')
p()
p('Production coverage compares AST statement heads with the untouched base and requires standard-library monitoring, a compiled-code fingerprint and the exact current file SHA. Prior observations count only for byte-identical files. Unobserved CPU statements remain gaps; blocked host/GPU paths are not counted as covered. Source: '+evidence('CHANGED_COVERAGE.json')+'.')
p()
p('| Scope / class | Statements | Evidence |')
p('|---|---:|---|')
for cls,count in coverage['classes'].items():p(f'| Production / {cls} | {count} | '+evidence('CHANGED_COVERAGE.json')+' |')
for cls,count in hcoverage['classes'].items():p(f'| Harness / {cls} | {count} | '+evidence('HARNESS_COVERAGE.json')+' |')
p()
p('Incremental source coverage below isolates this build from inherited changes. Shared files support several groups; the source-file table avoids double-counting them. JSON configuration bytes are hash-bound, not Python statements. Source: '+evidence('INCREMENTAL_COVERAGE.json')+'.')
p()
p('| Changed source file | Observed | Unobserved by class | Evidence |')
p('|---|---:|---|---|')
for file,counts in read('INCREMENTAL_COVERAGE.json')['by_file'].items():
    rest=', '.join(f'{k}: {v}' for k,v in counts.items() if k!='observed') or 'None'
    p(f'| {file} | {counts.get("observed",0)} | {rest} | '+evidence('INCREMENTAL_COVERAGE.json')+' |')
p()
p('Harness coverage uses exact-file-hash matched line observations and reports its weaker measurement method separately. The original complete harness test log retains the denied syscall-witness failure. The executable subset runs without retrying that operation. Sources: '+evidence('HARNESS_COVERAGE.json')+', '+evidence('proofs/g8/test.log')+', '+evidence('proofs/g8_available/RESULT.json')+'.')
p()
p('## Blockers carried forward')
p()
blockers=sorted({x for value in kits.values() if isinstance(value,dict) for x in value.get('blockers',[])})
for name in blockers:p('- `'+name+'`. Source: '+evidence('KIT_RESULT.json')+'.')
for text in [
    'BOUND_NUMERIC_INPUTS_MISSING: no bound producer pose/depth/FoV inputs; the real-row parity gate is unpassed.',
    'READOUT_MIGRATION_INCOMPLETE: point-depth helpers, legacy branches, public transforms and calculator precision remain outside the requested complete migration.',
    'B04_SEALED_VALIDATE_MISMATCH: the staged validator pin rejects tool-bearing items; no b04 source change beyond paths is authorized.',
    'STATUS_OWNER_MISSING: existing statuses without a registered head output remain A4 blockers, with exact file:line records in the EAT evidence.',
    'NATIVE_CALL_ATTRIBUTION_FAILED: response injection remains outside forward, and the tiny tokenizer cannot faithfully report its numeric call text.',
    'STRACE_WITNESS_UNAVAILABLE: PTRACE_TRACEME is denied; claim-grade acceptance is unavailable.',
    'FULL_STORE_DIVISION_UNPROVED: inherited full VQA census, native full-store build and complete post-filter allocation proofs remain absent.',
    'ORIGINAL_ADMISSION_COUNTS_UNESTABLISHED: inherited baseline count discrepancies remain; the repaired full-extent gate stays enabled.',
    'PRODUCTION_INFERENCE_CLOSURE_UNPROVED: dynamic dispatch and external dependencies have not been exhaustively qualified.']:
    p('- '+text+' Sources: '+evidence('DECISIONS.md')+', '+evidence('EAT1_GROUP_EVIDENCE.json')+', '+evidence('N1_CARRIED_BLOCKERS.json')+', `../w9f/out/BUILD9FIX_REPORT.md`.')
if coverage['classes'].get('CPU-reachable unresolved',0):p('- CPU_COVERAGE_GAPS: every unresolved source statement is listed in '+evidence('GAPS.json')+'.')
p()
p('No launch, network, Orchard/GCS call or GPU execution was performed. No real pretrained or full-store acceptance is claimed. Full dense-scene reconstruction, complete parent overlap, all frame-count readers, independent review and deployed inference were not checked. The workspace and temporary-folder sizes were measured; the total size of other lane workspaces was not measured. Source: '+evidence('STORAGE.json')+'.')
p()
p('## Product inference components outside the weights')
p()
p('These are the known direct components relevant to acceptance. The appendix also lists the conservative local import inventory at file:line. That inventory includes support/training imports and cannot certify dynamic or external closure. Existing selectors and policies listed here were not added by this build. Source: '+evidence('proofs/audit/INFERENCE_COMPONENTS.json')+'.')
p()
p('| Component | Source | Operation |')
p('|---|---|---|')
for r in inventory['known_outside_forward']:
    description=r['operation']
    if r['component']=='OwnGeometry.pose':description='Builds public geometry outside forward; the serving callback delegates yaw to the registered module, while the legacy branch still computes it here.'
    p(f'| {r["component"]} | `work/tree_r1/{r["file"]}:{r["line"]}` | {description} |')
p()
p('## For the review')
p()
for text in [
    'Review G5/G7 refusals: call/response budgets and out-of-range frames raise without injected substitute text. Other error/status substitutions remain findings. Check these changes against the intended admission and serving contract.',
    'Review the G8 claim-test patch: registration, zero parameters, manifest input/output declarations, persistent buffer matching, artifact-file hashing and live-buffer equality. The scanner, syscall witness and failed clauses were not suppressed.',
    'Review native adapter manifest declarations, including fixed_math buffers, config files and tower source files. The toy registered LM program remains a fixture stand-in; it is not product evidence.',
    'Review the A5 sandbox mount change: it mounts each exact SHA-authenticated artifact file, including declared external config paths. It adds no parent directory mount or scanner exemption. The manifest/sandbox test checks that an external file is visible without its parent directory. Sources: work/build10/eat1/run.py, work/build10/test_adapter_manifest10.py.',
    'Review b04 assembly separately from b04 source: the original trained head files are mounted read-only; tiny LM and captured tower-boundary fixtures are built locally. Only the listed path constants change b04 source.',
    'Review the updated tests for explicit budget and bad-frame refusal, and the tower-manifest assertion. They reflect intentional behavior changes; the unchanged base comparison remains separate.',
    'Recheck inherited semantic status authentication, RECOVERY_ROWS_ABSENT / UNIT_ROWS_ABSENT refusals, exact mix bytes, full-extent admission, removal-list division and all sealed scene exclusions. None receives a new exemption.',
    'No answer selector, rule table, response fallback or new suppression was added. The ground_route compatibility alias retains the existing fallback field and remains visible to the scanner.',
    'Do not approve A2 from b04’s PASS alone: its routed items fail before the intended response path. Do not approve row parity from zero checked bound responses.',
]:p('- '+text)
p()
p('Review sources: `out/EAT1_FIXED_MATH.patch`, `out/TREE.diff`, '+evidence('B04_STAGING.json')+', '+evidence('EAT1_GROUP_EVIDENCE.json')+', '+evidence('FINAL_BINDING_AUDIT.json')+', '+evidence('KIT_METADATA_REPAIR.json')+'.')
p()
p('## Local component inventory appendix')
p()
p('Each entry is `component@line` within the named file. This is the conservative inventory, not a claim that every listed function runs in production. Source and full classifications: '+evidence('proofs/audit/INFERENCE_COMPONENTS.json')+'.')
p()
byfile=defaultdict(list)
for r in inventory['components']:byfile[r['file']].append(r)
for file,components in sorted(byfile.items()):p('- `work/tree_r1/'+file+'`: '+', '.join('`'+r['component']+'@'+str(r['line'])+'`' for r in components)+'.')
p()
p('The staged b04 source inventory follows. It includes fixture/training support; the validator refusal prevents a complete dynamic product-path claim. Source: '+evidence('proofs/audit/B04_COMPONENTS.json')+'.')
p()
byfile=defaultdict(list)
for r in read('proofs/audit/B04_COMPONENTS.json')['components']:byfile[r['file']].append(r)
for file,components in sorted(byfile.items()):p('- `work/build10/b04_stage/'+file+'`: '+', '.join('`'+r['component']+'@'+str(r['line'])+'`' for r in components)+'.')
(L/'out/BUILD10_REPORT.md').write_text('\n'.join(out)+'\n')
record=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md';prior=record.read_text();marker='\n## Build 10\n'
section=(marker+'\nThe candidate registers depth and heading readouts, binds their buffers and source manifests, and refuses incomplete calls without truncation. It remains GO=false: bound-row raw inputs are missing, the migration is partial, and b04 refuses its sealed validator. The observed A2 pass is not acceptance.\n\n'
    f'Tree seal: `{delivery["tree_seal"]}` (`out/TREE_SEAL.json`). Archive SHA256: `{delivery["sha256"]}` (`work/build10/DELIVERY.json`). Full results, limitations, parity counts, clause tables and review changes: `out/BUILD10_REPORT.md`.\n')
if marker in prior:prior=prior.split(marker)[0]
record.write_text(prior.rstrip()+'\n'+section)
print('Wrote BUILD10_REPORT.md and the Build 10 design record section.')
