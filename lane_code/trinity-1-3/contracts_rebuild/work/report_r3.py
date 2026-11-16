from pathlib import Path
import ast,collections,hashlib,json,os
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r3';B=L/'work/base/work/base/tree_b01ce449'
def read(p):
    assert p.stat().st_size<20_000_000,p
    return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def link(name):return f'[{name}]({O/name})'
results={};sources=[]
for tag in ('FINAL_APPLIED_R3','EXTRA_R3','CLASS_API_R3','SNAPSHOT_R3'):
    p=O/f'{tag}_results.json'
    if p.exists():
        values=read(p);assert all(v['outcome']=='passed' for v in values.values()),p
        if tag!='SNAPSHOT_R3':results.update(values)
        sources.append(str(p))
counts=dict(collections.Counter(v['outcome'] for v in results.values()))
assert counts and set(counts)=={'passed'}
(O/'FINAL_TEST_RESULTS_R3.json').write_text(json.dumps(dict(source_paths=sources,outcomes=counts,tests=results,
    tree=str(L/'work/trees/r3_proof/base'),test_directory=str(L/'work/tests_r3')),indent=2)+'\n')
replay=read(O/'real_replay_r3/REAL_GEOMETRY_REPLAY.json');cov=read(O/'COVERAGE_DETAIL_R3.json')
apply=read(O/'APPLY_PROOF_R3.json');manifest=read(O/'PATCH_MANIFEST_R3.json');mut=read(O/'MUTATION_R3.json')
audit=read(O/'REAL_ROW_AUDIT_R3.json')
assert not replay['totals']['assertion_failures'] and not audit['failures']
assert len(mut['mutations'])>=18 and all(v['killed'] for v in mut['mutations'].values())
inventory=L/'work/base/out/BASE_FILES_b01ce449.sha256';base={}
for line in inventory.read_text().splitlines():
    h,rel=line.split('  ',1);assert sha(B/rel)==h,rel;base[Path(rel).as_posix()]=h
seal=hashlib.sha256(json.dumps(base,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert seal==manifest['base_seal'],seal
for epoch in ('','_R2'):
    old=read(O/f'PATCH_MANIFEST{epoch}.json')
    assert all(sha(O/name)==h for name,h in old['patch_sha256'].items())
    overlay=L/('work/src_r2' if epoch else 'work/src')
    assert all(sha(overlay/rel)==e['patched_sha256'] for rel,e in old['files'].items())
ref=ast.parse((L/'work/ref/gravity_guard_a62e3975_recovered.py').read_text());actual=ast.parse((S/'student_pilot/geometry_profiles.py').read_text())
fn=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_up_convention')
const=lambda tree:next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UP_PLANE_MIN' for t in n.targets))
assert ast.dump(fn(ref))==ast.dump(fn(actual)) and ast.dump(const(ref))==ast.dump(const(actual))
assert all(sha(L/'work/trees/r3_proof/base'/rel)==e['patched_sha256'] for rel,e in manifest['files'].items())
total=sum((Path(root)/name).stat().st_size for root,dirs,files in os.walk(L) for name in files if not (Path(root)/name).is_symlink())
assert total<3_000_000_000,total
integrity=dict(source=str(O/'PATCH_MANIFEST_R3.json'),base_inventory_source=str(inventory),base_files_verified=len(base),base_seal=seal,
    prior_packet_patch_hashes_unchanged=True,prior_overlay_hashes_unchanged=True,guard_function_ast_equal=True,
    guard_constant_ast_equal=True,guard_reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'),
    applied_tree_matches_manifest=True,lane_bytes_at_check=total,lane_source=str(L))
(O/'PACKET_INTEGRITY_R3.json').write_text(json.dumps(integrity,indent=2)+'\n')
t=replay['totals'];covered=sum(v['executed'] for v in cov.values());changed=sum(v['total'] for v in cov.values())
report=[
f"The contract packet passes {counts['passed']} CPU tests and kills every tested mutation. The patches apply to the sealed base and integration snapshot without fuzz or offsets. Sources: {link('FINAL_TEST_RESULTS_R3.json')}, {link('MUTATION_R3.json')}, {link('APPLY_PROOF_R3.json')}.",
f"A served ground remains usable for metric calls when its heading or size is unavailable. True ground failures allow only a different named retry and a direct answer. Generator entry points retain subclassable classes in both epochs. OFF reproduces the sealed generator fixture outputs byte for byte; ON changes only the documented heading fields and their private replay metadata. Sources: {link('GENERATOR_PARITY_R3.json')}, {link('REVIEW_DISPOSITION_R3.md')}.",
f"Move uses its source heading, turn uses both endpoint headings, and pose horizontal fields and yaw require the reference and queried headings. Depth horizontal coordinates in the reference frame require the reference heading. Metric fields remain available. Calculator dispatch has no heading gate. Source: {link('HEADING_DEPENDENCE_R3.md')}.",
f"Cache-backed admission requires the capture's phrase binding. Admission and serving share candidate construction; cache names determine the runtime universe. Malformed records defer locally, and materialization records bounded qid examples with full counts. Sources: {link('REAL_ROW_AUDIT_R3.json')}, {link('FINAL_TEST_RESULTS_R3.json')}.",
f"The replay covers {t['captures']} captures with {len(t['assertion_failures'])} failed assertions. OFF equals base response bytes. The ON guard serves all captures; the sealed guard refuses {t['sealed_refused']}. Source: {link('real_replay_r3/REAL_GEOMETRY_REPLAY.json')}.",
f"Changed-line tracing executes {covered} of {changed} changed executable statements. Execution coverage and mutation assertions are reported separately. Sources: {link('CHANGED_LINE_COVERAGE_R3.md')}, {link('MUTATION_R3.json')}.",
f"Apply with `bash out/apply_contract_patches_r3.sh TARGET --dry-run`, then omit `--dry-run` to install. The operator refuses non-writable targets before staging, verifies source and destination hashes, and refuses reapplication. Source: {link('APPLY_PROOF_R3.json')}.",
f"The convention guard and its constant retain the reviewed AST. The heading threshold remains configuration-bound with default 0.3. Sources: {link('PACKET_INTEGRITY_R3.json')}, [{S/'trace_format/contracts.py'}]({S/'trace_format/contracts.py'}).",
"The language model receives tool numbers through formatted text. These CPU fixtures exercise tools and training renderers; they do not run the RGB model or establish answer quality. The capture replay uses tower geometry and synthetic masks, without a metric-scale estimate. Gravity perturbations change gravity-dependent projections; heading availability does not claim exact invariance to a changed physical gravity vector.",
f"The preserved base and prior overlays verify against their manifests. Lane storage is {total} bytes. Source: {link('PACKET_INTEGRITY_R3.json')}."
]
(O/'CONTRACTS_REPORT_R3.md').write_text('\n\n'.join(report)+'\n')
summary=[f"The r3 packet is ready for independent review. It fixes partial-ground recovery, generator class dispatch, cache binding, status parsing, malformed-row handling, normalization, and application preflight. Source: {link('REVIEW_DISPOSITION_R3.md')}.",
f"The installed-tree checks pass {counts['passed']} tests; all {len(mut['mutations'])} tested mutations are killed, including every reviewed survivor. Sources: {link('FINAL_TEST_RESULTS_R3.json')}, {link('MUTATION_R3.json')}.",
f"The replay covers {t['captures']} captures with {len(t['assertion_failures'])} failed assertions and exact OFF/base parity. Source: {link('real_replay_r3/REAL_GEOMETRY_REPLAY.json')}.",
f"Apply with {link('apply_contract_patches_r3.sh')}. Application, read-only refusal, and reapplication proofs are in {link('APPLY_PROOF_R3.json')}. The full report is {link('CONTRACTS_REPORT_R3.md')}.",
"The proof covers tool behavior and training rendering, not RGB-model accuracy. The gravity-noise evidence distinguishes heading instability from ordinary changes in vertical projection."]
(O/'BUILD5_SUMMARY.md').write_text('\n\n'.join(summary)+'\n')
deliverables=['PATCH_geometry_r3.diff','PATCH_candidates_r3.diff','PATCH_box_r3.diff',
    'PATCH_geometry_on_tree_r1_r3.diff','PATCH_MANIFEST_R3.json','apply_contract_patches_r3.sh',
    'contract_hash_checks_r3.py','APPLY_PROOF_R3.json','FINAL_TEST_RESULTS_R3.json',
    'CHANGED_LINE_COVERAGE_R3.md','HEADING_DEPENDENCE_R3.md','MUTATION_R3.json',
    'REAL_ROW_AUDIT_R3.json','CONTRACTS_REPORT_R3.md','REVIEW_DISPOSITION_R3.md','BUILD5_SUMMARY.md',
    'real_replay_r3/REAL_GEOMETRY_REPLAY.json','real_replay_r3/REAL_GEOMETRY_REPLAY.md']
(O/'PACKET_INDEX_R3.json').write_text(json.dumps({name:dict(path=str(O/name),bytes=(O/name).stat().st_size,
    sha256=sha(O/name)) for name in deliverables},indent=2)+'\n')
print(json.dumps(dict(tests=counts,mutations=len(mut['mutations']),captures=t['captures'],coverage=[covered,changed],lane_bytes=total)))
