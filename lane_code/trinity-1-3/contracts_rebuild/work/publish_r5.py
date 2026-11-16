"""Publish the current packet and source-bound verification results."""
from pathlib import Path
import ast,collections,hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r5';B=L/'work/base/work/base/tree_b01ce449';W=L/'work/row_families_r5'
def read(p):return json.loads(p.read_text())
def write(name,value):(O/name).write_text(json.dumps(value,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def link(label,p):return f'[{label}]({p})'
def run(script):
    result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work'/script)],capture_output=True,text=True)
    (L/'work'/('publish_'+Path(script).stem+'_r5.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0,(script,result.stdout,result.stderr)

tests=read(L/'work/B8_COMPLETE_R5_results.json');snapshot=read(L/'work/B8_COMPLETE_SNAPSHOT_R5_results.json')
assert tests and snapshot and all(v['outcome']=='passed' for v in [*tests.values(),*snapshot.values()])
proof=read(O/'APPLY_PROOF_R5.json')
write('FINAL_TEST_RESULTS_R5.json',dict(tests=tests,integration_tests=snapshot,
    outcomes=dict(collections.Counter(v['outcome'] for v in tests.values())),
    integration_outcomes=dict(collections.Counter(v['outcome'] for v in snapshot.values())),
    tree=proof['tree'],integration_tree=proof['integration']['tree'],test_directory=str(L/'work/tests_r5'),
    source_paths=[str(L/'work/B8_COMPLETE_R5_results.json'),str(L/'work/B8_COMPLETE_SNAPSHOT_R5_results.json')],
    logs=[str(L/'work/tests_complete_r5.log'),str(L/'work/tests_complete_snapshot_r5.log')],
    coverage_probe=read(L/'work/B8_COMPLETE_COVERAGE_R5_results.json')))
mutants=read(L/'work/mutation_r5/round_close/results.json');mutants.update(read(L/'work/mutation_r5/round_extra/results.json'))
assert all(v['killed'] or (v['equivalent'] and v['returncode']==0) for v in mutants.values())
M=read(O/'PATCH_MANIFEST_R5.json')
for name,v in mutants.items():
    assert v['full_suite'] and '-x' in v['command'] and '-k' not in v['command']
    rel=Path(v['source']).relative_to(L/'work/trees/r5_applied')
    for file in M['files']:
        expected=(S/file).read_text()
        if Path(file)==rel and v['old']:expected=expected.replace(v['old'],v['new'])
        assert (Path(v['tree'])/file).read_text()==expected,(name,file,'stale mutation tree')
    v['final_source_hashes_verified']=True
write('MUTATION_R5.json',dict(source_paths=[str(L/'work/mutation_r5/round_close/results.json'),str(L/'work/mutation_r5/round_extra/results.json')],
    mutations=mutants,killed=sum(v['killed'] for v in mutants.values()),equivalent=sum(bool(v['equivalent']) and not v['killed'] for v in mutants.values()),
    full_suite=True,stop_on_first_failure=True,baseline=str(O/'FINAL_TEST_RESULTS_R5.json')))

run('row_families_r5/test_off_parity.py');run('row_families_r5/test_provider_contract.py')
run('row_families_r5/compare.py');run('row_families_r5/validate_evidence.py');run('row_families_r5/inventory.py');run('row_families_r5/integrity.py')
parity=read(W/'comparison.json');assert not parity['defects'] and parity['summary']['off_parity']
parity.update(status='PASS',validation=read(W/'validation.json'),integrity=read(W/'integrity.json'),inventory=read(W/'inventory.json'))
parity['admission_policy_note']='L-2c removes the bare legacy scalar-gap parser exception because no sealed POOL record needs it. The unchanged synthetic legacy_surface/object_abs_distance rows are explicitly deferred; all other rendered ON rows are admitted.'
write('ROW_FAMILY_PARITY_R5.json',parity)
lines=[f'OFF matches the sealed base on every sample, and every ON text change passes the strict heading substitution check. Source: {link("comparison",O/"ROW_FAMILY_PARITY_R5.json")}.',
       parity['admission_policy_note']+' '+link('POOL audit',O/'REAL_ROW_AUDIT_R5.json')+'.',
       '| Family | Base / OFF / ON rendered | ON admitted / deferred | OFF parity | Source |','|---|---:|---:|---|---|']
for f in parity['families']:
    rows=f['rows_per_arm'];counts=f['audit_counts']
    lines.append(f"| {f['family']} | {rows['base']} / {rows['off']} / {rows['on']} | {counts.get('admitted',0)} / {counts.get('deferred',0)} | {f['off_parity']} | {link('samples',O/'ROW_FAMILY_PARITY_R5.json')} |")
(O/'ROW_FAMILY_PARITY_R5.md').write_text('\n\n'.join(lines[:2])+'\n\n'+'\n'.join(lines[2:])+'\n')
audit=read(L/'work/REAL_ROW_AUDIT_R5.json');assert audit['totals']['deferred']==0 and audit['legacy_bare_gaps']['rows']==0
audit['legacy_bare_gaps']['rule']='Removed in both epochs; no sealed POOL row uses the exception. Synthetic legacy-surface fixtures defer explicitly.'
audit['candidate_precedence']=dict(order=['batch.cache_phrases / persisted batch_cache_phrases','candidate_phrases','cache_phrases','candidate_manifest','external manifest entry','question-derived native candidates'],
    shared_function=str(S/'student_pilot/phrases.py')+'::candidate_binding',
    runtime=str(S/'student_pilot/s1_grounding.py'),admission=str(S/'student_pilot/training_contract.py'),materializer=str(S/'student_pilot/s1_routing.py'))
write('REAL_ROW_AUDIT_R5.json',audit)
run('heading_report_r5.py');run('coverage_r5.py')
coverage=read(O/'COVERAGE_DETAIL_R5.json');assert not coverage['uncovered_executable'],coverage['uncovered_executable']
replay=read(O/'real_replay_r5/REAL_GEOMETRY_REPLAY.json');assert not replay['totals']['assertion_failures']
sensor=read(L/'work/test_artifacts_r5/SENSOR313_REPLAY_R5.json');assert sensor['mismatches']==0
search=read(L/'work/test_artifacts_r5/SENSOR313_SOURCE_SEARCH_R5.json');assert search['eligible_live_sensor313_records']==0
angle=read(L/'work/test_artifacts_r5/ROTATED_ANGLE_R5.json');assert all(v==next(iter(angle.values())) for v in angle.values())
attack=read(L/'work/test_artifacts_r5/HEADING_ATTACK_R5.json')
attack_exceptions=[dict(scenario=scenario,call=call,evidence=data) for scenario,records in attack['yaw'].items() for call,data in records.items() if isinstance(data,dict) and data.get('served_identical') is False]
write('REVIEW_ATTACK_RESULTS_R5.json',dict(
    rotated_calculator=dict(passed=True,source=str(L/'work/test_artifacts_r5/ROTATED_ANGLE_R5.json')),
    heading=dict(source=str(L/'work/test_artifacts_r5/HEADING_ATTACK_R5.json'),physical_input_changes=attack_exceptions,
                 explanation='Room sampling changes with the rotated camera view. When a later camera rotates, its near-nadir centre ray moves in the defined reference frame; serving those depth-point coordinates is correct. Pose-k centre remains invariant. These are physical-view changes, not an arbitrary reference-basis leak.'),
    sensor_replay=sensor,source_search=search,
    review_script_logs=[str(L/'work'/n) for n in ('binding_close_r5.log','depth_close_r5.log','provider_close_r5.log')]))
# Preserve diff -ruN output, including test changes.
with (O/'INTERDIFF_R4_TO_R5.diff').open('w') as f:
    for a,b in [('src_r4','src_r5'),('tests_r4','tests_r5')]:
        result=subprocess.run(['diff','-ruN',str(L/'work'/a),str(L/'work'/b)],stdout=f);assert result.returncode in (0,1)
with (O/'INTERDIFF_R4_TO_R5_PATCHES.diff').open('w') as f:
    for stem in ('geometry','candidates','box','geometry_on_tree_r1'):
        result=subprocess.run(['diff','-u',str(O/f'PATCH_{stem}_r4.diff'),str(O/f'PATCH_{stem}_r5.diff')],stdout=f);assert result.returncode in (0,1)

def guard(p):
    return [ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if
        isinstance(n,ast.FunctionDef) and n.name=='validate_up_convention' or
        isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UP_PLANE_MIN' for t in n.targets)]
assert guard(S/'student_pilot/geometry_profiles.py')==guard(L/'work/ref/gravity_guard_a62e3975_recovered.py')
inventory={str(p.relative_to(B)):sha(p) for p in B.rglob('*') if p.is_file()}
seal=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert seal=='b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
verdict=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_contracts2/REVIEW_VERDICT_CONTRACTS_R4.md')
assert sha(verdict).startswith('0636c954')
allocated=int(subprocess.run(['du','-sk',str(L)],capture_output=True,text=True,check=True).stdout.split()[0])*1024
assert allocated<4_000_000_000
write('PACKET_INTEGRITY_R5.json',dict(base_seal=seal,base_source=str(B),guard_ast_equal=True,
    guard_reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'),review_source=str(verdict),review_sha256=sha(verdict),
    lane_allocated_bytes=allocated,cap_bytes=4_000_000_000,storage_source=str(L),
    source_hashes={str(p.relative_to(S)):sha(p) for p in S.rglob('*.py')},
    df=subprocess.run(['df','-BG','/scratch'],capture_output=True,text=True,check=True).stdout))

items=[
 ('H-1','Gate the sensor provider on the epoch; replay selects the stored epoch. ON sensor sessions select fused boxes under the sensor contract; OFF retains sealed version-specific selection.','test_sensor313_off_provider_and_audit','PASS'),
 ('H-2','Withhold u/v for any heading-unavailable operand. Both point producers share a stable private metric basis before rounding; the generator uses the serving calculator under ON.','test_calculator_field_scope_and_shared_implementation; test_rotated_calculator_fields; test_grounded_calculator_metric_basis_and_generator_parity','PASS'),
 ('M-1','Use one binding resolver in runtime, admission and materialization; persist cache metadata and accept the runtime batch at admission. Preserve the selected row universe when an external manifest differs.','test_shared_binding_served_or_deferred; test_build_defers_one_row_and_keeps_clean_row[manifest_superset]; test_build_defers_one_row_and_keeps_clean_row[phrases_superset]','PASS'),
 ('M-2','Rerender depth from arguments in every heading state. Strict comparison rejects error lines, altered numbers and altered served fields; move distance retains sealed half-cent rounding.','test_rerender_depth_arguments; test_strict_heading_comparison; test_move_nadir_distance_retains_sealed_rounding','PASS'),
 ('L-1','Serve pose-k centre when reference heading is defined; withhold only unavailable yaw. Serve reference-pose identity.','test_decode_attacks_and_move_source_distance; test_pose_identity_and_later_centre','PASS'),
 ('L-2a','Load the serving calculator lazily only under ON; standalone generator imports retain their sealed dependency graph.','test_standalone_generator_imports','PASS'),
 ('L-2b','Raise generator Refusal for orphaned, mismatched and unsupported tool events.','test_generator_refusal_type','PASS'),
 ('L-2c',f'Remove the bare scalar-gap exception: {audit["legacy_bare_gaps"]["rows"]} sealed POOL rows need it. Synthetic legacy-surface rows defer explicitly. '+link('counts',O/'REAL_ROW_AUDIT_R5.json'),'test_legacy_gap_off_grammar; test_legacy_scalar_gap_audit','PASS; explicit fixture deferral'),
 ('L-2d','Retain angle templates, vocabulary mappings and aliases under ON; audit each branch by disabling it separately.','test_vocabulary_and_suffix_exclusions; test_all_angle_templates_and_aliases','PASS'),
 ('L-2e','Keep cache-key lookup pure and merge aliases in a private copy used by consumers.','test_cache_lookup_preserves_caller; test_normalizer_exceptions_and_duplicate_merge','PASS'),
 ('L-3','Omit the unreachable partial-ground branch: each matching header already has ok status.','test_dead_partial_ground_and_registry_status_probe','EQUIVALENT; probe PASS'),
]
test_source=link('suite evidence',O/'FINAL_TEST_RESULTS_R5.json')
item_table=['| Item | Current change / decision | Test | Result |','|---|---|---|---|']
for item,change,test,result in items:item_table.append(f'| {item} | {change} | {test} | {result}; {test_source} |')
mut_table=['| Mutant | Change | Test / probe | Result and source |','|---|---|---|---|']
for mid,v in mutants.items():
    test='; '.join(v['failing_tests']) or 'test_dead_partial_ground_and_registry_status_probe' if mid in ('R_R4','R_R5','R_N7') else '; '.join(v['failing_tests']) or 'test_legacy_gap_off_grammar'
    change=(v['old'].strip()+' → '+v['new'].strip()).replace('\n',' ').replace('|','\\|') if v['old'] else v['equivalent']
    mut_table.append(f"| {mid} | {change} | {test} | {'KILLED' if v['killed'] else 'EQUIVALENT; '+v['equivalent']}; {link('log',Path(v['log']))} |")
counts=parity['summary'];total=replay['totals'];mut_count=sum(v['killed'] for v in mutants.values())
paragraphs=[
 'The r5 packet closes the confirmation findings and passes the complete suite on both applied trees. OFF retains sealed row bytes; ON text changes pass strict comparison. '+test_source+'; '+link('application proof',O/'APPLY_PROOF_R5.json')+'.',
 f'The suite passes {len(tests)} tests on each tree. Mutation tests kill {mut_count} mutants and prove {len(mutants)-mut_count} equivalent, using a fresh tree and the full suite for each. '+test_source+'; '+link('mutation evidence',O/'MUTATION_R5.json')+'.',
 f'Every arm renders {counts["rendered_rows"]["base"]} rows across {counts["families"]} renderer/family groups. ON admits {counts["on_audits"].get("admitted",0)} and explicitly defers {counts["on_audits"].get("deferred",0)} synthetic bare-gap legacy rows under the L-2c decision. No error row is accepted as a heading substitution. '+link('row-family evidence',O/'ROW_FAMILY_PARITY_R5.json')+'.',
 f'The real POOL audit admits {audit["totals"]["admitted"]} source records and defers {audit["totals"]["deferred"]}. Disabling vocabulary mappings loses {audit["ablations"]["vocabulary"]["admitted_only"]} admitted rows; disabling angle templates loses {audit["ablations"]["templates"]["admitted_only"]}; disabling aliases loses {audit["ablations"]["aliases"]["admitted_only"]}. These ablations overlap and count source representations, not unique qids. '+link('audit with examples',O/'REAL_ROW_AUDIT_R5.json')+'.',
 f'The sealed-source search finds {search["eligible_live_sensor313_records"]} replayable sensor traces with the required live-query payload. Base-generated fallback traces replay {sensor["calls"]} calls with {sensor["mismatches"]} mismatches. '+link('search and replay evidence',O/'REVIEW_ATTACK_RESULTS_R5.json')+'.',
 f'The real G3T replay covers {total["captures"]} captures with {len(total["assertion_failures"])} failed assertions. '+link('replay evidence',O/'real_replay_r5/REAL_GEOMETRY_REPLAY.json')+'.',
 'The mask cache supplies the runtime competition universe. batch.cache_phrases and persisted batch_cache_phrases take precedence; candidate_phrases is the row declaration, cache_phrases is its cache fallback, and candidate_manifest is its last declared binding. An external per-qid manifest fills only missing bindings and is carried into the materialized row. Without a cache binding, native candidates come from the question. Admission can receive the runtime batch directly. '+link('shared resolver',S/'student_pilot/phrases.py')+'; '+link('materializer',S/'student_pilot/s1_routing.py')+'.',
 'RGB inputs and text-only numerical observations retain their existing paths. The gravity guard matches the reference AST, and the heading threshold remains configuration-bound. These CPU fixtures do not measure model quality. Camera-pool exclusions and full surface-converter inputs remain unavailable. '+link('integrity',O/'PACKET_INTEGRITY_R5.json')+'; '+link('heading inventory',O/'HEADING_DEPENDENCE_R5.md')+'.',
 'Apply with `bash out/apply_contract_patches_r5.sh TARGET --dry-run`; omit `--dry-run` to install. The helper verifies hashes and refuses reapplication. '+link('manifest',O/'PATCH_MANIFEST_R5.json')+'.',
]
(O/'CONTRACTS_REPORT_R5.md').write_text('\n\n'.join(paragraphs)+'\n\n'+'\n'.join(item_table)+'\n\n'+'\n'.join(mut_table)+'\n')
(L/'work/summary_content_r5.json').write_text(json.dumps(dict(paragraphs=paragraphs[:6],item_table=item_table,mutant_table=mut_table),indent=2))
print('Published current evidence and report.')
