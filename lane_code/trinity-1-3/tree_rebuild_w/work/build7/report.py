"""Write a source-backed delivery report without converting unknowns into passes."""
import collections,hashlib,json,re
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7';O=L/'out'
def read(name,default=None):
 p=L/name
 return json.loads(p.read_text()) if p.exists() else default
def source(name):return '`'+name+'`'
report=[]
def put(s=''):report.append(s)
seal=read('out/TREE_SEAL.json',{});delivery=read('work/build7/DELIVERY.json',{})
comparison=read('work/build7/SUITE_COMPARISON.json',{})
coverage=read('work/build7/CHANGED_COVERAGE.json',{})
packet=read('work/build7/proofs/packet/results.json',{})
tree=read('work/build7/proofs/suite_tree/results.json',{})
base=read('work/build7/proofs/suite_base/results.json',{})
kit=read('work/build7/proofs/review/KIT_READCHECK.json',[])
rows=read('work/build7/proofs/rows/RESULTS.json',{})
put('# Build 7 — BLOCKED; neither kit is launchable')
put('\nThe tree and kits contain the input gates, policy additions and patch integrations below. This build does not qualify the requested product. Missing production inputs, incomplete code integration, unqualified reader paths and failed checks remain explicit blockers. Nothing was launched or submitted.')
put('\nSource seal: '+source(seal.get('tree_sha256','pending'))+' (`out/TREE_SEAL.json`).')
put('\nPackage: '+source(delivery.get('path','pending'))+'; SHA256 '+source(delivery.get('sha256','pending'))+'; bytes '+str(delivery.get('bytes','pending'))+' (`work/build7/DELIVERY.json`). The inventory and base-relative diff are `out/TREE_FILES.sha256` and `out/TREE.diff`.')
put('\n## Requested items')
put('\n“Blocked” distinguishes completed local work from the missing evidence or code still required. The item numbers follow the build request.')
put('\n| Item | Status | Result and remaining blocker | Evidence |\n|---|---|---|---|')
items=[
('1','Closed locally; remote unverified','Staging mappings use the supplied source pins and archive member inventory. Frame-host self-check authenticates source bytes before staging. No Orchard source was read.','work/tree_r1/launch_r2/staging_sources.json; work/tree_r1/launch_r2/input_check.py; tests.test_r2_build7.InputTests.test_sources_pass_absent_sha_and_member_refusal'),
('2','Blocked: init_selection_pending','Init stays a pinned rule-selected parameter; temporary sources and mismatched hashes refuse. No candidate was selected. Record dependencies are enumerated separately.','work/tree_r1/student_pilot/b7_inputs.py; work/build7/proofs/review/INIT_DEPENDENCIES.json'),
('3','Blocked: rows_lane_store_bindings_missing','Family pins require D0 v5 and admitted A0/A2 sources and reject the sealed stores. The host binds each supplied family manifest to those pins before the existing native materializer combines streams. Missing or unbound manifests refuse. Production pins remain absent.','work/tree_r1/student_pilot/b7_inputs.py; work/build7/proofs/input_binding/results.json'),
('4','Blocked: gf1_real_dense_manifest_missing','The synthetic clip is absent from kit staging. A2 requires the real GF-1 manifest under the dense plan; no local fixture substitutes for it.','work/tree_r1/student_pilot/r2_config.py; work/build7/kits/RESULTS.json'),
('5','Closed','The empty exclusion-list files remain as authenticated zero-row lists. They preserve parent list provenance and exclude no row.','work/tree_r1/student_pilot/row_removals.py:31; work/build7/proofs/review/KIT_READCHECK.json'),
('6','Blocked: processor_resolution_pin_missing; full parent inventory unqualified','Both kits carry explicit required resolution parameters and per-module trainability/rates. Tiny-model optimizer membership equals requires_grad. Real bound processor values and full parent-model validation are unavailable.','work/build7/PROCESSOR_SEARCH.json; work/build7/proofs/review/KIT_READCHECK.json; work/build7/proofs/targeted_final/scale/RESULT.json'),
('7','Closed locally; stage limitation recorded','Positive scale weight is pinned in both kits. The real pose target producer supplies geometry-derived d-bar and the tiny scale loss backpropagates to the scale MLP. Existing connector-only A2 stage freezes that head; its subsequent joint stage can train it. Reader scale source is unchanged.','work/build7/proofs/targeted_final/scale/RESULT.json; work/build7/proofs/review/KIT_READCHECK.json; work/build7/DECISIONS.md'),
('8','Blocked: ALL_FORMATTERS_NOT_QUALIFIED','Versioned module and JSON are pinned; bounded printed responses round-trip. Inline and multiline bound envelopes remain distinct. Complete producer/runtime formatter coverage and canonical field reconstruction remain unproved.','work/tree_r1/student_pilot/response_spec.py; work/tree_r1/student_pilot/response_spec.json; work/build7/proofs/rows/RESULTS.json'),
('9','Blocked: ROWS_RULE_TEXT_PRESENT (rows lanes)','Row admission refuses detected rule-only text. Bounded slices contain unavailable/not-seen statuses. Numeric tower-rule provenance cannot be inferred from text alone. Rows were not edited.','work/tree_r1/student_pilot/row_text_audit.py; work/build7/proofs/review/RESPONSE_RULE_SOURCES.json; work/build7/proofs/rows/RESULTS.json'),
('10','Closed label gate; no passing production receipt','Kits default to harness_served and claim neither room form. The gate consumes the actual EAT report schema and requires passing dynamic clauses plus the reader artifact digest. Fixture pass, failure and wrong-artifact refusals pass. No model_served claim is made.','work/tree_r1/student_pilot/b7_inputs.py:53; work/build7/proofs/input_binding/results.json'),
('11','Blocked: FRAME64_ALL_READERS_UNQUALIFIED; OUTSIDE_FORWARD_FORMATTING','Core encoder, carrier/readout capacity, pose targets and export support pinned frame counts. All ground/MDG/read paths are not qualified. Final answer passthrough is tested; tool-value formatting remains outside forward. ReVSI is listed first; kits default to SFT.','work/build7/proofs/targeted_final/frames/TOKENS.json; work/build7/proofs/audit/NUMBER_PATHS.json; work/build7/proofs/review/KIT_READCHECK.json'),
('12','Blocked: ROWS_MINORITY_FORMS_UNBOUND; INDEPENDENT_REVIEW_PENDING','Both policy, separate type gate, per-item answer_form and pinned minority sampler are implemented. Missing head grammars refuse program rows; room stays direct. Native end-to-end store sampling and all legacy-policy byte parity remain unproved. Recovery form is deferred.','work/tree_r1/student_pilot/routing_type_gate.py; work/build7/DECISIONS.md; work/build7/proofs/rows/RESULTS.json'),
('13','Blocked: R0_FULL_INPUT_INVENTORY_UNAVAILABLE','Pinned R0 authority and alias-family refusals are implemented. Available slices were scanned. Full staged frames, caches and every stream are unavailable; unknown overlap is not admitted.','work/tree_r1/student_pilot/r0_exclusion.py; work/build7/proofs/audit/AUTHORITY_HASHES.json; work/build7/proofs/rows/RESULTS.json'),
('14','Blocked: BF16_CACHE_GRADIENT_PARITY; INDEPENDENT_REVIEW_PENDING','Cache patch rebased; option is off with FP32 default. Enabled BF16 is refused by kits. Supplied BF16 gradient tolerance still fails and was not widened. Cache tests and OFF behavior remain in the suite.','work/build7/PATCH_HUNKS.json; work/build7/proofs/targeted/results.json; work/tree_r1/tests/test_gf1_cache.py'),
('15','Blocked: B04_FORWARD_HOOK_REQUIRED; PORTRAIT_MASK_DISTORTION','Native tiny export/reload emits an artifact manifest and declared module roles. Full read-file closure is not qualified. Stencil, degree and status computations remain outside forward; portrait mask paths remain distorted to preserve bound-row bytes. EAT results follow below.','work/tree_r1/student_pilot/eat1_export.py; work/build7/proofs/eat1; work/build7/proofs/audit/RESIZE_AUDIT.json'),
('16','Blocked: BOUND_FAITHFUL_IDENTITY_RECEIPT_MISSING; FULL_ENCODER_PARITY_UNQUALIFIED','Faithful patch rebased behind an off-by-default switch. Materializer exists; fixture identity gate refuses insufficient identity. Native tiny losses, gradients, batches, legacy policy data and own-value suffix masks match the authenticated build-6 source. Full scheduled-sampling encoder parity and bound routing identity remain unqualified.','work/build7/PATCH_HUNKS.json; work/build7/proofs/off_parity/RESULTS.json; work/build7/proofs/targeted_final/results.json'),
('16a','Blocked: GLOO_INITIALIZATION; MULTIRANK_END_SLOT_UNPROVED','Shell stop-file paths and rank polling are connected. Real trap/poll proof passed. Gloo could not initialize; full wrapper chain, multi-rank boundary stop and end-slot export were not proved. Fallback condition is tested; exported fallback end slot remains unproved.','work/build7/proofs/stop/RESULTS.json; work/build7/proofs/review/STOP_PATH.json'),
('17','Blocked pending all suite/coverage criteria','Final frozen package groups and packet suite are recorded below. Failures and CPU gaps remain failures, including new ones.','work/build7/FINAL_PASS.json; work/build7/SUITE_COMPARISON.json; work/build7/CHANGED_COVERAGE.json'),
('18','Closed staging; GO=false','Both final kits were staged from empty, A2 first, scanned and authenticated. Their source pins match the frozen tree.','work/build7/proofs/review/KIT_READCHECK.json; work/build7/proofs/package/KIT_TESTS.json'),
('19','Carried into final comparison','Build-6 regressions and gaps are individually mapped below. Build 6 was not separately finalized. Package groups have input-hash-bound resume receipts.','work/build7/BUILD6_DISPOSITION.json; work/build7/package.py')]
for num,status,detail,evidence in items:put('| '+num+' | '+status+' | '+detail+' | '+source(evidence)+' |')
put('\n## Suites and coverage')
pc=collections.Counter(v.get('outcome','unknown') for v in packet.values())
put('\nPacket: '+json.dumps(dict(run=len(packet),**pc))+' (`work/build7/proofs/packet/results.json`). The harness executes the original tests under `work/contracts_r6/packet_root/work/tests_r6`, relocating input/output paths in memory. Their assertions remain unchanged.')
put('\n| Package variant | Run | Passed | Failure events | Error events | Skipped | Complete | Source |\n|---|---:|---:|---:|---:|---:|---|---|')
for name,value in [('tree',tree),('base',base)]:
 put('| '+name+' | '+' | '.join(str(v) for v in (value.get('tests','pending'),len(value.get('passed',[])),len(value.get('failures',[])),len(value.get('errors',[])),len(value.get('skips',[])),value.get('complete',False)))+' | '+source('work/build7/proofs/suite_'+name+'/results.json')+' |')
put('\nComparison: '+json.dumps({k:comparison.get(k,'pending') for k in ('run','passed','preexisting','regressions','r2_failures','skipped')})+' (`work/build7/SUITE_COMPARISON.json`). All failure names, causes and paired base traces are retained there. Execution counts include repeated test IDs; subtest and setup errors can add failure events.')
base_failed={name for name,_ in base.get('failures',[])+base.get('errors',[])}
fixed=sorted(base_failed.intersection(tree.get('passed',[])))
(B/'FIXED_BASE_FAILURES.json').write_text(json.dumps(dict(count=len(fixed),tests=fixed,tree='work/build7/proofs/suite_tree/results.json',base='work/build7/proofs/suite_base/results.json'),indent=2)+'\n')
put('\nPreviously failing base test IDs now passing: '+str(len(fixed))+' (`work/build7/FIXED_BASE_FAILURES.json`); these exact-ID fixes are distinct from new tests and from repeated execution counts.')
put('\n| Changed-statement class | Count | Source |\n|---|---:|---|')
for name,count in coverage.get('classes',{'pending':0}).items():put('| '+name+' | '+str(count)+' | `work/build7/CHANGED_COVERAGE.json` |')
put('\nCoverage uses standard-library sys.monitoring, AST changed-statement heads, compiled-code fingerprints and exact current-file hashes. No inference from adjacent lines counts as coverage. Builds through this final tree are compared with the untouched base; integrated packet lines enter the same denominator. `work/build7/GAPS.json` lists unresolved CPU lines. External classifications state missing inputs.')
prior=read('work/build7/proofs/audit/BUILD6_REGRESSIONS.json',[])
disposition=[]
for row in prior:
 name=row['test'];matches=[r for r in comparison.get('failures',[]) if r['test']==name]
 passed=any(p==name or p.split(' (')[0]==name.split(' (')[0] for p in tree.get('passed',[]))
 disposition.append(dict(test=name,status='resolved' if passed and not matches else 'open',evidence='work/build7/proofs/suite_tree/results.json',cause=matches[0]['cause'] if matches else ('not in final passing receipt' if not passed else 'passed on final source')))
oldgaps=read('work/build6/GAPS.json',{});mapped=[]
for name,entries in oldgaps.items():
 for line,text in entries:
  matches=[r for r in coverage.get('statements',[]) if r['file']==name and r['text']==text]
  resolved=bool(matches) and all(r['executed'] for r in matches)
  mapped.append(dict(file=name,build6_line=line,text=text,status='resolved' if resolved else 'open',
   final_lines=[r['line'] for r in matches],cause='exact statement text observed at every matching final changed statement' if resolved else 'No unambiguous all-observed final statement match; not assumed covered'))
carry=dict(regressions=disposition,gaps=mapped,gap_counts=dict(collections.Counter(r['status'] for r in mapped)))
(B/'BUILD6_DISPOSITION.json').write_text(json.dumps(carry,indent=2)+'\n')
put('\nBuild-6 regression disposition (`work/build7/BUILD6_DISPOSITION.json`):')
for r in disposition:put('\n- '+source(r['test'])+': '+r['status']+'; '+r['cause']+'.')
put('\nBuild-6 gap mapping: '+json.dumps(carry['gap_counts'])+' (`work/build7/BUILD6_DISPOSITION.json`); the original per-file gaps remain in `work/build6/GAPS.json`. Ambiguous textual mappings remain open.')
put('\n## Kit pins and model behavior')
for k in kit:
 put('\n'+k['arm'].upper()+': SHA256 '+source(k['kit_sha256'])+'; scanner '+k['scan']['status']+' (`work/build7/proofs/review/KIT_READCHECK.json`). Layout: '+source(json.dumps(k['layout']))+'. Trainable list: '+source(json.dumps(k['trainable_modules']))+'.')
put('\nThe module list follows the existing full_ft/final-mode optimizer; loading the bound private-depth initialization freezes its private ViT. The connector-only stage separately freezes the other modules. `artifact.json` records actual named-parameter membership on export. The tiny-model list is not proof that an absent full checkpoint has the same inventory.')
put('\nThe scale weight is **GUESS 1.0**, equal to the final-mode gravity weight (`work/build7/build_kits.py`). The real `pose_samples.encode_sample` and `camera_targets.trajectory_scale` produce per-clip d-bar; the existing head loss takes its logarithm. Measured loss and gradient parameter names are in `work/build7/proofs/targeted_final/scale/RESULT.json`. No benchmark answer chooses the target or weight.')
put('\nThe native `CarrierC1.readout` exposes `trajectory_step_m`; `HeadState` currently discards the scale output and its downstream geometry still uses the existing scale source. `student_pilot/tower_scale.py` and `tower_scale_rule.py` remain unchanged in their scale-source behavior. Consuming the head scale needs the in-forward reader hook; this build does not switch it.')
tokens=read('work/build7/proofs/targeted_final/frames/TOKENS.json',[])
put('\nTiny-model frame measurements: '+source(json.dumps(tokens))+' (`work/build7/proofs/targeted_final/frames/TOKENS.json`). This uses the tiny native model with one visual token per frame, not D0 resolution. **GUESS:** doubling frame count doubles visual tokens and approximately doubles visual/activation storage; attention work can approach fourfold. Actual GPU memory/time is unmeasured. D0-resolution token counts await its processor pin.')
put('\nThe routed query tensor still fixes its frame dimension in `student_pilot/carrier_c1_routing.query_tensor`. Additional ground, MDG and camera-row assumptions are enumerated with file:line in `work/build7/proofs/audit/FRAME64_REMAINING_SITES.json`. These are local implementation or compatibility-proof gaps, not missing production pins. The kit’s FRAME64_ALL_READERS_UNQUALIFIED blocker remains in force.')
put('\nThe empty exclusion lists remain pinned to the empty-file digest. `Removals.__init__` reads only nonblank lines (`work/tree_r1/student_pilot/row_removals.py:31`) and `keep` tests membership in the resulting empty sets. They are zero-effect provenance entries, not missing data inferred to be clean.')
put('\nInit dependencies for every record are in `work/build7/proofs/review/INIT_DEPENDENCIES.json`. The selected export, pose head, depth head and frame embeddings depend directly on the selection. Private-depth and connector records depend on whether the selected export supplies those components; other component records retain their independent provenance obligations.')
put('\n## Bound slices, response text and exclusions')
put('\n| Slice | Rows read | Rule-only status rows | Responses / exact round-trips | R0 matches | Portrait frames | Source |\n|---|---:|---:|---|---|---|---|')
for r in rows.get('families',[]):
 c=r['counts'];put('| '+Path(r['source']).name+' | '+str(c.get('rows',0))+' | '+str(c.get('runtime_box_status',0))+' | '+str(c.get('responses',0))+' / '+str(c.get('response_roundtrip',0))+' | '+str(c.get('r0_refused',c.get('r0_matches',0)))+' | Unknown; dimensions absent | '+source(r['source'])+' |')
put('\nAll slice counts and source hashes come from `work/build7/proofs/rows/RESULTS.json`; overlapping fixture and real slices are not a population estimate. R0 matches are inspected-row matches only: no row files were modified, so no physical removal is claimed. Full pose, pointing, raster, depth, dense-frame and cache inventories were not supplied; their removed counts and overlap are unknown. The kits refuse unknown full-input qualification.')
put('\nThe format module preserves the bound inline camera/calculator envelope and newline ground envelope; signed deltas, metric decimals, integer degree angles and status literals retain their printed bytes. These existing variants are represented explicitly rather than normalized. The parser preserves the body instead of reconstructing every semantic field, so full canonical formatting is still open. Patterns and actual print sites are in `work/build7/proofs/review/RESPONSE_RULE_SOURCES.json`. Heuristic text matches cannot certify that a numeric value came from a head.')
put('\n## EAT-1 and outside-weight inference components')
baseline={'A1':'PASS (tower weights declared)','A2':'FAIL','A3':'FAIL','A4':'FAIL','A5':'PASS'}
put('\n| Clause | Supplied build-5 GF-1 baseline | Build-7 GF-1 tiny | Build-7 C8r tiny |\n|---|---|---|---|')
eats={m:read('work/build7/proofs/eat1/'+m+'/run/EAT1_REPORT.json',{}) for m in ('gf1','c8r')}
for clause in ('A1','A2','A3','A4','A5'):
 put('| '+clause+' | '+baseline[clause]+' | '+str(eats['gf1'].get('clauses',{}).get(clause,{}).get('status','NOT RUN'))+' | '+str(eats['c8r'].get('clauses',{}).get(clause,{}).get('status','NOT RUN'))+' |')
put('\nSources: `work/design/eat1_b03/out/BASELINE_A2_TREE.md`; `work/build7/proofs/eat1/gf1/run/EAT1_REPORT.json`; `work/build7/proofs/eat1/c8r/run/EAT1_REPORT.json`. Static scope was copied and rewritten to this tree in `work/build7/proofs/eat1/SCOPE_READ.txt`.')
put('\nA5 is incomplete because the supplied runner reports its cache-proof clause as NOT RUN; tower execution and perturbation clauses pass. The baseline’s aggregate PASS must not substitute for the missing clause (`work/build7/proofs/eat1/gf1/run/EAT1_REPORT.json`).')
scan=read('work/build7/proofs/eat1/SCAN_READ.json',{})
classes=collections.Counter(f['rule'] for f in scan.get('findings',[]))
put('\nBuild-7 static findings by class: '+source(json.dumps(dict(classes)))+' (`work/build7/proofs/eat1/SCAN_READ.json`). Baseline class counts are recorded in `work/design/eat1_b03/out/BASELINE_A2_TREE.md`.')
baseline_classes=dict(constant=290,threshold=76,status=52,guard=48,table_load=32,data_file=20,response_outside_model=17,unit_conversion=15,cache=12,except_substitute=9)
current_classes=collections.Counter()
for name,count in classes.items():current_classes[name.split('.',1)[-1]]+=count
put('\n| Static finding class | Supplied build-5 baseline | Build-7 scope |\n|---|---:|---:|')
for name in sorted(set(baseline_classes)|set(current_classes)):
 put('| '+name+' | '+str(baseline_classes.get(name,0))+' | '+str(current_classes.get(name,0))+' |')
put('\nTable sources: `work/design/eat1_b03/out/BASELINE_A2_TREE.md`, section 1, and `work/build7/proofs/eat1/SCAN_READ.json`. Counts are scanner findings, not independent defects or acceptance passes.')
put('\nThe supplied tiny adapters use tiny pretrained-module stand-ins, a scripted token policy for exercising calls, seeded connector perturbations and no live ground session. Their findings qualify those fixture paths only. They are acceptance-test scaffolding, not a new product selector. Native tiny export/reload uses only one-rank collective/state-collection stand-ins; the real export and reader functions run.')
put('\nRemaining outside-forward computations include the depth stencil in `student_pilot/geometry_profiles.py`, degree conversions in `student_pilot/carrier_c1_routing.py` and `trace_format/box_v313.py`, statuses in the box module, response injection in `carrier_c1_batch_decode.py`, typed errors in `carrier_c1_decode.py`, and calibrated MDG tau. Their exact current lines appear below and in `RESPONSE_RULE_SOURCES.json`. They remain assigned to the in-forward hook or named build blockers; moving a function name alone would not satisfy forward execution.')
put('\nNo final-answer unit conversion was found in the inspected `evalpath.runtime.generate` path; it returns decoded model text unchanged, as the passthrough fixture verifies. Tool-response number formatting is still outside the weights and is not claimed compliant. `work/build7/proofs/audit/NUMBER_PATHS.json` lists each discovered formatting/conversion site. The scan is conservative, not a proof of every dynamic product path.')
put('\n| Formatting/conversion location | Existing operation |\n|---|---|')
for entry in read('work/build7/proofs/audit/NUMBER_PATHS.json',[]):
 put('| '+source('work/tree_r1/'+entry['file']+':'+str(entry['line']))+' | '+source(entry['text'].replace('|','&#124;'))+' |')
components=read('work/build7/proofs/audit/INFERENCE_COMPONENTS.json',{}).get('components',[])
put('\nConservative inference component inventory, with file:line for review (`work/build7/proofs/audit/INFERENCE_COMPONENTS.json`). Module-level functions are outside registered weights; backend methods need dynamic forward-scope judgment. This includes support/scoring functions and does not assert that every entry executes for every item. It does not replace the acceptance test.\n')
grouped=collections.defaultdict(list)
for c in components:grouped[c['file']].append(c['component']+':'+str(c['line']))
for file,values in grouped.items():put('- '+source('work/tree_r1/'+file)+': '+', '.join(source(v) for v in values)+'.')
put('\n## Portrait audit')
put('\nThe fixed-mask canvases in `student_pilot/routed_features.py:18`, `ofs/core.py:51` and `verifykit/export.py:32` distort portrait aspect. Portrait and landscape square-mask fixture extents are in `work/build7/proofs/targeted_final/portrait/RESULT.json`. The GF-1 square-pad path preserves aspect, but padded coordinates still require the existing ROI mapping. The native student processor normally uses aspect-aware resize; the absent production processor configuration prevents full qualification. No RGB source population was inspected, so each bound slice has an unknown portrait share.')
put('\nThe complete resize-site audit is `work/build7/proofs/audit/RESIZE_AUDIT.json`. Entries marked “requires transform-context review” remain open; the audit did not establish every resize as safe. No mask coordinate change was made because row-byte parity was not proved.')
put('\n| Resize location | Portrait assessment |\n|---|---|')
for entry in read('work/build7/proofs/audit/RESIZE_AUDIT.json',[]):
 put('| '+source('work/tree_r1/'+entry['file']+':'+str(entry['line']))+' | '+str(entry['portrait_aspect_distorted'])+' |')
put('\n## Stop path')
put('\nS1 wrote the host-kit stop file while its sandbox used a separate staged kit; S1 also did not export the K3 path that ranks poll. The shell now writes the staged stop file and exports its sandbox path, and the rank checks it at step boundaries. `work/build7/proofs/review/STOP_PATH.json` records the current file:line chain. The real extracted shell trap and native poll pass; `work/build7/proofs/stop/RESULTS.json` records both stop-file SHA256 values.')
put('\nGloo initialization failed with “Cannot resolve 127.0.0.1 to a (local) address” (`work/build7/proofs/stop/RESULTS.json`). I did not retry or bypass that environment restriction. There is no multi-rank end slot and no end-slot hash. The fallback condition forces export at its configured step, but a real multi-rank fallback export remains unproved.')
put('\n## For the second review')
put('\n- Review the both-path build-loop/type gate and sampler separately. Check preserved policies, per-item form identity, missing grammars, native preparation binding and exact minority quotas. The shared grammar authority remains byte-identical (`work/build7/proofs/audit/AUTHORITY_HASHES.json`).')
put('- Review the cache rebase and its numerical limits. Every hunk disposition is in `work/build7/PATCH_HUNKS.json`; BF16 gradient parity fails the original tolerance. Confirm the off path and FP32 launch restriction before enabling the option.')
put('- Review faithful-row all-reduced refusals, the identity gate and missing bound-row identity/OFF-parity receipts. No independent review was performed: the build explicitly forbids another agent.')
put('- Review unresolved product computations against EAT, and the manifest’s missing full production read closure. No acceptance claim follows from attaching module names or a manifest.')
put('- Review every remaining suite regression and CPU gap before changing GO. `work/build7/SUITE_COMPARISON.json`, `GAPS.json` and `BUILD6_DISPOSITION.json` are the authoritative lists.')
put('\n## Limits and delivery state')
put('\nNot checked: real staging bytes on Orchard/GCS, the selected init, full stores, complete alias overlap, production processor values, real frame portrait share, GPU capacity or timing, real distributed stop/export, every formatter, every long-frame reader, full trained-module closure, a production EAT read, or an independent review. No launch, remote call, checkpoint copy, full-store materialization, Git, SSH, GPU or other agent was used. The package and kits are review artifacts; GO remains false.')
text='\n'.join(report)+'\n';(O/'BUILD7_REPORT.md').write_text(text)
card='# Prelaunch card — Build 7: GO=false\n\nThe final tree is sealed as '+seal.get('tree_sha256','pending')+' (`out/TREE_SEAL.json`). Both kits are blocked.\n\n'
for k in kit:card+='- '+k['arm'].upper()+': '+k['kit_sha256']+' (`work/build7/proofs/review/KIT_READCHECK.json`). Blockers: '+', '.join(k['blockers'])+'.\n'
card+='\nRead `out/BUILD7_REPORT.md`, `work/build7/SUITE_COMPARISON.json`, `work/build7/GAPS.json` and the EAT reports before any approval. No production approval is present.\n'
(O/'PRELAUNCH_CARD.md').write_text(card)
design=O/'DESIGN_RECORD_tree_rebuild_20261115.md';original=design.read_text();marker='\n## Build 7\n'
entry=marker+'\nThe sealed tree and both closed kits are delivered for review. Input pins and refusal gates are implemented, but missing inputs, reader-forward compliance, long-frame qualification, cache precision, stop/export and validation gaps prevent launch. Decisions and remaining work are in `out/BUILD7_REPORT.md` and `work/build7/DECISIONS.md`. The init remains unselected; no rows or benchmark-dependent quotas were changed.\n'
design.write_text(original.split(marker)[0]+entry)
print(json.dumps(dict(report='out/BUILD7_REPORT.md',tree_complete=tree.get('complete',False),base_complete=base.get('complete',False),packet_tests=len(packet))))
