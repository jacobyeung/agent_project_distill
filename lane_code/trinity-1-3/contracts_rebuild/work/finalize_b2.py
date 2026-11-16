from pathlib import Path
import collections,hashlib,json
L=Path(__file__).resolve().parents[1];out=L/'out'
def load(name):return json.loads((out/name).read_text())
def save(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n')
def link(name):return f'[{name}]({out/name})'
def source(name):return f'[{Path(name).name}]({L/name})'

fixtures={p.stem.removeprefix('B2_fixture_'):json.loads(p.read_text()) for p in out.glob('B2_fixture_*.json')}
assert len(fixtures)==11
baseline=load('CPU_base_proof_off.json')
for kind,r in fixtures.items():
    assert r['orientations']['inverted']['on']['guard']=='reference_camera_up_opposes_gravity'
    assert r['orientations']['rolled90']['on']['guard']=='pass'
    if kind in baseline:
        off=r['orientations']['original']['off'];b=baseline[kind]
        assert off['guard']==b['verdict'] and off['responses']==b['responses'],kind
heads={p.stem.removeprefix('B2_heads_'):json.loads(p.read_text()) for p in out.glob('B2_heads_*.json')}
assert len(heads)==4
proof=dict(source=str(L/'work/tests/test_build2.py'),fixture_source=str(L/'work/tests/fixtures_contracts.py'),
    fixture_count=len(fixtures),orientation_cases=len(fixtures)*3,epoch_cases=len(fixtures)*6,
    inverted_refused=len(fixtures),rolled90_passed=len(fixtures),sealed_replay_byte_equal=len(baseline),
    sealed_replay_source=str(out/'CPU_base_proof_off.json'),
    orientation_definition='Preserve each fixture pitch, translations, intrinsics, depth and masks. Set absolute image roll to inverted or ninety degrees, so already inverted fixtures remain genuinely inverted.',
    fixtures=fixtures,head_response_path='LiveSession.bind_state -> carrier_c1_decode.respond_state; actual OwnGeometry head formatter',head_fixtures=heads,
    metric_assertion='Every metric value emitted by OFF equals ON. Heading-defined responses are identical except the required MDG repair. Undefined heading emits the shared status. Sealed guard acceptance alone does not guarantee a metric response: exact vertical lifting and MDG boxes can be unavailable.',
    limitations=['Synthetic masks and geometry; no model inference or real-capture geometry replay.',
                  'Exact-vertical sealed lifting failure and sealed MDG box failure have no numeric value to compare. Their added ON outputs are explicit exceptions, not a universal parity claim.'])
save('CPU_PROOF_B2.json',proof)

# Merge rerun outcomes by test ID; retain unavailable inherited tests explicitly.
results={};origins={}
for tag in ('B2_INTEGRATION','B2_FINAL','B2_FIXTURE_FINAL','B2_COVERAGE_EXTRA','B2_TREE_RUNNABLE'):
    for name,value in load(tag+'_results.json').items():
        if tag=='B2_TREE_RUNNABLE':name='trees/tree_r1_rehearsal/'+name
        results[name]=value;origins[name]=str(out/(tag+'_results.json'))
contracts={k:v for k,v in results.items() if k.startswith('tests/test_')}
# Lane tests have ids tests/test_*.py; inherited tests carry trees/<tree>/tests/.
assert contracts and all(v['outcome']=='passed' for v in contracts.values()),[(k,v['outcome']) for k,v in contracts.items() if v['outcome']!='passed']
tree={k:v for k,v in results.items() if '/tests/test_r2_' in k}
blocked={k:v['detail'] for k,v in tree.items() if v['outcome']!='passed'}
assert all('FileNotFoundError' in detail for detail in blocked.values())
summary=dict(source_paths=sorted(set(origins.values())),contract_suite=dict(collections.Counter(v['outcome'] for v in contracts.values())),
    tree_suite=dict(collections.Counter(v['outcome'] for v in tree.values())),tree_unavailable=blocked,
    remaining_failures={k:v for k,v in results.items() if v['outcome']=='failed'},results=results,result_sources=origins)
save('FINAL_TEST_RESULTS_B2.json',summary)

audit=load('REAL_ROW_AUDIT.json');u=load('REAL_CANDIDATE_UNIVERSE.json')['totals'];seal=load('INTEGRATION_SEAL.json');coverage=load('COVERAGE_DETAIL_B2.json')
assert not audit['findings'] and not load('REAL_CANDIDATE_UNIVERSE.json')['disagreements']
assert all(v['total']==v['executed'] for v in coverage.values())
distance=audit['totals']['packed:object_abs_distance'];room=audit['totals']['packed:room_size_estimation']
meta=sum(v['counts'].get('rows_read',0) for v in audit['deferred_members'].values())
record='/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md'
recordlink=f'[geometry record]({record})'
rowsource=link('REAL_ROW_AUDIT.json');usource=link('REAL_CANDIDATE_UNIVERSE.json');testsource=link('FINAL_TEST_RESULTS_B2.json');cpusource=link('CPU_PROOF_B2.json')
coverage_text='; '.join(f"{g} {v['executed']}/{v['total']}" for g,v in coverage.items())

report=f'''# Contracts report

The patches apply with exact hashes and zero fuzz to the sealed base and the supplied integration tree. Real-row admission agrees with runtime candidate membership. The integration rehearsal is ready for review; tests requiring external record fixtures remain unavailable. Sources: {link('APPLY_PROOF.json')}, {rowsource}, {usource}, {testsource}.

## Application and integration

Run `bash out/apply_contract_patches.sh TARGET_TREE --dry-run`, then omit `--dry-run` to install. Keep {link('contract_hash_checks.py')}, {link('PATCH_MANIFEST.json')} and every patch beside the script. The script checks every touched base hash, chooses the hash-bound integration variant, patches a complete sibling copy in geometry/candidates/box order, rejects offsets/fuzz/rejects, verifies final hashes, rechecks the target inventory, then replaces the directory with rollback on an ordinary installation error. It retains staging and the original tree. It refuses repeat application and altered bases without changing the target. Evidence: {link('APPLY_PROOF.json')}.

The only overlapping file is `student_pilot/carrier_c1_routing.py`; it belongs to the geometry patch. {link('PATCH_geometry_on_tree_r1.diff')} preserves the integration event-row admission branch and adds the contract heading branch. Applying the independent edits in either order gives identical bytes. Sources: {link('INTEGRATION_MERGE_PROOF.json')}, {link('PATCH_MANIFEST.json')}.

The rehearsal contains {seal['files']} source files and has seal `{seal['tree_sha256']}`, computed by its own `student_pilot/source_seal.py` inventory and digest. Source: {link('INTEGRATION_SEAL.json')}.

## Model and tool contract

The model answers from RGB. The patched tool path keeps geometry private and exposes numbers only through the deployed text formatter. Training and serving share that formatter. The response path is `carrier_c1_decode.respond_state` → `trace_format313.respond` → `LiveSession.execute`. Head calls use the same bound session and deployed head formatter. Sources: {source('work/tests/fixtures_contracts.py')}, {source('work/tests/test_build2.py')}, {source('work/src/student_pilot/carrier_c1_decode.py')}.

The boolean `contract_epoch` defaults ON. OFF retains the sealed guard and formatting for replay. Backend identity, materialization receipts and recorded queries bind the epoch. Undefined heading prints `heading unavailable`; it does not label visible objects `not seen`. Distances, area, physical size and count remain available where their geometry supports them. Centres, yaw, axes, witnesses, keypoints and directional head outputs withhold heading-dependent values. Metric boxes remain private. Sources: {source('work/src/trace_format/contracts.py')}, {source('work/src/student_pilot/geometry_profiles.py')}, {cpusource}.

The reviewed guard uses `UP_PLANE_MIN = 0.3`; when reference up has less image-plane support, usable frames determine the convention verdict. No alternate heading basis is introduced. Marked MDG outputs expose already-cut lifted points as `points_cut`; they do not recut masks or change thresholds. Sources: {source('work/src/student_pilot/geometry_profiles.py')}, {source('work/src/student_pilot/live_instances314.py')}.

## Real rows and candidate universe

The complete scan covers {distance['rows_read']} distance and {room['rows_read']} room program rows in each of the admitted and packed representations. After the package exclusion lists, {distance['sealed_pool_eligible']} distance and {room['sealed_pool_eligible']} room rows are eligible; all pass the final audit. The room count comes from the supplied package manifest, which includes both scene-room sets. Raw/packed representations are not distinct examples. Source: {rowsource}.

The audit calls exactly the function used by the materializer admission loop, `audit_training_contract([row], manifest)[0]`, on unchanged real JSON. It also scans direct rows and all identifiable deferred/removal members. The latter contain {meta} metadata records without question/target/events, plus an empty member; a no-op audit verdict does not admit these metadata records to training. Sources: {rowsource}, {source('work/real/x/66caacf5c9191457.json')}.

The comparison establishes sealed **pool eligibility**, not actual optimization exposure. The package lacks the leg's sampled membership roster. Its `training_admitted=False` field is a generator invariant and cannot answer which rows the optimizer consumed. Every inspected canonical row has its eligibility and exclusion sources in {link('REAL_ROW_ADMISSION_LEDGER.jsonl')}. Sources: {rowsource} and {source('work/src/student_pilot/ground_rows.py')}.

The demonstrated defects and their fixes are part of the final candidates patch: admission permits the same question-parser fallback as runtime when no manifest is configured, and distance parsing excludes a terminal parenthesized unit from the object phrase. Explicitly configured manifests still require the row entry. The recorded sample shows the rejected row and malformed operand; repaired findings include row text and source-member positions. The candidate patch, manifest, application evidence, final coverage and CPU proof are regenerated for these source changes. Sources: {link('REAL_ROW_DEFECT_B1.json')}, {rowsource}, {link('PATCH_MANIFEST.json')}.

The real package supplies neither candidate phrases nor a candidate manifest, so production for these rows uses the question parser. Admission independently derives its set from question/options. Runtime uses `s1_grounding.build_backend` → `GroundV3.config` → the real `routed_features.select_instances` membership guard. The check stops at geometry access after membership; it does not claim real masks were lifted. All {u['rows']} distance rows agree, with {u.get('disagreement',0)} disagreements. Source: {usource}.

Among eligible rows, {u['eligible_outside_sealed_eight_keys']} of {u['eligible_operands']} grounded operand occurrences lie outside the sealed eight keys. The sealed per-question universe would refuse {u['eligible_refused_by_sealed_question_universe']} occurrences. Across all rows before exclusions, the corresponding counts are {u['outside_sealed_eight_keys']} and {u['refused_by_sealed_question_universe']} of {u['operands']}. These are occurrence counts, not distinct phrases. Source: {usource}.

## CPU proof and coverage

The proof contains {proof['fixture_count']} base fixture kinds, {proof['orientation_cases']} orientation cases and {proof['epoch_cases']} ON/OFF cases. Every genuinely inverted copy refuses and every absolute ninety-degree roll passes. The near-nadir fixture has in-plane up approximately 0.03; the positive-margin fixture explicitly exercises a sealed guard pass with undefined heading. The unavailable-box case and actual MDG policy path are included. Source: {cpusource}.

OFF matches the sealed responses byte-for-byte for the {proof['sealed_replay_byte_equal']} inherited fixture kinds. Every metric value emitted by OFF equals ON. Heading-defined outputs match except for the required MDG repair; undefined headings print their status. Exact vertical lifting and marked MDG boxes can fail after the sealed guard passes, so added ON metrics in those cases are explicit exceptions to universal parity. Head calls also traverse the bound response path. Source: {cpusource}.

The final merged contract-suite outcomes are {summary['contract_suite']}; the integration tree's new tests are {summary['tree_suite']}. Tree failures require external record fixtures absent from the supplied snapshot. The standalone inherited SAM3 reference test also lacks its external file; the lane's sealed-source normalization fixture passes. Raw logs and every final test-ID disposition remain in {testsource}.

Changed executable-line coverage is {coverage_text}. Every changed executable line ran, including the rebased routing statements. Line evidence and test IDs: {link('CHANGED_LINE_COVERAGE_B2.md')}. These CPU fixtures do not measure model quality or real capture recovery.

## dev-S1 captures predicted to refuse

Records-derived, not a rerun: the raw-G3T proxy predicts sealed-guard refusal for 12 captures carrying 21 distance items; the head estimate spans 6–13 captures. The new guard is predicted to serve distance for all 12 proxy captures because their near-nadir references defer the convention check to usable upright frames. Heading-dependent outputs refuse wherever in-plane up is below 0.3. These are projections from {recordlink}, not measured patched admissions.

The same record describes 14 near-nadir captures, implying 2 proxy captures already passed the sealed guard; their heading-dependent outputs would also refuse where the threshold is unmet. Source: {recordlink}.

The first real check is the step-544 geometry tar `geometry_8c58df1547371bdb`, replayed on CPU through patched `GeometryContract.validate` and `LiveSession`. This lane will run that replay when the file arrives. The tar is not among the supplied inputs; no real-geometry result is claimed.
'''
(out/'CONTRACTS_REPORT.md').write_text(report)

design=f'''# Design record: contracts rebuild

The contract uses the reviewed gravity guard, a shared candidate identity, a per-row status audit and the marked MDG box bridge. One epoch boolean selects the contract throughout training, serving and replay. The model consumes RGB; tool numbers reach it as formatted text. Implementation and hashes: {link('PATCH_MANIFEST.json')}.

The guard and heading policy share the optical projection identity `||R[2,:2]||² = 1 − R[2,2]² = ||R[:2,2]||²`. Undefined heading withholds public coordinates and orientation while private original-world geometry supports metrics. The threshold is 0.3 in {source('work/src/student_pilot/geometry_profiles.py')}. A replacement heading basis would mix public coordinate conventions and is therefore excluded.

Candidate identity uses normalized full phrases. A supplied capture list defines candidate competition; absent a configured list, both admission and runtime parse question/options. An explicitly configured manifest remains mandatory for each named row. Terminal distance units are not part of an operand name. The real-row defect witness and complete agreement proof justify these narrow corrections: {link('REAL_ROW_DEFECT_B1.json')}, {rowsource}, {usource}.

A failed ground permits one different listed ground, then a direct answer. Calls after that retry, repeated names, operator faults and unrecognized responses defer the row. The supplied ruling defines this behavior: [trace ruling](/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md:276). Unknown templates can still require explicit candidate phrases; deferrals expose that missing binding.

The MDG bridge aliases already-cut points only when the marker declares the cut. Recutting would change the geometry. OFF replay preserves sealed behavior; ON intentionally repairs unavailable boxes and withholds undefined headings. Exact metric comparisons and explicit unavailable-output exceptions appear in {cpusource}.

Integration preserves the tree event-row branch and the contract heading branch. The edits commute byte-for-byte; only the geometry patch needs a hash-bound rebase. Application stages and verifies the full tree before installation. Sources: {link('INTEGRATION_MERGE_PROOF.json')}, {link('APPLY_PROOF.json')}.

The current proof covers all changed executable lines, full real-row scans and runnable integration tests. Missing record fixtures prevent a completely green integration suite. Actual training exposure cannot be reconstructed from pool membership alone. Sources: {link('CHANGED_LINE_COVERAGE_B2.md')}, {rowsource}, {testsource}.

The real-capture effect remains records-derived: 12 proxy captures / 21 distance items are predicted to regain distance service, with heading refusal below the threshold; the head range is 6–13 captures ({recordlink}). The pending step-544 `geometry_8c58df1547371bdb` CPU replay will test this prediction through the actual guard and live session.
'''
(out/'DESIGN_RECORD_contracts_rebuild_20261115.md').write_text(design)

body=f'''# Build 2 summary

The patch packet applies cleanly to the sealed base and the integration snapshot. The real-row audit and candidate-membership check pass. Sources: {link('APPLY_PROOF.json')}, {rowsource}, {usource}.

- The final candidates patch fixes demonstrated missing-manifest false positives and unit text in parsed object names. The patch, manifest and dependent final proofs are regenerated. Evidence: {link('REAL_ROW_DEFECT_B1.json')}, {link('PATCH_MANIFEST.json')}.
- All {distance['rows_read']} distance and {room['rows_read']} room programs pass admission in both source representations. Eligible pool counts are {distance['sealed_pool_eligible']} and {room['sealed_pool_eligible']}; actual optimizer membership is unavailable. Source: {rowsource}.
- All {u['rows']} distance rows agree with runtime membership. The sealed per-question universe would reject {u['eligible_refused_by_sealed_question_universe']} eligible operand occurrences; {u['eligible_outside_sealed_eight_keys']} of {u['eligible_operands']} fall outside its eight keys. Source: {usource}.
- The fixture proof covers {proof['orientation_cases']} orientation cases in both epochs. All {proof['inverted_refused']} inverted copies refuse; all {proof['rolled90_passed']} rolled copies pass. Exact-vertical lifting and MDG repair remain explicit parity exceptions. Source: {cpusource}.
- Contract-suite outcomes: {summary['contract_suite']}. Tree-suite outcomes: {summary['tree_suite']}; unavailable record fixtures explain its failures. Source: {testsource}.
- Coverage: {coverage_text}. Source: {link('CHANGED_LINE_COVERAGE_B2.md')}.
- Rehearsal seal: `{seal['tree_sha256']}`. Source: {link('INTEGRATION_SEAL.json')}.

Apply with {link('apply_contract_patches.sh')}; start with `--dry-run`. The only rebase is {link('PATCH_geometry_on_tree_r1.diff')}. The script requires the hash helper, manifest and patches beside it.

Real capture recovery remains a records-derived prediction until `geometry_8c58df1547371bdb` arrives. The planned CPU replay is specified in {link('CONTRACTS_REPORT.md')}. Retained test trees and staging are listed in [{L/'REMOVAL_CANDIDATES.md'}]({L/'REMOVAL_CANDIDATES.md'}).

Reader-facing text retains the sealed-versus-patched comparison because it defines replay behavior, and retains the defect/fix disclosure because the dispatch requires it.
'''
(out/'BUILD2_SUMMARY.md').write_text(body)

manifest=load('PATCH_MANIFEST.json')
manifest.update(build2_proofs={k:str(out/k) for k in ('APPLY_PROOF.json','INTEGRATION_MERGE_PROOF.json','INTEGRATION_SEAL.json','REAL_ROW_AUDIT.json','REAL_CANDIDATE_UNIVERSE.json','CPU_PROOF_B2.json','FINAL_TEST_RESULTS_B2.json','CHANGED_LINE_COVERAGE_B2.md')},integration_seal=seal['tree_sha256'])
save('PATCH_MANIFEST.json',manifest)
paths=sorted(p for p in (L/'work/trees').iterdir() if p.name.startswith(('.contracts-','b2_')))
paths+=sorted((L/'work').glob('b2_packet_*'))
rem=['# Retained temporary artifacts','','These paths are retained for user-managed cleanup. The rehearsal tree remains the integration result.','']
rem += ['- [ ] `'+str(p)+'`' for p in paths]
rem += ['- [ ] `'+str(L/'work/tmp')+'` — retained test fixtures and CPU proof logs.']
(L/'REMOVAL_CANDIDATES.md').write_text('\n'.join(rem)+'\n')
lane_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file());assert lane_bytes<3_000_000_000
names=['apply_contract_patches.sh','contract_hash_checks.py','PATCH_MANIFEST.json','PATCH_geometry.diff','PATCH_geometry_on_tree_r1.diff','PATCH_candidates.diff','PATCH_box.diff',
    'APPLY_PROOF.json','INTEGRATION_SEAL.json','INTEGRATION_MERGE_PROOF.json','REAL_ROW_AUDIT.json','REAL_ROW_ADMISSION_LEDGER.jsonl','REAL_CANDIDATE_UNIVERSE.json','CPU_PROOF_B2.json','CHANGED_LINE_COVERAGE_B2.md','COVERAGE_DETAIL_B2.json','FINAL_TEST_RESULTS_B2.json','CONTRACTS_REPORT.md','DESIGN_RECORD_contracts_rebuild_20261115.md','BUILD2_SUMMARY.md']
index={name:dict(path=str(out/name),bytes=(out/name).stat().st_size,sha256=hashlib.sha256((out/name).read_bytes()).hexdigest()) for name in names}
index['workspace']=dict(path=str(L),bytes=lane_bytes,limit_bytes=3_000_000_000)
save('PACKET_INDEX_B2.json',index)
print(json.dumps(dict(contract=summary['contract_suite'],tree=summary['tree_suite'],coverage={g:[v['executed'],v['total']] for g,v in coverage.items()},lane_bytes=lane_bytes),indent=2))
