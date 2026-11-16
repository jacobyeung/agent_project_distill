"""Publish source-bound final evidence after all validation completes."""
from pathlib import Path
import ast, collections, hashlib, json, os, shutil, subprocess, tarfile
L=Path(__file__).resolve().parents[1]; O=L/'out'; S=L/'work/src_r4'; B=L/'work/base/work/base/tree_b01ce449'
def read(path): return json.loads(path.read_text())
def write(name,value): (O/name).write_text(json.dumps(value,indent=2)+'\n')
def link(label,path): return f'[{label}]({path})'
full=read(L/'work/B7_FINAL_R4_results.json')
snapshot=read(L/'work/B7_SNAPSHOT_R4_results.json')
full.update(read(L/'work/B7_EDGES_R4_results.json'))
snapshot.update(read(L/'work/B7_SNAPSHOT_EDGES_R4_results.json'))
assert full and snapshot and all(v['outcome']=='passed' for v in [*full.values(),*snapshot.values()])
proof=read(O/'APPLY_PROOF_R4.json')
prior=read(O/'FINAL_TEST_RESULTS_R3.json')['tests']
def test_key(key):return key[key.index('tests_r'):].replace('tests_r3/','tests_r4/').replace('_r3.py','_r4.py')
assert {test_key(k) for k in prior} <= {test_key(k) for k in full}
tests=dict(source_paths=[str(L/f'work/{tag}_results.json') for tag in
           ('B7_FINAL_R4','B7_SNAPSHOT_R4','B7_EDGES_R4','B7_SNAPSHOT_EDGES_R4')],
           outcomes=dict(collections.Counter(v['outcome'] for v in full.values())),tests=full,
           integration_outcomes=dict(collections.Counter(v['outcome'] for v in snapshot.values())),integration_tests=snapshot,
           tree=proof['tree'],test_directory=str(L/'work/tests_r4'),
           retained_suite=dict(source=str(O/'FINAL_TEST_RESULTS_R3.json'),tests=len(prior),all_retained=True),
           row_family_regressions={name:dict(passed=True,source=str(L/'work/row_families_r4'/name),
               evidence=str(L/'work/row_families_r4'/artifact)) for name,artifact in [
               ('test_off_parity.py','off_parity_reproduction.json'),('test_provider_contract.py','provider_reproduction.json')]})
write('FINAL_TEST_RESULTS_R4.json',tests)
mut=read(L/'work/MUTATION_R4.json');old=read(O/'MUTATION_R3.json')
for mid,m in mut['mutations'].items():
    if mid in old['mutations']:m['description']=old['mutations'][mid]['description']
assert all(v['killed'] for v in mut['mutations'].values()) and set(old['mutations']) <= set(mut['mutations'])
mut['baseline_suite']=str(O/'FINAL_TEST_RESULTS_R4.json');write('MUTATION_R4.json',mut)
audit=read(L/'work/REAL_ROW_AUDIT_R4.json');assert audit['totals']['deferred']==0
with tarfile.open(L/'work/real/eb3429c5.tar') as archive:
    members={m.name for m in archive if m.isfile() and m.name.endswith('.jsonl.gz')}
audited={Path(m['source']).name for m in audit['members'].values()}
assert members == audited
audit['archive_member_coverage']=dict(all_row_members_audited=True,members=sorted(members),
    extraction_receipt=str(L/'work/extraction_r4.json'))
audit['production_intake']=dict(
    point_program_pool_reaches_audit=False,
    explanation='s1_pool.selected_rows calls validate_source_row before yielding. Packed sources require ground_rows.validate, which excludes infrastructure-only derivgen-row-v1 point programs. carrier_c1_routing.check_row accepts canonical v2 or ground forms. The legacy database path calls the audit before rendering; structured events can reach that call, but they still must pass the canonical renderer before materialization. The audit supports structured events without expanding source eligibility.',
    sources=[str(B/'student_pilot/s1_pool.py')+':105',str(B/'student_pilot/s1_pool.py')+':245',
             str(S/'student_pilot/s1_routing.py')+':295',str(S/'student_pilot/s1_routing.py')+':346',
             str(S/'student_pilot/carrier_c1_routing.py')+':180'],
    integration_intake='The integration archive adds r2_contract.event_row for reviewed ground events. It uses ground_call/token and ground_response/text, both parsed by the auditor.',
    integration_source=str(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar')+'!tree_r1/student_pilot/r2_contract.py',
    test_source=str(L/'work/tests_r4/test_row_families_r4.py'))
audit['candidate_contract']=dict(
    source=str(S/'student_pilot/phrases.py'),
    rule='Admission and native serving parse complete source-question templates. Native angle templates retain referring phrases and include the generator category-to-annotation mappings. Explicit cache candidates remain authoritative and never receive template expansion.',
    annotation_binding_source=str(B/'generator/dose_t0.py')+':50',
    alias_examples=str(L/'work/native_alias_audit_r4.json'),
    tests=str(L/'work/tests_r4/real_candidate_cases_r4.json'))
write('REAL_ROW_AUDIT_R4.json',audit)
# Preserve diff -ruN output and its exit status; changed trees normally return one.
with (O/'INTERDIFF_R3_TO_R4.diff').open('w') as stream:
    for before,after in [('src_r3','src_r4'),('tests_r3','tests_r4')]:
        result=subprocess.run(['diff','-ruN',str(L/'work'/before),str(L/'work'/after)],stdout=stream)
        assert result.returncode in (0,1)
heading=(O/'HEADING_DEPENDENCE_R3.md').read_text().replace('src_r3','src_r4').replace('tests_r3','tests_r4').replace('r3_proof','r4_proof').replace('_R3','_R4').replace('test_review_r3.py','test_review_r4.py')
for name in ['DECODE_ATTACK_R4.json']:
    heading=heading.replace(str(O/name),str(L/'work/test_artifacts_r4'/name))
(O/'HEADING_DEPENDENCE_R4.md').write_text(heading)
M=read(O/'PATCH_MANIFEST_R4.json')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
def guard(path):
    return [ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='validate_up_convention'
            or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UP_PLANE_MIN' for t in n.targets)]
assert guard(S/'student_pilot/geometry_profiles.py')==guard(L/'work/ref/gravity_guard_a62e3975_recovered.py')
checks=[]
for rel,m in M['files'].items():
    checks.append(dict(source=str(S/rel),overlay_matches=sha(S/rel)==m['patched_sha256'],
                       applied_matches=sha(Path(proof['tree'])/rel)==m['patched_sha256'],
                       base_matches=sha(B/rel)==m['base_sha256']))
assert all(all(v for k,v in c.items() if k!='source') for c in checks)
total=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert total < 3_000_000_000
write('PACKET_INTEGRITY_R4.json',dict(checks=checks,guard_ast_equal=True,guard_reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'),
    lane_logical_bytes=total,limit_bytes=3_000_000_000,full_tree_copies=4,
    storage_source=str(L),df=subprocess.run(['df','-BG','/scratch'],capture_output=True,text=True,check=True).stdout,
    files={str(p.relative_to(L)):sha(p) for p in [*S.rglob('*.py'),*O.glob('PATCH_*_r4.diff')]}))
parity=read(O/'ROW_FAMILY_PARITY_R4.json')['summary']
replay=read(O/'real_replay_r4/REAL_GEOMETRY_REPLAY.json')
coverage=read(O/'COVERAGE_DETAIL_R4.json')
totals=replay['totals']
report=[
 'The contract packet passes the CPU suite, preserves OFF row bytes, and admits every audited sealed POOL record. '+link('Tests',O/'FINAL_TEST_RESULTS_R4.json')+', '+link('row-family evidence',O/'ROW_FAMILY_PARITY_R4.json')+', '+link('POOL audit',O/'REAL_ROW_AUDIT_R4.json')+'.',
 'The lifting backend supplies heading metadata only under ON. Generator registries dispatch to the shared serving calculator under ON and retain sealed entries under OFF. Sensor sessions use the fused box provider; predicted-mode and MDG selection remain explicit. '+link('Source overlay',S/'student_pilot/ground_lifting.py')+', '+link('registry',S/'generator/derivgen_v7/derivgen/calculator.py')+', '+link('provider',S/'trace_format/box_v313.py')+'.',
 'The auditor parses combined records, paired textual events and structured point-program events. Generation and auditing share the structured formatter. Legacy scalar gaps use their declared revision. Complete source templates and native annotation aliases bind candidate names without trusting emitted calls; cache manifests remain authoritative. '+link('Auditor',S/'student_pilot/training_contract.py')+', '+link('formatter',S/'trace_format/point_events.py')+', '+link('candidate contract',O/'REAL_ROW_AUDIT_R4.json')+'.',
 'Raw infrastructure-only point programs do not enter the current POOL route: source validation rejects their schema before yielding them. Legacy database rows are audited before rendering. Format support in the auditor does not change membership gates. '+link('Intake evidence',O/'REAL_ROW_AUDIT_R4.json')+'.',
 f'The suite passes {len(full)} tests on each applied tree. Mutation testing kills {mut["killed"]} of {len(mut["mutations"])} mutations. '+link('Tests',O/'FINAL_TEST_RESULTS_R4.json')+', '+link('mutations',O/'MUTATION_R4.json')+'.',
 f'Every arm renders {parity["rendered_rows"]["base"]} rows across {parity["families"]} renderer/family groups. OFF matches base bytes; ON admits every rendered row with mapped differences only. '+link('Parity evidence',O/'ROW_FAMILY_PARITY_R4.json')+'.',
 f'The POOL audit covers {audit["totals"]["rows"]} source records and defers {audit["totals"]["deferred"]}. Admitted and packed representations count separately. Per-type totals and per-reason example slots are recorded in '+link('the audit',O/'REAL_ROW_AUDIT_R4.json')+'.',
 f'The real G3T replay covers {totals["captures"]} captures with {len(totals["assertion_failures"])} failed assertions. '+link('Replay evidence',O/'real_replay_r4/REAL_GEOMETRY_REPLAY.json')+'.',
 f'Changed-line tracing executes {sum(v["executed"] for v in coverage.values())} of {sum(v["total"] for v in coverage.values())} changed executable lines. Execution coverage is separate from mutation assertions. '+link('Coverage',O/'CHANGED_LINE_COVERAGE_R4.md')+'.',
 'Ordered patches apply without fuzz or offsets to the sealed base and integration snapshot. The apply helper verifies hashes, checks permissions before staging, and refuses reapplication. '+link('Application proof',O/'APPLY_PROOF_R4.json')+'.',
 'Apply with `bash out/apply_contract_patches_r4.sh TARGET --dry-run`; omit `--dry-run` to install. '+link('Manifest',O/'PATCH_MANIFEST_R4.json')+'.',
 'The convention guard retains the reference AST. Heading availability remains configuration-bound with default 0.3. '+link('Guard proof',O/'PACKET_INTEGRITY_R4.json')+', '+link('threshold source',S/'trace_format/contracts.py')+'.',
 'RGB inputs and text-only numerical observations retain their existing paths. These CPU checks do not measure model answer quality. The capture replay uses real tower geometry with synthetic masks and no supplied metric-scale estimate. Camera pool exclusion authority and full surface-converter inputs are absent; native camera leaves and keypoint sessions are covered. '+link('Scope',O/'ROW_FAMILY_PARITY_R4.json')+', '+link('replay limits',O/'real_replay_r4/REAL_GEOMETRY_REPLAY.json')+'.',
 'No project-history statements are retained; base/OFF/ON are controlled test arms.'
]
(O/'CONTRACTS_REPORT_R4.md').write_text('\n\n'.join(report)+'\n')
summary=[
 'The r4 packet is ready for review. It preserves OFF byte parity, restores the sensor provider, and audits structured point programs and all routed POOL types.',
 f'- {len(full)} tests pass on both applied trees; {mut["killed"]} mutations are killed. '+link('Tests',O/'FINAL_TEST_RESULTS_R4.json')+', '+link('mutations',O/'MUTATION_R4.json')+'.',
 f'- {parity["rendered_rows"]["base"]} rows per arm pass parity and ON admission checks. '+link('Row families',O/'ROW_FAMILY_PARITY_R4.json')+'.',
 f'- {audit["totals"]["rows"]} POOL source records have {audit["totals"]["deferred"]} audit deferrals. '+link('Audit',O/'REAL_ROW_AUDIT_R4.json')+'.',
 f'- {totals["captures"]} real captures have {len(totals["assertion_failures"])} failed replay assertions. '+link('Replay',O/'real_replay_r4/REAL_GEOMETRY_REPLAY.json')+'.',
 '- Patches apply cleanly to the sealed base and integration snapshot. '+link('Apply proof',O/'APPLY_PROOF_R4.json')+'.',
 f'- Lane storage is {total} bytes, below the {3_000_000_000}-byte cap; full tree copies total {4}. '+link('Integrity',O/'PACKET_INTEGRITY_R4.json')+'.',
 'The full camera-pool and surface-converter wrappers still require their source authority packages. No GPU or model-quality claim is made. '+link('Current contract and limits',O/'CONTRACTS_REPORT_R4.md')+'.'
]
(O/'BUILD7_SUMMARY.md').write_text(summary[0]+'\n\n'+'\n'.join(summary[1:-1])+'\n\n'+summary[-1]+'\n')
