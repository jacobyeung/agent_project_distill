"""Write the final review report from authenticated proof receipts."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';O=L/'out'
def read(path):return json.loads((L/path).read_text())
def local(path):return str(Path(path).relative_to(L)) if str(path).startswith(str(L)+'/') else str(path)
def code(value):return '`'+str(value)+'`'
def refs(*paths):return '; '.join(code(local(p)) for p in paths)
gate=read('work/build9/LOCAL_REPAIR_GATE.json');seal=read('out/TREE_SEAL.json');delivery=read('work/build9/DELIVERY.json')
comparison=read('work/build9/SUITE_COMPARISON.json');coverage=read('work/build9/CHANGED_COVERAGE.json')
packet=read('work/build9/proofs/packet/results.json');tree=read('work/build9/proofs/suite_tree/results.json');base=read('work/build9/proofs/suite_base/results.json')
rows=read('work/build9/proofs/row_counts/RESULT.json');mixes=read('work/build9/proofs/row_counts/MIX_BOUND.json')
admission=read('work/build9/proofs/recovery/recovery_rows/RESULT.json');stop=read('work/build9/proofs/stop_multirank/AUDIT.json')
verification=read('work/build9/FINAL_VERIFICATION.json');blockers=read('work/build9/CARRIED_BLOCKERS.json')
inventory=read('work/build9/proofs/audit/INFERENCE_COMPONENTS.json');kits=read('work/build9/proofs/review/KIT_READCHECK.json')
eat={name:read(f'work/build9/proofs/eat1/{name}/run/EAT1_REPORT.json') for name in ('c8r','gf1')}
lines=[]
def put(text=''):lines.append(text)
put('# Build 9 — review package; GO=false')
put('\nThe failure-status text gate and faithful identity delimiter defect are repaired. Recovery and unit input checks are installed. The local repair gate is '+code(gate['status'])+' ('+refs('work/build9/LOCAL_REPAIR_GATE.json')+'). Production acceptance remains blocked by the inputs and findings below.')
put('\nFull admission of every published slice row is blocked by the unchanged sealed scene exclusions. The text gate and training reader pass the requested slice counts; full intake retains the excluded rows as refusals. The proof uses explicit fixture form/head bindings and metadata-only RGB pins. It does not qualify production head ownership, independent scene coverage or row-store bindings ('+refs('work/build9/proofs/recovery/recovery_rows/RESULT.json','work/build9/DECISIONS.md')+').')
put('\nThe source seal is '+code(seal['tree_sha256'])+' ('+refs('out/TREE_SEAL.json')+'). The base-relative diff and inventory are '+refs('out/TREE.diff','out/TREE_FILES.sha256')+'.')
put('\nThe package is '+code(delivery['path'])+', '+str(delivery['bytes'])+' bytes, SHA256 '+code(delivery['sha256'])+' ('+refs('work/build9/DELIVERY.json')+').')
put('\n| Item | Disposition | Result or named missing input | Evidence |\n|---|---|---|---|')
items=[
('1','Closed text gate/reader; blocked full-intake target','Status assertions outside complete tool responses still refuse. Other text/provenance patterns retain their scope. BOUND_SLICE_SEALED_SCENE_EXCLUSIONS prevents all-row full admission; metadata fixture bindings do not close D3.','work/build9/proofs/recovery/recovery_rows/RESULT.json'),
('2','Closed bounded census and input gate','RECOVERY_ROWS_ABSENT refuses missing populations or a zero recovery mix. No non-simulated status was found in the bound slices; no real rows were fabricated.','work/build9/proofs/row_counts/RESULT.json; work/build9/proofs/requirements/results.json'),
('2a','Closed bounded conversion audit and input gate','Each bound unit row has one written conversion from its printed metres. UNIT_ROWS_ABSENT refuses a zero population for any required unit or a zero unit mix. Full-store unit marginals remain missing with D3.','work/build9/proofs/row_counts/RESULT.json; work/build9/proofs/requirements/results.json'),
('3a','Closed delimiter defect; production blocked','Native camera identity preserves admitted target bytes; wrong answers and decision results still refuse. BOUND_FAITHFUL_IDENTITY_RECEIPT_MISSING keeps faithful kit training disabled.','work/build9/proofs/identity/IDENTITY.json; work/build9/proofs/identity/PREPARATION.json'),
('3b','Closed on authenticated lane evidence' if not stop['rerun_required'] else 'Lane rerun required','Production constructors bind the trace version before checkpointing. '+('The supplied stop driver exercised unchanged source; no rerun was performed.' if not stop['rerun_required'] else 'Run work/build9/proofs/stop_multirank/RUN.sh on the lane.'),'work/build9/proofs/stop_multirank/AUDIT.json'),
('3c','Blocked; unchanged scope','Every requested acceptance/input blocker is carried below. No inference formatter, selector, fallback, threshold or in-forward hook was added.','work/build9/CARRIED_BLOCKERS.json'),
('3d',gate['status'],'The gate requires complete suites, no unexpected regression, no R2 failure, and no CPU-reachable statement gap. The retained BF16 event remains explicit.','work/build9/LOCAL_REPAIR_GATE.json'),
('4','Closed frozen pass','Both kits staged from empty, A2 first, with GO=false. Packet, frozen package, base comparison, changed-statement coverage and EAT checks completed.','work/build9/FINAL_PASS.json; work/build9/FINAL_VERIFICATION.json')]
for item in items:put('| '+' | '.join(item)+' |')
put('\n## Recovery admission and status counts')
put('\n| Family | Published rows read | Text gate admitted | b7 reader admitted | Full intake with fixture bindings | Retained scene refusals | Evidence |\n|---|---:|---:|---:|---:|---:|---|')
for name,v in admission['families'].items():
    c=v['counts'];put(f"| {name} | {c['read']} | {c['text_admitted']} | {c['reader']} | {c['admitted']} | {sum(v['refusals'].values())} | `work/build9/proofs/recovery/recovery_rows/{name}/RESULT.json` |")
put('\nThe full-intake refusals above are sealed eval-room matches. All published slice files and their trace targets remain unchanged. The native negative proof appends a model-authored “not seen” assertion and verifies that the reader refuses it. Unclosed responses and delimiters split across fields do not exempt a status ('+refs('work/build9/proofs/recovery/results.json','work/tree_r1/tests/test_r2_build9_recovery.py')+').')
put('\nThe status columns below count rows, with simulated / not-simulated counts in each cell. The census reads the printed responses and `ground_record.events[].audit.simulated`; event counts are also retained in the JSON receipt. Final A0 slices replace their older copies. Missing simulation flags are distinguished from explicit false values in the receipt. No non-simulated failure status was found in this scope ('+refs('work/build9/proofs/row_counts/RESULT.json')+').')
put('\n| Family | Rows read | not seen: simulated / not | unresolved: simulated / not | box unavailable: simulated / not | Source |\n|---|---:|---:|---:|---:|---|')
for name,v in rows['families'].items():
    values=[str(v['status_rows'][s]['simulated'])+' / '+str(v['status_rows'][s]['not_simulated']) for s in ('not seen','unresolved','box unavailable')]
    put('| '+' | '.join([name,str(v['counts']['rows']),*values,code(v['source'])+'; `work/build9/proofs/row_counts/RESULT.json`'])+' |')
put('\n## Units and routing expectations')
put('\n| Unit | Bound rows | Rows after sealed exclusions | Valid written conversions | Evidence |\n|---|---:|---:|---:|---|')
unit=rows['families']['a0_units']
for u in ('cm','ft','in'):put(f"| {u} | {unit['units'][u]} | {unit['units_after_exclusions'][u]} | {unit['units'][u]} | `work/rows_slices/slices_final/a0_units.jsonl`; `work/build9/proofs/row_counts/RESULT.json` |")
put('\nInvalid conversion lines or unconverted metre answers: '+str(unit['counts'].get('unit_rows_invalid',0))+' ('+refs('work/build9/proofs/row_counts/RESULT.json')+'). The audit checks the question unit, printed metric operand, conversion constant, arithmetic, and final answer. It performs no reader-side or answer-side conversion.')
put('\n| Kit | Recovery rows/step, ideal | Recovery draws/step, registered allocation | Recovery simulated / not, ideal | Unit rows/step, ideal | cm / ft / in per step, published slice | cm / ft / in per step, retained slice | Evidence |\n|---|---:|---:|---:|---:|---|---|---|')
for arm,v in mixes.items():
    e=v['conditional_expected'];before=' / '.join(f"{e['unit_rows_per_step'][u]:.6f}" for u in ('cm','ft','in'));after=' / '.join(f"{e['unit_rows_per_step_after_exclusions'][u]:.6f}" for u in ('cm','ft','in'))
    put(f"| {arm.upper()} | {e['recovery_rows_per_step']:.6f} | {e['recovery_draws_per_step']:.6f} | {e['recovery_simulated_per_step']:.6f} / {e['recovery_not_simulated_per_step']:.6f} | {e['units_rows_per_step']:.6f} | {before} | {after} | `work/build9/proofs/row_counts/MIX_BOUND.json`; `out/MIX_A0.json` |")
put('\nThese are conditional expectations from the existing mix and measured slice proportions. The full-population file does not provide unit marginals, and D3 remains unbound. They are not measured production sampling rates. The kit audit confirms that both staged mixes match the supplied allocation and bind the post-exclusion slice counts. Baseline benchmark error rates did not select a quota, threshold or quantity ('+refs('work/rows_slices/slices_final/COUNTS_A0_v4.json','work/build9/proofs/row_counts/MIX_BOUND.json')+').')
put('\n## Suites and coverage')
put('\n| Suite | Run | Passed | Pre-existing failure events | Regression events | R2 failures | Skipped | Evidence |\n|---|---:|---:|---:|---:|---:|---:|---|')
put(f"| Packet | {len(packet)} | {sum(v['outcome']=='passed' for v in packet.values())} | 0 | {sum(v['outcome']!='passed' for v in packet.values())} | Not applicable | 0 | `work/build9/proofs/packet/results.json` |")
put('| Frozen package | '+' | '.join(str(comparison[k]) for k in ('run','passed','preexisting','regressions','r2_failures','skipped'))+' | `work/build9/SUITE_COMPARISON.json` |')
put(f"| Base reference | {base['tests']} | {len(base['passed'])} | {len(base['failures'])+len(base['errors'])} | Not applicable | Not applicable | {len(base['skips'])} | `work/build9/proofs/suite_base/results.json` |")
put('\nTest executions and failure events use the inherited counting rules; multiple subtests can create multiple events. Unchanged base groups resume only with matching source, fixture and runner hashes. The frozen R2 group additionally pins the read-only real slices supplied beside the archive. Those external slice inputs are not a claim of full-store portability ('+refs('work/build9/proofs/package/RESULTS.json','work/build9/proofs/suite_base','work/build9/proofs/suite_tree/r2/GROUP_RECEIPT.json')+').')
put('\nSome legacy tests exceed the temporary-storage cap during execution. The unchanged harness records these as errors, compacts its own scratch products, and checks the cap again before the next test. These are refusals, not passing storage proofs. Per-group maxima and every affected test appear in '+refs('work/build9/STORAGE_AUDIT.json')+'; the base comparison determines whether each failure event is pre-existing.')
put('\n| Changed-statement class | Count | Evidence |\n|---|---:|---|')
for kind in ('observed','CPU-reachable unresolved','GPU','frame-host','model-loader'):
    put(f"| {kind} | {coverage['classes'].get(kind,0)} | `work/build9/CHANGED_COVERAGE.json` |")
put('\nCoverage measures changed production AST statement heads against the untouched base with standard-library monitoring; the inherited harness excludes test bodies. A hit is accepted only when its executed code fingerprint and whole-file hash match current source. CPU-reachable gaps remain gaps; a missing production input is not a pass ('+refs('work/build9/CHANGED_COVERAGE.json','work/build9/GAPS.json','work/build9/coverage.py')+').')
put('\nThe native CPU proof runs the real row producer, admission, SQLite reader, RGB encoder, response masking and model forward. Synthetic RGB and failure events are inputs. Tiny native model/head weights and a lossless tokenizer/processor stand in at the unavailable pretrained/GPU model boundary. The weighted proof uses the native final training recipe and checks positive routing loss. This is a training-path proof; deployed frozen towers and product closure remain unqualified ('+refs('work/build9/proofs/cpu_weighted/RGB.json','work/build9/proofs/cpu_weighted/results.json')+').')
put('\nThe supplied stop proof passes signal and fallback cases, including checkpoint, export and reload. Its receipt hash and exercised-source comparison are recorded in the audit. The static construction audit covers both rank branches, D0/H1 and resume paths. It does not run the production allocation wrapper ('+refs('work/lane_stop2/proofs/stop_multirank/RESULT.json','work/build9/proofs/stop_multirank/AUDIT.json')+').')
put('\n## Kits and EAT-1')
put('\n| Kit | SHA256 | State | Evidence |\n|---|---|---|---|')
for k in kits:put('| '+k['arm'].upper()+' | '+code(k['kit_sha256'])+' | GO=false; CLEAN | `work/build9/proofs/review/KIT_READCHECK.json` |')
put('\nThe inherited scale weight remains labelled GUESS. No production processor value, init, dense manifest or store was invented. The kit source archives and job-visible records pass the existing scanner ('+refs('work/build9/build_kits.py','work/build9/proofs/review/KIT_READCHECK.json','work/build9/proofs/package/KIT_TESTS.json')+').')
put('\n| EAT-1 clause | C8r tiny reader | GF-1 tiny reader | Evidence |\n|---|---|---|---|')
for clause in ('A1','A2','A3','A4','A5'):
    put('| '+clause+' | '+eat['c8r']['clauses'][clause]['status']+' | '+eat['gf1']['clauses'][clause]['status']+' | `work/build9/proofs/eat1/c8r/run/EAT1_REPORT.json`; `work/build9/proofs/eat1/gf1/run/EAT1_REPORT.json` |')
put('\nStatic scan: '+refs('work/build9/proofs/eat1/SCAN_READ.json')+'. Tiny acceptance adapters use seeded native tower/model stand-ins and scripted call tokens. Their results do not qualify a trained production artifact. The outside-forward response construction and required reader hook remain out of scope.')
put('\n## Carried blockers')
put('\n| Blocker | Disposition | Evidence |\n|---|---|---|')
for r in blockers:put('| '+r['blocker']+' | '+r['disposition']+' | '+code(r['evidence'])+' |')
put('\nBF16 keeps its original assertion and tolerance; enabled BF16 remains refused. Portrait share remains unknown. Faithful identity is proved only on the CPU fixture, not the missing production-bound store. All other retained blockers keep the build-8 evidence listed above ('+refs('out/BUILD8_REPORT.md','work/build9/CARRIED_BLOCKERS.json')+').')
put('\n## For the second review')
put('\n- Independently review the admission change in `student_pilot/row_text_audit.py`: only complete tool-response spans exempt failure statuses; model-authored statuses still refuse. Review the explicit unresolved-status coverage, malformed delimiters and unchanged other patterns. This review is required by `work/design/20261117T0655Z_ORCH_ANSWER_recovery_gate.md`.')
put('- Keep the distinction between text-gate counts, the b7 reader, fixture form/head bindings and full intake. Resolve the sealed scene conflicts with the rows lane; do not bypass exclusions or treat unknown overlap as a pass (`work/build9/proofs/recovery/recovery_rows/RESULT.json`).')
put('- Review the required-family launch checks and the conditional mix accounting. The next production leg still needs store-bound recovery and per-unit counts; no real failure status was found in the inspected slices (`work/build9/proofs/row_counts/RESULT.json`, `work/build9/proofs/row_counts/MIX_BOUND.json`).')
put('- Review faithful envelope preservation and the existing disagreement metric without changing thresholds. Keep faithful training disabled until the production-bound identity receipt exists (`work/build9/proofs/identity/IDENTITY.json`).')
put('- Accept the supplied stop receipt only with its source comparison. No current exercised source changed; the prepared rerun script is available if those sources change (`work/build9/proofs/stop_multirank/AUDIT.json`, `work/build9/proofs/stop_multirank/RUN.sh`).')
put('- Let lane b03_e2etest judge the outside-weight components below. This build adds training-input checks and a training-label fix; it does not claim an in-forward inference implementation (`work/build9/proofs/audit/INFERENCE_COMPONENTS.json`).')
put('\nNot checked: independent review; full store/frame/cache inventories; independent full scene-overlap coverage; deployed real-failure caches; production per-unit marginals; production init and processor pins; full encoder parity; portrait population share and coordinate parity; production allocation wrapper; GPU execution or timing; complete trained-model EAT acceptance. No launch, remote service call, SSH, Git, GPU, or other agent was used.')
put('\nMeasured storage: lane '+str(verification['storage_bytes']['lane'])+' bytes; temporary folder '+str(verification['storage_bytes']['tmp'])+' bytes; scratch free '+str(verification['scratch_free_bytes'])+' bytes ('+refs('work/build9/FINAL_VERIFICATION.json')+').')
put('\n## Outside-weight inference inventory')
put('\nThe following known operations remain outside forward. The conservative import inventory that follows also includes support and training functions whose dynamic reachability is unproved. It identifies review locations; it does not establish that every method runs outside weights or that external/dynamic dependencies are complete ('+refs('work/build9/proofs/audit/INFERENCE_COMPONENTS.json')+').')
put('\n| File:line | Operation |\n|---|---|')
for r in inventory['known_outside_forward']:put('| '+code(r['file']+':'+str(r['line']))+' | '+r['operation']+' |')
put('\n<details>\n<summary>Conservative inference import inventory</summary>\n\n| File:line | Component | Classification |\n|---|---|---|')
for r in inventory['components']:put('| '+code(r['file']+':'+str(r['line']))+' | '+code(r['component'])+' | '+r['classification']+' |')
put('\n</details>\n')
(O/'BUILD9_REPORT.md').write_text('\n'.join(lines))
design=O/'DESIGN_RECORD_tree_rebuild_20261115.md';existing=design.read_text();marker='\n## Build 9\n'
section='''
## Build 9

The status audit admits printed head failures while refusing model-authored status assertions. The faithful materializer preserves admitted answer envelopes, and genuine decision mismatches still refuse. Kit input checks require recovery rows and every requested conversion unit. The bounded census finds only simulated failure statuses; unit traces preserve printed-metre arithmetic. Full intake retains sealed eval-room refusals, so all-row full admission remains blocked. Production store, head and full-population unit bindings remain missing.

The supplied lane stop proof is authenticated against unchanged exercised sources. Both kits remain GO=false. The complete outcomes, counts, source/package/kit hashes, coverage classes, EAT clauses, retained blockers and required independent admission review appear in `out/BUILD9_REPORT.md`. The local repair gate is '''+code(gate['status'])+' (`work/build9/LOCAL_REPAIR_GATE.json`).\n'
design.write_text(existing.split(marker)[0]+section if marker in existing else existing+section)
(B/'STATUS.md').write_text('# Build 9 status\n\nFinal delivery complete; GO=false. Local repair gate: '+gate['status']+'.\n\nThe status gate, bounded recovery/unit accounting and faithful delimiter repair are complete. Full-intake all-row admission remains blocked by preserved sealed scene exclusions. Production and acceptance blockers remain in `out/BUILD9_REPORT.md`.\n\nEvidence: `work/build9/LOCAL_REPAIR_GATE.json`, `work/build9/FINAL_PASS.json`, `work/build9/FINAL_VERIFICATION.json`, `work/build9/SUITE_COMPARISON.json`, `work/build9/CHANGED_COVERAGE.json`.\n')
print(json.dumps(dict(report='out/BUILD9_REPORT.md',gate=gate['status'],seal=seal['tree_sha256'],package=delivery['path'])))
