"""Publish source-backed results and preserve every unresolved acceptance input."""
import collections,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8';O=L/'out'
def read(name,default=None):
 p=L/name
 return json.loads(p.read_text()) if p.exists() else default
def tick(x):return '`'+str(x)+'`'
seal=read('out/TREE_SEAL.json',{});delivery=read('work/build8/DELIVERY.json',{})
comparison=read('work/build8/SUITE_COMPARISON.json',{})
coverage=read('work/build8/CHANGED_COVERAGE.json',{})
packet=read('work/build8/proofs/packet/results.json',{})
tree=read('work/build8/proofs/suite_tree/results.json',{})
base=read('work/build8/proofs/suite_base/results.json',{})
kits=read('work/build8/proofs/review/KIT_READCHECK.json',[])
stop=read('work/build8/proofs/stop_multirank/RESULT.json',{})
gaps=coverage.get('classes',{}).get('CPU-reachable unresolved',0) if coverage else 'pending'
report=[]
def put(s=''):report.append(s)
put('# Build 8 — review package; GO=false')
put('\nThe local fixture regressions and legacy direct-source path are repaired. Frame-count propagation has native CPU proofs, and the portrait audit records each transform. BF16 parity, production inputs, distributed stop evidence and the in-forward reader work remain blockers. The final suite and coverage results below determine the validation status; a completed harness does not imply product acceptance.')
put('\nThe source seal is '+tick(seal.get('tree_sha256','pending'))+' (`out/TREE_SEAL.json`). The base-relative diff and inventory are `out/TREE.diff` and `out/TREE_FILES.sha256`.')
put('\nThe package is '+tick(delivery.get('path','pending'))+', '+str(delivery.get('bytes','pending'))+' bytes, SHA256 '+tick(delivery.get('sha256','pending'))+' (`work/build8/DELIVERY.json`).')
put('\n| Requested item | Status | Result or missing input | Evidence |\n|---|---|---|---|')
items=[
('1','Blocked: BF16_CACHE_GRADIENT_PARITY','The tokenizer, staging-pin and runtime-file fixtures are repaired. The original BF16 gradient assertion remains unchanged and failing; enabled BF16 remains refused.','work/build8/proofs/regressions/DISPOSITION.json; work/build8/proofs/regressions/BF16_PARITY.json; work/build8/SUITE_COMPARISON.json'),
('2','Closed' if comparison.get('r2_failures')==0 else 'Blocked: R2_FAILURES','Final R2 failure events: '+str(comparison.get('r2_failures','pending'))+'.','work/build8/SUITE_COMPARISON.json; work/build8/proofs/suite_tree/r2/results.json'),
('3','Closed locally' if gaps==0 else 'Blocked: CPU_STATEMENT_GAPS','CPU-reachable unresolved statement heads: '+str(gaps)+'. External-only classifications retain their source evidence.','work/build8/CHANGED_COVERAGE.json; work/build8/GAPS.json; work/build8/proofs/final_repairs/results.json; work/build8/proofs/final_repairs/CACHE_CLI.json; work/build8/proofs/final_repairs/CACHE_READER.json; work/build8/proofs/final_repairs/CACHE_ROW.json; work/build8/proofs/final_repairs/PREPARATION.json'),
('4','Closed' if stop.get('status')=='PASS' else 'Blocked: MULTIRANK_STOP_UNPROVED','The sandbox attempt refused socket creation. A separate lane receipt reached the first step but failed signal forwarding because the helper path was wrong. The prepared driver repairs that path and resets stale markers; it has not been rerun here. No completed end slot or artifact hash exists. Lane runs RUN.sh after build 8.','work/build8/proofs/stop_multirank/RUN.sh; work/build8/proofs/stop_multirank/RESULT.codex_sandbox.json; work/build8/proofs/stop_multirank/RESULT.json; work/build8/proofs/stop_multirank/DRIVER_PINS.json'),
('5','Closed locally; blocked full qualification','The query, pose-geometry, row packing, preservation and mask-reader dimensions propagate the frame count. Both native own-value routes run through the SQLite reader and tiny forward; faithful text returns to the language model. Full camera selection needs sealed goal-scene exclusions; the canonical GT loader and production processor/readers remain unqualified.','work/build8/proofs/final_repairs/results.json; work/build8/proofs/final_repairs/FRAME_COUNTS.json; work/build8/proofs/suite_tree/r2/results.json; work/build8/proofs/audit/FRAME64_SITE_REVIEW.json; work/build8/proofs/audit/FRAME64_REMAINING_SITES.json'),
('6','Audit closed; PORTRAIT_MASK_DISTORTION remains','Every inherited transform-review entry is classified. Bound mask coordinates remain unchanged; portrait share unknown: frame dimensions absent from the bound slices.','work/build8/proofs/audit/RESIZE_AUDIT.json; work/build8/proofs/audit/PORTRAIT_SUMMARY.json'),
('7','Closed','Legacy direct-source and suffix paths refuse empty or whitespace reasoning with LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED. Concrete traces preserve their bytes. Bound R2 admission is unchanged.','work/build8/proofs/direct/results.json; work/build8/proofs/direct/DIRECT.json; work/tree_r1/tests/test_r2_build8_direct.py'),
('8','Blocked; scope preserved','D2 init, D3 row-store bindings, D4 real dense manifest, rows-lane text and forms, in-forward reader work, production processor values and BF16 enablement remain unresolved.','work/build8/kits/RESULTS.json; work/build8/DECISIONS.md; out/BUILD7_REPORT.md')]
for r in items:put('| '+' | '.join(r)+' |')
put('\n| Suite | Run | Passed | Pre-existing failure events | Regression events | R2 failure events | Skipped | Evidence |\n|---|---:|---:|---:|---:|---:|---:|---|')
packet_fail=sum(v.get('outcome')!='passed' for v in packet.values())
put('| Packet | '+str(len(packet))+' | '+str(len(packet)-packet_fail)+' | 0 | '+str(packet_fail)+' | Not applicable | '+str(sum(v.get('outcome')=='skipped' for v in packet.values()))+' | `work/build8/proofs/packet/results.json` |')
put('| Frozen tree | '+' | '.join(str(comparison.get(k,'pending')) for k in ('run','passed','preexisting','regressions','r2_failures','skipped'))+' | `work/build8/SUITE_COMPARISON.json` |')
put('| Base reference | '+str(base.get('tests','pending'))+' | '+str(len(base.get('passed',[])))+' | '+str(len(base.get('failures',[]))+len(base.get('errors',[])))+' | Not applicable | Not applicable | '+str(len(base.get('skips',[])))+' | `work/build8/proofs/suite_base/results.json` |')
put('\nRun/pass values count test executions; failure events can include multiple failing subtests. The base groups resume only when source, fixture and runner hashes match their existing receipts. The runner retains its build-7 bytes. Group receipts under `work/build8/proofs/suite_base/` and the package log identify resumed groups; these are retained executions, not new runs.')
put('\n| Changed-statement class | Count | Evidence |\n|---|---:|---|')
for name in ('observed','CPU-reachable unresolved','GPU','frame-host','model-loader'):
 put('| '+name+' | '+str(coverage.get('classes',{}).get(name,0))+' | `work/build8/CHANGED_COVERAGE.json` |')
put('\nCoverage counts AST statement heads changed since the untouched base. Standard-library monitoring accepts hits only when the executed code fingerprint and current whole-file hash match. Unexecuted CPU statements remain gaps; a missing production input is not a passing test. The external classification records identify the required loader, frame host or GPU input.')
put('\nThe cache measurement isolates BF16 storage: the same BF16 tower/base passes with FP32 cached features. The failing BF16-cache case measures maximum absolute gradient error 1.5157856978476048e-05 and maximum relative error 0.01689813102427034 against tolerance 0.015625 (`work/build8/proofs/regressions/BF16_PARITY.json`). Lossy storage rounds pooled FP32 normalized features before the FP32 affine/projection. No cast-order defect was found; this build changes neither the tolerance nor BF16 enablement.')
put('\nThe native preparation proof records `gt_decision_mismatch` when an admitted R2 camera row reaches faithful identity checking (`work/build8/proofs/cpu/PREPARATION.json`). The adapter wraps the answer at `work/tree_r1/student_pilot/r2_adapters.py:73`, while the materializer compares its bare decision to that field at `work/tree_r1/generator/derivgen_v7/derivgen/materialize.py:566`. Faithful training remains disabled; this synthetic refusal does not measure identity on the unavailable bound store.')
put('\n| Kit | SHA256 | State | Evidence |\n|---|---|---|---|')
for k in kits:put('| '+k['arm'].upper()+' | '+tick(k['kit_sha256'])+' | GO=false; '+k['scan'].get('status','unverified')+' | `work/build8/proofs/review/KIT_READCHECK.json` |')
put('\nBoth kits were staged from empty in the requested order. The scale weight remains a labelled GUESS, inherited from the gravity-weight rationale; the minority count remains its registered input rather than a benchmark-derived statistic. Exact values and their unresolved pins appear in `work/build8/build_kits.py` and `work/build8/proofs/review/KIT_READCHECK.json`. Job-visible scanning runs on both staged and extracted kits.')
put('\n| EAT-1 clause | GF-1 tiny reader | C8r tiny reader | Evidence |\n|---|---|---|---|')
eats={m:read('work/build8/proofs/eat1/'+m+'/run/EAT1_REPORT.json',{}) for m in ('gf1','c8r')}
for clause in ('A1','A2','A3','A4','A5'):
 put('| '+clause+' | '+' | '.join(str(eats[m].get('clauses',{}).get(clause,{}).get('status','NOT RUN')) for m in ('gf1','c8r'))+' | `work/build8/proofs/eat1/gf1/run/EAT1_REPORT.json`; `work/build8/proofs/eat1/c8r/run/EAT1_REPORT.json` |')
put('\nThe static scan is `work/build8/proofs/eat1/SCAN_READ.json`. Tiny acceptance adapters use seeded native model/tower stand-ins and scripted call tokens to exercise readers. They do not qualify a production artifact or supply a product selector. A NOT RUN cache-proof subclause remains incomplete even when other dynamic checks pass. Stencil, degree, status and response-injection work stays outside forward and remains assigned to the reader-hook lane.')
put('\nThe stop driver uses the native shell trap, signal forwarder, rank relay, training loop, checkpoint/export writers and artifact reader. CPU allocation scaffolding replaces the production admission/GPU-launch setup. Tiny randomly initialized native weights and a tiny tokenizer/processor stand in at the unavailable model boundary; RGB encoding and SQLite reading remain real. The driver records per-rank source-bound statement hits when it can run. The sandbox attempt failed before any rank ran; the separate lane receipt failed after the first step at the signal helper path. The driver is repaired but unverified, and the production admission wrapper was not tested (`work/build8/proofs/stop_multirank/SOURCE.json`, `work/build8/proofs/stop_multirank/RESULT.codex_sandbox.json`, `work/build8/proofs/stop_multirank/RESULT.json`, `work/build8/proofs/stop_multirank/DRIVER_PINS.json`).')
put('\n| Build-7 blocker | Build-8 disposition | Evidence |\n|---|---|---|')
blockers=[
('init_selection_pending / D2','Unchanged; rule-selected production init is absent.','work/build8/kits/RESULTS.json'),
('rows_lane_store_bindings_missing / D3','Unchanged; production family/store pins are absent.','work/build8/kits/RESULTS.json'),
('gf1_real_dense_manifest_missing / D4','Unchanged; real dense reconstruction manifest is absent.','work/build8/kits/RESULTS.json'),
('processor_resolution_pin_missing; full parent inventory','Unchanged; no production processor or full parent-model proof.','work/build8/PROCESSOR_SEARCH.json'),
('ALL_FORMATTERS_NOT_QUALIFIED','Unchanged; bounded response round-trips do not establish all formatter paths.','out/BUILD7_REPORT.md'),
('ROWS_RULE_TEXT_PRESENT; ROWS_MINORITY_FORMS_UNBOUND','Unchanged rows-lane work; no bound row bytes or quotas were changed.','out/BUILD7_REPORT.md; work/build7/proofs/rows/RESULTS.json'),
('LEGACY_DIRECT_SOURCE_TRACE_UNQUALIFIED','Closed for empty-think training admission; concrete source/reader tests pass.','work/build8/proofs/direct/results.json'),
('FRAME64_ALL_READERS_UNQUALIFIED','Local dimensions repaired; full canonical GT and production readers remain blocked.','work/build8/proofs/audit/FRAME64_REMAINING_SITES.json'),
('OUTSIDE_FORWARD_FORMATTING; B04_FORWARD_HOOK_REQUIRED','Unchanged; the acceptance hook and registered computations remain absent.','work/build8/proofs/eat1'),
('R0_FULL_INPUT_INVENTORY_UNAVAILABLE','Unchanged; full stream/frame/cache overlap remains unknown.','work/build8/kits/RESULTS.json'),
('BF16_CACHE_GRADIENT_PARITY','Retained at the original failing tolerance; FP32 storage comparison passes.','work/build8/proofs/regressions/BF16_PARITY.json'),
('PORTRAIT_MASK_DISTORTION','All audit entries classified; known distortion retained without row-byte parity.','work/build8/proofs/audit/RESIZE_AUDIT.json'),
('BOUND_FAITHFUL_IDENTITY_RECEIPT_MISSING','Still missing; native R2 preparation now provides a concrete delimiter/decision refusal.','work/build8/proofs/cpu/PREPARATION.json'),
('FULL_ENCODER_PARITY_UNQUALIFIED','Unchanged; the bounded CPU proofs do not replace full production encoder parity.','work/build7/proofs/off_parity/RESULTS.json'),
('GLOO_INITIALIZATION; MULTIRANK_END_SLOT_UNPROVED','The sandbox refused sockets. A separate lane receipt reached the first step but failed signal forwarding. The helper path is repaired; end-slot validation remains unproved.','work/build8/proofs/stop_multirank/RESULT.codex_sandbox.json; work/build8/proofs/stop_multirank/RESULT.json; work/build8/proofs/stop_multirank/DRIVER_PINS.json'),
('INDEPENDENT_REVIEW_PENDING','Unchanged; this build used no other agent.','work/build8/DECISIONS.md'),
('SUITE_OR_COVERAGE_CRITERIA_UNMET','See the current counts above; unresolved failures and gaps remain blockers.','work/build8/SUITE_COMPARISON.json; work/build8/GAPS.json')]
for r in blockers:put('| '+' | '.join(r)+' |')
put('\n## For the second review')
put('\n- Run `work/build8/proofs/stop_multirank/RUN.sh` outside the socket-restricted sandbox. Review both ranks, the next-step stop boundary, checkpoint/export pins, artifact reload and fallback result. The driver’s admission-scope limitation remains explicit.')
put('- Check BF16 cache quantization at the unchanged assertion and keep the kit refusal until parity is qualified.')
put('- Review concrete direct traces, both-policy admission and the preserved scene exclusions. The separate bound R2 admission route was not altered.')
put('- Resolve faithful identity using the admitted answer envelope, then measure the unavailable bound store. The current refusal must not be converted into a claimed pass.')
put('- Review every remaining frame-count site, portrait coordinate defect, suite regression and CPU gap against its evidence file before changing GO.')
put('- The end-to-end acceptance lane should judge the outside-weight components below against the actual product inference path. This build did not move their selector, formatter, threshold or fallback behavior into the weights.')
put('\nNot checked: production init selection, full store/frame/cache inventories, unknown scene overlap, production processor values, full canonical long-frame admission, portrait population share, mask row-byte parity, full trained-model closure, GPU timing/capacity, successful multi-rank stop/reload, production EAT acceptance or independent review. No remote service, launch, GPU, checkpoint copy, full-store materialization, Git, SSH or other agent was used.')
verified=read('work/build8/FINAL_VERIFICATION.json')
if verified:put('\nFinal storage and hash verification: '+json.dumps({k:verified[k] for k in ('tree_files','storage_bytes','scratch_free_bytes')})+' (`work/build8/FINAL_VERIFICATION.json`).')
put('\nThe outside-weight source inventory follows. It conservatively includes module functions and reader/backend methods in the supplied inference scope, including support functions whose dynamic reachability is not established. A class name alone does not establish model registration. This inventory and the EAT traces identify the components for acceptance review; they do not certify a production path (`work/build8/proofs/audit/INFERENCE_COMPONENTS.json`).')
put('\nThe following known decoder and geometry operations require acceptance review. They remain unchanged, apart from the requested query-frame dimension. Their presence means the current reader cannot be claimed as the completed in-forward product.')
put('\n| File:line | Operation outside forward |\n|---|---|')
for r in read('work/build8/proofs/audit/INFERENCE_COMPONENTS.json',{}).get('known_outside_forward',[]):
 put('| '+tick(r['file']+':'+str(r['line']))+' | '+r['operation']+' |')
put('\n<details>\n<summary>Conservative inference component inventory</summary>\n')
put('\n| File:line | Component | Source classification |\n|---|---|---|')
for r in read('work/build8/proofs/audit/INFERENCE_COMPONENTS.json',{}).get('components',[]):
 put('| '+tick(r['file']+':'+str(r['line']))+' | '+tick(r['component'])+' | '+r['classification']+' |')
put('\n</details>')
(O/'BUILD8_REPORT.md').write_text('\n'.join(report)+'\n')
design=O/'DESIGN_RECORD_tree_rebuild_20261115.md';old=design.read_text();marker='\n## Build 8\n'
entry=marker+'\nThe local fixtures, visible-frame dimensions and legacy direct-source admission are repaired and covered by native CPU proofs. Empty-think training rows refuse with a named error. The portrait audit records each transform without changing bound mask coordinates. BF16 cache parity, missing production inputs, faithful identity, multi-rank stop evidence and the in-forward reader work remain explicit blockers. Both kits remain GO=false. The sealed package, final suites, changed-statement coverage and acceptance findings are recorded in `out/BUILD8_REPORT.md` and `work/build8/FINAL_VERIFICATION.json`.\n'
design.write_text(old.split(marker)[0]+entry if marker in old else old+entry)
(B/'FINAL_STATE.json').write_text(json.dumps(dict(tree_seal=seal.get('tree_sha256'),package={k:comparison.get(k) for k in ('run','passed','preexisting','regressions','r2_failures','skipped')},coverage=coverage.get('classes'),packet=dict(run=len(packet),passed=len(packet)-packet_fail),go=False),indent=2)+'\n')
print(json.dumps(dict(report='out/BUILD8_REPORT.md',cpu_gaps=gaps,regressions=comparison.get('regressions'),r2_failures=comparison.get('r2_failures'))))
