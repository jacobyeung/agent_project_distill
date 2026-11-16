"""Build the review report from completed, source-bound receipts."""
import collections,hashlib,json,re
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
def read(name):return json.loads((L/name).read_text())
def emit(name,value):(L/name).write_text(json.dumps(value,indent=2)+'\n')
tree=read('work/build6/proofs/suite_tree/results.json');base=read('work/build6/proofs/suite_base/results.json')
assert tree['complete'] and base['complete']
comparison=read('work/build6/SUITE_COMPARISON.json');coverage=read('work/build6/CHANGED_COVERAGE.json')
substitution=read('work/build6/LEGACY_SUBSTITUTION.json')
permissions={r['test']:r for r in read('work/build6/LEGACY_PERMISSION.json')}
assert substitution['verified']
assert all(hashlib.sha256((L/r['source']).read_bytes()).hexdigest()==r['source_sha256'] for r in substitution['sources'])
def explained_cause(row):
 if row['test']==substitution['test'] and row['cause']=='unclassified: AssertionError: False is not true':
  return 'legacy substitution expectation contradicts the native no-substitution guard'
 if row['test'] in permissions and row['cause']=='unclassified: PermissionError: [Errno 1] Operation not permitted':
  proof=permissions[row['test']]
  assert proof['tree_error']==row['tree_error'] and proof['base_error']==row['base_error'],'Refresh the permission explanation against final receipts'
  if proof['socket_constructor_in_both']:return 'sandbox refuses the legacy socket-construction fixture'
 return row['cause']
explained_counts=dict(collections.Counter(explained_cause(r) for r in comparison['failures'] if r['preexisting']))
legacy_lines=['# Pre-existing legacy failures','','Each listed test also fails in the untouched base. The basis records either a matching failure cause or a source-authenticated refusal preserved from Build 5. Both tracebacks and prior refusal evidence are retained in `work/build6/SUITE_COMPARISON.json`; guard hashes are in `work/build6/LEGACY_GUARDS.json`.','',
              '| Test | Cause | Basis |','|---|---|---|']
legacy_lines.extend('| `'+r['test'].replace('|','\\|')+'` | '+explained_cause(r).replace('|','\\|')+' | '+r['basis']+' |'
                    for r in comparison['failures'] if r['preexisting'])
legacy_lines += ['', 'The substitution and socket explanations are authenticated by `work/build6/LEGACY_SUBSTITUTION.json` and `work/build6/LEGACY_PERMISSION.json`. They explain the retained errors without changing suite outcomes or comparison rules.']
(B/'PREEXISTING_FAILURES.md').write_text('\n'.join(legacy_lines)+'\n')
packet=read('work/build6/proofs/packet/results.json');pc=collections.Counter(r['outcome'] for r in packet.values())
r2=read('work/build6/proofs/suite_tree/r2/results.json')
prior=read('work/build5/proofs/suite_tree/results.json')
lost=sorted(set(prior['passed'])-set(tree['passed']))
emit('work/build6/B5_PASS_COMPARISON.json',dict(source='work/build5/proofs/suite_tree/results.json',current='work/build6/proofs/suite_tree/results.json',lost_passes=lost,preserved=len(set(prior['passed'])&set(tree['passed']))))
initial=read('work/build6/proofs/r2_diagnostic/results.json')
diagnostic_sources=['work/build6/proofs/r2_diagnostic/results.json']
initial_failures=initial['errors']+initial['failures']
if (B/'proofs/suite_tree/diagnostic_results.json').exists():
 diagnostic_sources.append('work/build6/proofs/suite_tree/diagnostic_results.json')
 previous=read(diagnostic_sources[-1]);initial_failures+=previous['errors']+previous['failures']
fixed=sorted({name.split(' (',1)[0] for name,_ in initial_failures} & set(tree['passed']))
emit('work/build6/FIXES.json',dict(sources=diagnostic_sources,passing_source='work/build6/proofs/suite_tree/results.json',tests=fixed,count=len(fixed),note='Unique diagnostic test methods now passing; includes fixture repairs and source-closure checks.'))
initial_packet=read('work/build6/proofs/packet/initial_results.json')
key=lambda name:name.split('/')[-1]
pf={key(name) for name,r in initial_packet.items() if r['outcome']=='failed'} & {key(name) for name,r in packet.items() if r['outcome']=='passed'}
emit('work/build6/PACKET_COMPARISON.json',dict(run=len(packet),passed=pc['passed'],failed=pc['failed'],skipped=pc['skipped'],fixed=len(pf),fixed_tests=sorted(pf),initial='work/build6/proofs/packet/initial_results.json',final='work/build6/proofs/packet/results.json'))
temporary=[]
packet_sizes=read('work/build6/proofs/packet/temporary_sizes.json')
temporary.append(dict(variant='packet',source='work/build6/proofs/packet/temporary_sizes.json',maximum=max(packet_sizes,key=lambda r:r['bytes']),over_cap=[r for r in packet_sizes if r['bytes']>200_000_000]))
for variant in ('tree','base'):
 source='work/build6/proofs/suite_'+variant+'/temporary_sizes.json';sizes=read(source)
 boundaries=[{**r,'bytes':max(r['before_bytes'],r['after_bytes'])} for r in sizes]
 temporary.append(dict(variant=variant,source=source,maximum=max(boundaries,key=lambda r:r['bytes']),over_cap=[r for r in boundaries if r['bytes']>200_000_000]))
emit('work/build6/REPORT_DETAILS.json',dict(temporary_sizes=temporary,preexisting_causes=explained_counts,
     explanation_sources=['work/build6/SUITE_COMPARISON.json','work/build6/LEGACY_SUBSTITUTION.json','work/build6/LEGACY_PERMISSION.json']))
parity=read('work/build6/proofs/rows/PARITY.json');units=read('work/build6/proofs/rows/UNITS.json');delivery=read('work/build6/DELIVERY.json');kits=read('work/build6/kits/RESULTS.json');integration=read('work/build6/INTEGRATION_CHECK.json');audit=read('work/build6/STATIC_AUDIT.json')
gate_fix=read('work/build6/GATE_IDENTITY_FIX.json')
qualified=(len(packet)==202 and pc['passed']==202 and pc['failed']==0
           and not r2['errors'] and not r2['failures']
           and not comparison['regressions'] and not lost
           and coverage['classes'].get('CPU-reachable unresolved',0)==0 and gate_fix['validated'])
lines=['# Build 6 report','', '**'+('CPU checks qualified; production remains blocked.' if qualified else 'CPU qualification incomplete; production remains blocked.')+'**','',
 'The accepted contracts are installed. The kits require a pinned init, preserve the route table, gate final family admission, accept direct square-foot and inch answers, and require metric scores by asked unit. No launch, remote service or GPU work was performed.','',
 '## Integration','',f"The integration has {integration['exact']} exact files and {integration['merged']} merged files. Every hunk is accounted for; both level-basis functions remain byte-identical. Source: `work/build6/INTEGRATION_CHECK.json`; hashes, hunk dispositions and the recovery adaptation: `out/CONTRACTS_INTEGRATION.md`.",'',
 'The recovery adaptation preserves simulated-GT recovery with contracts OFF and applies the accepted training audit with contracts ON. The protected artifact modes, pinned grammar and sealed exclusions remain unchanged (`work/build6/STATIC_AUDIT.json`).','',
 'The standalone launch gate also mirrors the native heading-threshold identity rule. Its native-parity assertion remains and covers both epochs and invalid thresholds. This additional integration repair is outside the packet manifest (`work/build6/GATE_IDENTITY_FIX.json`, `work/build6/GATE_IDENTITY_FIX.diff`).','',
 '## Suites','', '| Suite | Run | Passed | Pre-existing failure events | Remaining failure events | Fixed diagnostic cases | Source |', '|---|---:|---:|---:|---:|---:|---|',
 f"| Packet | {len(packet)} | {pc['passed']} | 0 | {pc['failed']} | {len(pf)} | `work/build6/PACKET_COMPARISON.json` |",
 f"| Packaged tree | {comparison['run']} | {comparison['passed']} | {comparison['preexisting']} | {comparison['regressions']} | {len(fixed)} | `work/build6/SUITE_COMPARISON.json`, `work/build6/FIXES.json` |",
 f"| R2 and shared grammar | {r2['tests']} | {len(r2['passed'])} | 0 | {len(r2['errors'])+len(r2['failures'])} | — | `work/build6/proofs/suite_tree/r2/results.json` |",'',
 f"The tree has {len(tree['skips'])} skipped test executions; the comparison base ran {base['tests']} selected failing methods/modules under the same harness. Source: `work/build6/proofs/suite_tree/results.json` and `work/build6/proofs/suite_base/results.json`. Run/pass counts retain the harness schedule, including repeated test IDs. Failure events can include subtests and setup failures; fixed cases count diagnostic methods, not production defects.",'',
 f"Build-5 passes lost: {len(lost)}. Every affected method is listed in `work/build6/B5_PASS_COMPARISON.json`.",'',
 'The package wrapper ran from an empty directory (`work/build6/proofs/package/INVOCATION.json`). The extension preserves the prior temporary cap and guards. Harness changes are recorded as diffs under `work/build6/`; test-input changes are in `work/build6/TEST_INPUT_ADAPTATIONS.json` and `work/build6/TEST_ADAPTATIONS.diff`.','',
 'The packet assertions are unchanged. Paths point to the integrated tree, the supplied base and fixed proof outputs; supplied supporting fixtures retain their hashes. The runner substitutes stdlib code-fingerprinted monitoring for tracing, writes subprocess snippets to files, and applies the existing temporary cap. Sources: `work/build6/PACKET_PATH_ADAPTATIONS.diff`, `work/build6/PACKET_MONITOR.diff`, `work/build6/PACKET_INPUTS.json`.','',
 '| Pre-existing cause | Events |', '|---|---:|']
lines.extend('| '+cause.replace('|','/')+' | '+str(n)+' |' for cause,n in explained_counts.items())
lines+=['','Every pre-existing test is named with its cause and classification basis in `work/build6/PREEXISTING_FAILURES.md`. Source for every cause/count: `work/build6/SUITE_COMPARISON.json`, including both base and tree tracebacks. Existing unsupported-reader refusals also match the Build-5 receipts and authenticated guard sources (`work/build6/LEGACY_GUARDS.json`); their different base causes remain visible. Multiple errors from one test are retained individually.','',
 'The legacy first-batch fixture expects substitution after a deliberately failing row. Both native implementations refuse the row immediately, so its finite-result assertion fails. The guard and fixture have identical ASTs in tree and base (`work/build6/LEGACY_SUBSTITUTION.json`). This explains the stale substitution expectation without inferring an unrecorded model-forward error.','',
 'The previously unnamed permission failures occur in socket constructors in both tree and base. Their exact tracebacks are in `work/build6/LEGACY_PERMISSION.json`; the explained cause counts and their source paths are in `work/build6/REPORT_DETAILS.json`.','',
 '| Temporary measurement | Maximum bytes | Over-cap boundary events | Source |','|---|---:|---:|---|']
lines.extend(f"| {r['variant']} | {r['maximum']['bytes']} | {len(r['over_cap'])} | `{r['source']}` |" for r in temporary)
lines+=['','Legacy teacher fixtures that exceed the cap remain failures; the cap was not raised. Measurements above the cap do not establish continuous storage compliance. Exact tests are in `work/build6/REPORT_DETAILS.json`.','',
 '## Changed-statement coverage','', '| Class | Statements |','|---|---:|']
lines.extend('| '+kind+' | '+str(coverage['classes'].get(kind,0))+' |'
             for kind in ('observed','CPU-reachable unresolved','frame-host','model-loader','GPU'))
lines+=['','Source: `work/build6/CHANGED_COVERAGE.json`. The denominator includes statement headers and simple statements whose spans touch edited lines against the untouched base, including edited continuation lines. Hits require an observed statement-head line, the current file hash and the compiled-code fingerprint. Each external-input classification names its missing input; unresolved CPU statements remain explicit in `work/build6/GAPS.json`.','',
 '## Row proofs','', 'These counts cover packed-row production, validation and grammar. Full frame and scene joins remain unchecked.','', '| Family | Rows | OFF admitted / deferred | ON admitted / deferred | OFF equals build 5 | Source |','|---|---:|---:|---:|---|---|']
for r in parity['families']:
 lines.append(f"| {r['family']} | {r['rows']} | {r['off']['admitted']} / {r['off']['deferred']} | {r['on']['admitted']} / {r['on']['deferred']} | {r['off_equals_build5']} | `{r['source']}` |")
lines+=['','Counts and output hashes: `work/build6/proofs/rows/PARITY.json`. The comparison uses the authenticated build-5 tree copy. The real packed-row producer, reader and pinned grammar ran end to end; only frame-count placeholders were supplied. This proof does not run RGB joins or full scene admission. The supplied canonical slices produce no ON changes, consistent with the clean-row cases in `work/contracts_r6/ROW_FAMILY_PARITY_R6.md`. The packet suite exercises defective and heading-unavailable cases separately.','',
 'Historical full-intake receipts referenced by the earlier report are absent from this copied lane. Their published scene-admission counts were not requalified. This is an explicit limit of the row proof.','',
 'The supplied program slices contain frame-index lists, but the room slice has no frame-index or frame-pin field. The metadata census is in `work/build6/ROW_FRAME_METADATA.json`. The grammar check therefore does not establish a real RGB/frame join for these rows.','',
 f"The recorded admitted unit population is {units['admitted_population']:,}, at {units['rows_per_step']:.6f} rows per step. Sources: `{units['count_source']}` and `{units['rate_source']}`. `out/MIX_A0.md` now uses that admitted population.",'',
 '| Asked unit | Slice rows | Rows per step | Source |','|---|---:|---:|---|']
for u,n in units['slice_counts'].items():lines.append(f"| {u} | {n} | GUESS {units['slice_projected_rows_per_step'][u]:.6f} | `work/build6/proofs/rows/UNITS.json`; `{units['source']}` |")
lines+=['','Per-unit rates project slice proportions; the supplied full census has no per-unit counts. The proof checks exactly one conversion line per row, its unit factor, the printed distance operand, rounded product and final answer (`work/build6/proofs/rows/UNITS.json`).','',
 f"Room questions asking in square feet: {units['square_feet_room_rows']} in the supplied slice (`{units['room_source']}`). The direct row form is accepted, but this training slice does not cover it. No room program family was added.",'',
 '## Next-leg admission and CPU boundary','',
 'A2 is built to admission first; A0 is the fallback if A2 does not admit. Neither is a control. The route table retains absolute-distance and camera programs, direct room/other answers, unit rows and recovery rows (`work/tree_r1/student_pilot/r2_contract.py`, `work/tree_r1/student_pilot/r2_config.py`).','',
 'The init is the authenticated launch input in `out/INIT_INPUT.json`. No tested newer export was supplied, so the recorded choice uses the fallback. Archive staging derives its layout from that pin. Unpinned kits refuse (`work/tree_r1/tests/test_r2_build6.py`).','',
 'The final family gate refuses retention below 90% for units, recovery, room and distance programs after legitimate exclusions. Unknown overlap stays in the denominator. The fixture tests each family, the exact boundary and an unknown exclusion (`work/tree_r1/student_pilot/r2_admission.py`, `work/tree_r1/tests/test_r2_build6.py`).','',
 'Room calls execute through shared and generator sessions, live and audit sessions, the responder and routed decoder in the room-capable protocol selected by both kits (`work/build6/KIT_READCHECK.json`). Synthetic dense pose/depth replace GPU head outputs; decoder token fixtures replace learned generation. The actual room computation and response readers run (`work/build6/proofs/suite_tree/r2/ROOM_RUNTIME.json`). Legacy protocol modes retain their room-call refusal; the runtime proof covers the selected mode.','',
 'The native preparation proof runs real intake, materialization, native readers and rank encoding. Tiny synthetic RGB, a tiny processor/model and synthetic tower/head outputs stand in at unavailable learned/GPU boundaries. No pretrained-export accuracy or full training is claimed (`work/build6/proofs/suite_tree/r2/B3_NATIVE_JOB_PROOF.json`; `work/tree_r1/tests/test_r2_models.py`).','',
 'Metric readers derive units from questions. Score reports use ordered per-unit rows so native JSON serialization preserves metres-first order; empty groups carry no score. The fixture checks the real writer/reader round trip. Unsupported legacy evaluators remain closed (`work/tree_r1/student_pilot/r2_units.py`, `work/tree_r1/student_pilot/r2_policy.py`, `work/tree_r1/tests/test_r2_build6.py`).','',
 'All fourteen evidence obligations remain; none was fabricated or removed. The init, pose/depth/frame-embedding heads and depth-init lineage records rebind the selected input. Other evidence duties remain unchanged (`out/RECORDS_TO_REGENERATE.md`, `work/build6/EVIDENCE_DISPOSITION.md`).','',
 '## Delivery','',f"Package: `{delivery['path']}` ({delivery['bytes']} bytes), SHA256 `{delivery['sha256']}`. Tree seal: `{delivery['tree_seal']}`. Source: `work/build6/DELIVERY.json`.",'',
 'The package contains source, both kits, the comparison base, fixtures, the extended harness, packet tests and supporting text fixtures. Run its `work/build6/PACKAGE_TEST.sh` from an empty directory; run `work/build6/PACKET_TEST.sh` for the packet suite. The supplemental contract edges and focused repairs are reproducible with `work/build6/TARGETED_TEST.sh`; their receipt is `work/build6/proofs/final_targeted/results.json`.','',
 '| Kit | Hash | Scanner | Authorization |','|---|---|---|---|']
for k in kits:lines.append(f"| `{k['kit_path']}` | `{k['kit_sha256']}` | {k['scan']['status']} | Closed |")
lines+=['','Source: `work/build6/kits/RESULTS.json`. Storage, source pins and protected modes: `work/build6/STATIC_AUDIT.json`.','',
 '## For the second review','',
 'Check the per-hunk recovery adaptation, the final packet/tree receipts, the build-5 pass comparison and the statement-level coverage classifications. Review the pinned-init archive mapping, final admission denominator, direct unit forms and room-call evidence.','',
 'Do not treat bounded packed-row parity or synthetic CPU mechanics as full frame-host admission. Real dense RGB, selected-export bytes, full-population scene joins, the evidence registry, pretrained loading, distributed GPU training and durable remote recovery remain unchecked. Both authorizations remain closed.']
(L/'out/BUILD6_REPORT.md').write_text('\n'.join(lines)+'\n')
status=f"# Build 6 status\n\n{'CPU checks qualified' if qualified else 'CPU qualification incomplete'}; production remains blocked.\n\nThe final evidence, package identity, suite outcomes, coverage classes and remaining limits are recorded in `out/BUILD6_REPORT.md`. Both kits retain closed authorizations.\n"
(B/'STATUS.md').write_text(status)
print(json.dumps(dict(qualified=qualified,packet=dict(pc),regressions=comparison['regressions'],lost_build5_passes=len(lost),coverage=coverage['classes'])))
