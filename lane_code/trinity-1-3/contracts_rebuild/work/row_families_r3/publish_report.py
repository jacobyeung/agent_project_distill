"""Write the requested reports once; preserve all packet and source files."""
import copy,json
from collections import Counter
from pathlib import Path
L=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
J=L/'out/ROW_FAMILY_PARITY_R3.json';MD=L/'out/ROW_FAMILY_PARITY_R3.md'
data=json.loads((W/'comparison.json').read_text())
validation=json.loads((W/'validation.json').read_text())
integrity=json.loads((W/'integrity.json').read_text())
inventory=json.loads((W/'inventory.json').read_text())
assert validation['all_evidence_checks_pass'] and integrity['all_hashes_match'] and integrity['under_limit']
assert not J.exists() and not MD.exists()
def production(r):
    f=r['family']
    if f.startswith('point_program/'):return ['generator/derivgen_v7/derivgen/program.py']
    if f.startswith('production_direction/'):return ['generator/ground_rows_out/render_full.py','generator/ground_rows_out/render_gaps_v314.py','generator/derivgen_v7/derivgen/programs_v314.py','generator/derivgen_v7/derivgen/ground_v312.py']
    if f.startswith('production_annotation/'):return ['generator/ground_rows_out/render_full.py','generator/derivgen_v7/derivgen/ground_v313_distance.py','generator/derivgen_v7/derivgen/box_v313.py']
    if f.startswith('ground/'):return ['generator/ground_rows_out/render_programs_v314.py','generator/derivgen_v7/derivgen/programs_v314.py']
    if f.startswith('legacy_surface/'):return ['generator/derivgen_v7/derivgen/ground_v312.py']
    if f.startswith('keypoints/'):return ['generator/derivgen_v7/derivgen/ground_v313.py','trace_format/ground_v313.py','student_pilot/e2e_routing_rows.py']
    if f.startswith('routing/'):return ['student_pilot/carrier_c1_routing.py']
    if f.startswith('runtime/'):return ['student_pilot/carrier_c1_decode.py','student_pilot/live_trace313.py','student_pilot/e2e_routing_rows.py']
    if f.startswith('recovery/'):return ['generator/derivgen_v7/derivgen/ground_v313.py','student_pilot/ground_rows.py']
    if f.startswith('headcall/'):return ['headcall/rows.py','headcall/derive.py']
    if f.startswith('pointing/'):return ['student_pilot/carrier_c1_data.py']
    if f.startswith(('camera/','camera_leaf/')):return ['generator/derivgen_v7/derivgen/camera_rows.py']
    if f=='room/prepared':return ['generator/ground_rows_out/render_room_v314.py','generator/derivgen_v7/derivgen/room_rows_v314.py']
    if f=='adapter/native':return ['student_pilot/e2e_routing_rows.py','student_pilot/carrier_c1_routing.py']
    if f=='adapter/ground':return ['student_pilot/ground_rows.py']
    if f=='control/canon_generate':return ['generator/derivgen_v7/derivgen/canon.py']
    if f=='control/canonical_route':return ['generator/derivgen_v7/derivgen/canon_render.py']
    if f=='control/pose_only':return ['student_pilot/pose_samples.py']
    if f=='control/recording_pose':return ['student_pilot/recording_pose.py']
    if f.startswith('control/head_program_'):return ['student_pilot/head_programs.py']
    if f.startswith('control/timestamp_count_'):return ['student_pilot/trace_targets.py']
    raise AssertionError(f)

for r in data['families']:
    r['production_source_paths']=[str(L/'work/base/work/base/tree_b01ce449'/p) for p in production(r)]
    r['patched_production_source_paths']=[str(L/'work/trees/r6_r3'/p) for p in production(r)]
    r['on_contract_changes']=dict(Counter(d['contract_change'] or 'UNEXPLAINED_PROVIDER_AUDIT_CHANGE' for s in r['samples'] for d in s['differences']))
    r['audit_note']='Original returned row audited both without context and with its declared synthetic GT candidate manifest; no text or events were altered.'

data['status']='FAIL: OFF/base parity and allowed ON differences'
data['summary']['semantic_program_families']=len(next(c['detail'] for c in validation['checks'] if c['name']=='native_semantic_family_enumeration'))
data['summary']['family_count_definition']='Distinct renderer/family groups, including versioned paths, adapters and controls; not distinct semantic question types.'
data['summary']['source_path']=str(J)
data['setup']=json.loads((W/'setup.json').read_text())
data['integrity']=integrity
data['validation']=validation
data['inventory']=inventory
data['candidate_binding_source']=str(W/'candidate_bindings.json')
data['fixtures']=[str(W/n) for n in ('render_arms.py','extra_families.py','program_families.py','supplement.py')]+[str(L/'work/tests_r3/generator_fixture_r3.py'),str(L/'work/tests_r3/fixtures_contracts.py')]
data['scope_notes']=[
 'The semantic inventory includes every FAMILIES/F17 entry in the base bindings module, plus program-dispatch additions, room preparation, pose/recording rows, pointing present/absent rows, HC/HX/HA sidecars, runtime MDG, recovery and keypoint fragments.',
 'Point-program samples invoke the native Program.execute renderer. They are synthetic pinhole/GT-style scenes and do not assert the outer generate wrapper native-annotation reference gate or dataset eligibility.',
 'Ground samples reuse the r3 sensor-calibration fixture with declared GT instance rasters. Labels are frozen from base fixture geometry for parity, not independent benchmark-accuracy evidence.',
 'production_direction uses the actual legacy Session branch selected by render_full/render_gaps. ground/direction separately tests the v3.14 program dispatcher with its modern session.',
 'production_annotation uses the exact AnnotationBoxProvider and distance prepare/make_session branch selected by render_full. ground/distance tests the fused provider used in the supplied r3 fixture.',
 'The contract auditor defers legacy structured point-program events with contract_missing_response; their text/response envelope must be converted to the canonical event format before this auditor can admit them. Base rows under ON auditing have the same reason.',
 'No row requires a GPU to execute its sampled per-row renderer. Full camera-pool and surface-conversion wrappers require the missing authority/input artifacts listed separately.'
]
data['findings']=[
 dict(id='D1',severity='blocking',title='The lifting backend passes a new keyword into the sealed generator registry even with the flag OFF',
      mechanism='student_pilot.ground_lifting.render_ground always passes heading_defined. derivgen.calculator.PrintedPointRegistry.register lacks that parameter. OFF selects the sealed generator Session; production legacy direction/surface sessions keep that registry in both epochs.',
      source_paths=[str(L/'work/trees/r6_r3/student_pilot/ground_lifting.py')+':178',str(L/'work/trees/r6_r3/generator/derivgen_v7/derivgen/calculator.py')+':157',str(L/'work/trees/r6_r3/generator/derivgen_v7/derivgen/ground_v312.py')+':49'],
      reproduction=str(W/'test_off_parity.py'),evidence=str(W/'off_parity_reproduction.json'),log=str(W/'off_parity_reproduction.log')),
 dict(id='D2',severity='unexplained_contract_change',title='ON changes the default provider audit on retained sensor keypoint rows',
      mechanism='A sensor session with multi_instance=False defaults to FusedBoxProvider in the generator, but ON dispatches to the runtime provider_for(sensor, 3.13), which selects the best-frame provider. The positive-heading response text is identical while audit.box_provider changes from fit_gbox_fused_full_v1 to fit_gbox_best_v1. None of the named contract changes explains this metadata switch.',
      source_paths=[str(L/'work/trees/r6_base/generator/derivgen_v7/derivgen/ground_v313.py')+':104',str(L/'work/trees/r6_r3/trace_format/ground_v313.py')+':118',str(L/'work/trees/r6_r3/trace_format/box_v313.py')],
      reproduction=str(W/'test_provider_contract.py'),evidence=str(W/'provider_reproduction.json'),log=str(W/'provider_reproduction.log'))]
data['unrenderable_with_supplied_inputs']=[
 dict(families=['camera/camera_displacement','camera/camera_movement_direction','camera/camera_rotation'],entry_point='derivgen.camera_rows.camera_rows',touched=False,
      missing_inputs=[dict(path='/scratch/jjyeung/orch_cd/streams2/work/flt/RESTI_EXCLUSIONS_20261109.json',sha256='ec38428b2c720956894eb16bd91e74fd6d86a8389cecdb715842dbd9a3c85415')],
      source_path=str(L/'work/base/work/base/tree_b01ce449/generator/derivgen_v7/derivgen/goal_exclusions.py'),evidence=str(W/'base.json'),
      coverage='The native _row camera renderer is sampled in all arms; the exclusion gate was not overridden.'),
 dict(families=['surface_conversion/nearest_surface'],entry_point='derivgen.surface_rows_v313.convert',touched=True,
      missing_inputs=['pairs_path JSONL containing source pairs/instances/witnesses','review_path JSONL with matching nearest_surface rows and pinned depth/calibration/mask inputs','summary_path JSON with source reference','hrp_root/out/local_sources.json','hrp_root/work/hrp.py','hrp_root/work/keypoints.py','tokenizer_path tokenizer JSON'],
      source_path=str(L/'work/base/work/base/tree_b01ce449/generator/derivgen_v7/derivgen/surface_rows_v313.py')+':60',
      coverage='Native Session surface_pair/extent_ends fragments are sampled; authoritative HRP-source conversion is not claimed.',rows_per_arm=dict(base=0,off=0,on=0),audit_verdicts=[])
]
data['writing_note']='No project-history statements were retained; base/OFF/ON are the requested controlled comparisons.'

def link(label,p):return f'[{label}]({p})'
s=data['summary'];num_source=link('JSON report',J)
lines=[
 f'**r3 fails row-family parity.** OFF cannot render bare-ground rows that base renders, and ON changes keypoint provider audits without a named contract justification. Both defects have failing reproductions. Source: {num_source}.',
 f'The sample covers {s["semantic_program_families"]} semantic program families across {s["families"]} renderer/family groups. It renders {s["rendered_rows"]["base"]} base rows, {s["rendered_rows"]["off"]} OFF rows and {s["rendered_rows"]["on"]} ON rows. Sources: {link("coverage checks",W/"validation.json")}, {num_source}.',
 f'Every ON row was audited. With the declared GT candidate binding, {s["on_audits"].get("admitted",0)} rows are admitted and {s["on_audits"].get("deferred",0)} defer. Served near-nadir absolute-distance rows are admitted for both fused and native-annotation providers. Sources: {num_source}, {link("candidate bindings",W/"candidate_bindings.json")}.',
 'The table counts emitted rows, not successful attempts at a refused renderer. B/OFF/ON columns use the same fixture inputs. A deferred audit is separate from a renderer exception. Every numeric table cell comes from the linked row artifacts and this report’s per-family JSON record.',
 '| Family / entry point | Touched path | B / OFF / ON | OFF parity | ON audit: admitted / deferred | ON differences or blocker | Sources |',
 '|---|---|---:|---|---:|---|---|'
]
for r in data['families']:
    counts=r['rows_per_arm'];aud=r['audit_counts'];changes=[]
    if not r['off_parity']:changes.append('D1')
    if 'UNEXPLAINED_PROVIDER_AUDIT_CHANGE' in r['on_contract_changes']:changes.append('D2')
    changes += [k.replace('_',' ') for k in r['on_contract_changes'] if not k.startswith('UNEXPLAINED')]
    if not any(counts.values()):changes=['Missing pinned exclusion authority']
    if r['audit_reasons']:changes+=list(r['audit_reasons'])
    sources=' '.join(link(arm, next(iter(r['samples']))['source_paths'][arm]) for arm in ('base','off','on'))
    parity='FAIL' if not r['off_parity'] else 'refusal only' if not counts['base'] else 'PASS'
    lines.append(f'| `{r["family"]}` — `{r["entry_point"]}` | {"yes" if r["touched"] else "no"} | {counts["base"]} / {counts["off"]} / {counts["on"]} | {parity} | {aud.get("admitted",0)} / {aud.get("deferred",0)} | {"; ".join(changes) or "unchanged"} | {sources} |')
lines.append(f'| `surface_conversion/nearest_surface` — `derivgen.surface_rows_v313.convert` | yes | 0 / 0 / 0 | not tested | 0 / 0 | Missing HRP source inputs; native fragments covered above | {num_source} |')
lines += [
 f'**D1: bare-ground registry incompatibility.** The patched {link("lifting formatter",L/"work/trees/r6_r3/student_pilot/ground_lifting.py")} supplies `heading_defined` unconditionally. The {link("sealed generator registry",L/"work/trees/r6_r3/generator/derivgen_v7/derivgen/calculator.py")} does not accept it. OFF fails for modern-session direction/keypoint rows; both OFF and ON fail for the production legacy direction and surface-distance paths. This is a code defect, not missing fixture data. Source: {link("failing reproduction",W/"off_parity_reproduction.json")}.',
 f'Run the intentionally failing regression: `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" XDG_CACHE_HOME={L}/work/.cache /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B {W}/test_off_parity.py`. It asserts complete OFF/base row equality. Source and retained failure: {link("test",W/"test_off_parity.py")}, {link("log",W/"off_parity_reproduction.log")}.',
 f'**D2: unexplained provider audit change.** ON changes `fit_gbox_fused_full_v1` to `fit_gbox_best_v1` for sensor keypoint sessions. Defined-heading text stays identical; the provider audit changes. The full JSON lists every changed audit field, including near-nadir cases. Sources: {link("provider reproduction",W/"provider_reproduction.json")}, {num_source}.',
 f'Run the intentionally failing regression: `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" XDG_CACHE_HOME={L}/work/.cache /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B {W}/test_provider_contract.py`. Source and retained failure: {link("test",W/"test_provider_contract.py")}, {link("log",W/"provider_reproduction.log")}.',
 f'Every other observed ON difference is mapped in the JSON to heading fields withheld, metric-only box/camera operands, or the MDG bridge. Text-length and span-offset changes are recorded alongside their underlying text changes. Open-vocabulary and normalized-phrase samples are included even where no output changes. Source: {num_source}.',
 f'The auditor returns `contract_missing_response` for the retained structured point-program event format. The same base records receive that verdict under ON auditing, so this result does not establish a new rendering regression. Unbound ground records can also defer for missing candidate context; both raw and manifest-bound verdicts are retained. Sources: {num_source}, {link("audit implementation",L/"work/trees/r6_r3/student_pilot/training_contract.py")}.',
 '**Wrappers that cannot complete with the supplied inputs:**',
 f'- `camera_rows.camera_rows` needs `/scratch/jjyeung/orch_cd/streams2/work/flt/RESTI_EXCLUSIONS_20261109.json`, with SHA-256 `ec38428b2c720956894eb16bd91e74fd6d86a8389cecdb715842dbd9a3c85415`. Its native per-row renderer is covered; the pool gate remains intact. Source: {link("exclusion authority declaration",L/"work/base/work/base/tree_b01ce449/generator/derivgen_v7/derivgen/goal_exclusions.py")}.',
 f'- `surface_rows_v313.convert` needs its pair JSONL, matching reviewed nearest-surface JSONL, summary JSON, pinned depth/calibration/mask inputs, `hrp_root/out/local_sources.json`, `hrp_root/work/hrp.py`, `hrp_root/work/keypoints.py`, and tokenizer JSON. Native surface/extent fragments are covered. Source: {link("converter input contract",L/"work/base/work/base/tree_b01ce449/generator/derivgen_v7/derivgen/surface_rows_v313.py")}.',
 f'The fixtures use production per-row renderers, GT-style sensor geometry and pinhole controls. They do not establish benchmark accuracy, full pool admission, or model quality. The source inventory, production caller paths, immutable arm artifacts, byte hashes and every ON difference are in {num_source}.',
 f'Both fresh trees match their packet hashes. Lane storage at the recorded check is {integrity["lane_logical_bytes"]} bytes, below the requested {integrity["limit_bytes"]}-byte cap; the report files add only text. Source: {link("integrity check",W/"integrity.json")}. Existing packet files and source trees were not edited. No project-history statements were retained.'
]
J.open('x').write(json.dumps(data,indent=2,allow_nan=False)+'\n')
MD.open('x').write('\n\n'.join(lines[:4])+'\n\n'+'\n'.join(lines[4:4+2+len(data['families'])+1])+'\n\n'+'\n\n'.join(lines[4+2+len(data['families'])+1:])+'\n')
print(json.dumps(dict(json=str(J),markdown=str(MD),status=data['status'])))
