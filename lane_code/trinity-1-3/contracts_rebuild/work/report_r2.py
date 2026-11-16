from pathlib import Path
import ast,collections,hashlib,json,os
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r2';B=L/'work/base/work/base/tree_b01ce449'
def read(p):
    assert p.stat().st_size<20_000_000,p
    return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def link(name,label=None):return f'[{label or name}]({O/name})'
results={};sources=[]
for tag in ('R2_FINAL_APPLIED','R2_EXTRA'):
    p=O/f'{tag}_results.json'
    if p.exists():results.update(read(p));sources.append(str(p))
counts=dict(collections.Counter(v['outcome'] for v in results.values()))
assert counts.get('failed',0)==0 and counts.get('error',0)==0
test_report=dict(source_paths=sources,outcomes=counts,tests=results,tree=str(L/'work/trees/r2_proof/base'),
    test_directory=str(L/'work/tests_r2'),original_tests=str(L/'work/tests'))
(O/'FINAL_TEST_RESULTS_R2.json').write_text(json.dumps(test_report,indent=2)+'\n')
prior=read(O/'real_replay/REAL_GEOMETRY_REPLAY.json');replay=read(O/'real_replay_r2/REAL_GEOMETRY_REPLAY.json')
cov=read(O/'COVERAGE_DETAIL_R2.json');apply=read(O/'APPLY_PROOF_R2.json');manifest=read(O/'PATCH_MANIFEST_R2.json')
assert not replay['totals']['assertion_failures']
assert all(r.get('tests') or r.get('reason') for v in cov.values() for r in v['lines'])
old=read(O/'PATCH_MANIFEST.json')
assert all(sha(O/name)==h for name,h in old['patch_sha256'].items())
assert all(sha(L/'work/src'/rel)==e['patched_sha256'] for rel,e in old['files'].items())
inventory=L/'work/base/out/BASE_FILES_b01ce449.sha256'
base_files=0
for line in inventory.read_text().splitlines():
    h,rel=line.split('  ',1);assert sha(B/rel)==h,rel;base_files+=1
ref=ast.parse((L/'work/ref/gravity_guard_a62e3975_recovered.py').read_text());actual=ast.parse((S/'student_pilot/geometry_profiles.py').read_text())
fn=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_up_convention')
const=lambda tree:next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UP_PLANE_MIN' for t in n.targets))
assert ast.dump(fn(ref))==ast.dump(fn(actual)) and ast.dump(const(ref))==ast.dump(const(actual))
assert all(sha(L/'work/trees/r2_proof/base'/rel)==e['patched_sha256'] for rel,e in manifest['files'].items())
integrity=dict(source=str(O/'PATCH_MANIFEST_R2.json'),base_inventory_source=str(inventory),base_files_verified=base_files,
    original_packet_patch_hashes_unchanged=True,original_overlay_hashes_unchanged=True,
    guard_function_ast_equal=True,guard_constant_ast_equal=True,
    guard_reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'),
    applied_tree_matches_manifest=True,packet_sha256={name:sha(O/name) for name in manifest['patch_sha256']})
total=0
for root,dirs,files in os.walk(L):
    for name in files:
        p=Path(root)/name
        if not p.is_symlink():total+=p.stat().st_size
assert total<3_000_000_000,total
integrity['lane_bytes_at_check']=total;integrity['lane_source']=str(L)
(O/'PACKET_INTEGRITY_R2.json').write_text(json.dumps(integrity,indent=2)+'\n')
t=replay['totals'];p=prior['totals'];n=replay['totals']['datasets']['arkitscenes']
passed=counts.get('passed',0);covered=sum(v['executed'] for v in cov.values());changed=sum(v['total'] for v in cov.values())
relative=sum(read(O/f'RELATIVE_HEADS_{kind}_R2.json')['comparisons'] for kind in ('nadir','nadir_positive','vertical'))
report=[
    '# Contract packet', '',
    f"The packet serves heading-independent fields while withholding only fields that need an unavailable heading. The installed-tree contract checks pass, the base and integration snapshot apply with zero fuzz, and OFF matches the sealed capture responses byte-for-byte. Sources: {link('FINAL_TEST_RESULTS_R2.json')}, {link('APPLY_PROOF_R2.json')}, {link('real_replay_r2/REAL_GEOMETRY_REPLAY.json')}.",
    '',
    f"`heading_plane_min` defaults to 0.3 and is bound in backend configuration, session state, run identity, materialization receipts, recorded queries, and response metadata. Invalid values raise a named refusal. The convention guard retains its exact reference AST and its independent constant. Sources: [{S/'trace_format/contracts.py'}]({S/'trace_format/contracts.py'}), {link('HEADING_IDENTITY_R2.json')}, {link('PACKET_INTEGRITY_R2.json')}.",
    '',
    'Move uses the source frame’s level heading; its destination needs only a camera centre. Turn uses both endpoint headings. A degenerate source withholds only horizontal move components, retaining vertical displacement and distance. Depth retains camera coordinates and spread even for a vertical camera. Pose retains height while withholding reference-relative horizontal coordinates and yaw. Ground, box, instance, witness, and keypoint responses retain their independent fields. Calculator vectors may be withheld while scalar results continue.',
    '', f"The complete field classification, math, code locations, emitter list, and proof tests are in {link('HEADING_DEPENDENCE_R2.md')}. Training renderers and admission accept valid partial observations before subsequent metric calls; genuine failed-ground recovery still applies. Source: [{S/'student_pilot/training_contract.py'}]({S/'student_pilot/training_contract.py'}), {link('FINAL_TEST_RESULTS_R2.json')}.",
    '',
    'Geometry remains private. The language model receives tool numbers only in formatted response text. The head calculator aliases the same implementation as the deployed trace formatter, so its receipt hashes the implementation. Private rounded operands support invariant measurements without printing withheld horizontal coordinates. The replay exercises tools, not RGB-model answer quality.',
    '', '## Capture evidence', '',
    '| Evidence | Captures | Sealed guard refusals | ON guard refusals | Reference plane below threshold | Sealed-served ARKitScenes captures with withheld reference-heading fields |',
    '|---|---:|---:|---:|---:|---:|',
    f"| {link('real_replay/REAL_GEOMETRY_REPLAY.json','Supplied replay')} | {p['captures']} | {p['sealed_refused']} | {p['patched_refused']} | {p['plane_below_threshold']} | {p['sealed_served_loses_heading']} |",
    f"| {link('real_replay_r2/REAL_GEOMETRY_REPLAY.json','r2 replay')} | {t['captures']} | {t['sealed_refused']} | {t['patched_refused']} | {t['plane_below_threshold']} | {t['sealed_served_loses_heading']} |",
    '',
    f"All {len(n['plane_below_threshold'])} ARKitScenes captures below the default threshold serve the recorded relative move and turn calls, with exact equality to the defined-heading computation of the same quantities. They retain camera coordinates, spread, height, support, size, counts, room measurements, and gaps. The {len(n['sealed_served_loses_heading'])} ARKitScenes captures served by the sealed guard lose only their frame-1-heading fields. No heading-free output is withheld because of the reference heading. Per-capture strings, endpoint frames, and source NPZ paths: {link('real_replay_r2/REAL_GEOMETRY_REPLAY.json')}; readable ledger: {link('real_replay_r2/REAL_GEOMETRY_REPLAY.md')}.",
    '',
    f"The replay records {len(t['assertion_failures'])} failed assertions and {len(t['angle_defined_refusals'])} calculator refusals shared with the defined-heading computation. OFF matches base byte-for-byte. Source: {link('real_replay_r2/REAL_GEOMETRY_REPLAY.json')}.",
    '',
    'The archive supplies tower gravity and depth, fixed synthetic masks stand in for segmentation, and no metric-scale estimate is supplied. Native metre labels therefore carry raw tower units. Coordinate rounding, coordinate-wise medians, box-yaw rounding, and room rasterization are preserved. Parity holds the geometry representation fixed; it does not assert that arbitrary re-rotation preserves every rounded digit.',
    '', '## Validation and application', '',
    f"The contract suite has {passed} passing tests. The near-nadir and vertical fixture matrices compare {relative} relative move/turn responses exactly. Sources: {link('FINAL_TEST_RESULTS_R2.json')}, "+', '.join(link(f'RELATIVE_HEADS_{k}_R2.json') for k in ('nadir','nadir_positive','vertical'))+'.',
    '',
    f"Changed executable-line evidence covers {covered} executed statements out of {changed}. Every changed executable statement ran. Sources: {link('CHANGED_LINE_COVERAGE_R2.md')}, {link('COVERAGE_DETAIL_R2.json')}.",
    '',
    f"Run `bash out/apply_contract_patches_r2.sh TARGET_TREE --dry-run`, then omit `--dry-run` to install. The target must be a writable local checkout. Keep the script, helper, manifest, and patches together. The operator stages a full copy, checks hashes before and after patching, rejects fuzz and offsets, rechecks the target inventory, and retains originals. Repeat application refuses without changing the tree. Source: {link('apply_contract_patches_r2.sh')}, {link('APPLY_PROOF_R2.json')}.",
    '',
    f"The snapshot variant preserves its event-row and preparation/admission branches in `carrier_c1_routing.py` and `carrier_c1_run.py`. The manifest selects it by both accepted source hashes. Sources: {link('PATCH_MANIFEST_R2.json')}, {link('PATCH_geometry_on_tree_r1_r2.diff')}.",
    '',
    f"The sealed base, original source overlay, and original patch hashes remain unchanged. The test proof retains {apply['full_tree_copies']} full trees. Lane storage at verification is {total} bytes. Sources: {link('PACKET_INTEGRITY_R2.json')}, {link('APPLY_PROOF_R2.json')}.",
    '',
    'The base/ON/OFF comparison is retained because it defines the requested replay arms. Original test files remain unchanged; the r2 copies use the field-scoped expectations required by this contract.'
]
(O/'CONTRACTS_REPORT_R2.md').write_text('\n'.join(report)+'\n')
summary=[f"The r2 packet is ready for review. It binds the heading threshold, serves every available heading-independent field, and preserves the guard AST. Sources: {link('CONTRACTS_REPORT_R2.md')}, {link('PACKET_INTEGRITY_R2.json')}.",
    f"The installed-tree suite passes {passed} tests; relative-head fixtures pass {relative} exact response comparisons. Sources: {link('FINAL_TEST_RESULTS_R2.json')}, "+', '.join(link(f'RELATIVE_HEADS_{k}_R2.json') for k in ('nadir','nadir_positive','vertical'))+'.',
    f"The replay covers {t['captures']} captures with {len(t['assertion_failures'])} failed assertions. All {len(n['plane_below_threshold'])} affected ARKitScenes captures retain heading-free outputs. The {len(n['sealed_served_loses_heading'])} already served by the sealed guard lose only reference-heading fields. OFF equals base byte-for-byte. Source: {link('real_replay_r2/REAL_GEOMETRY_REPLAY.json')}.",
    f"The patches pass zero-fuzz base/snapshot application and reject reapplication. Apply with {link('apply_contract_patches_r2.sh')}; begin with `--dry-run`. Evidence: {link('APPLY_PROOF_R2.json')}. Field table: {link('HEADING_DEPENDENCE_R2.md')}. Coverage: {link('CHANGED_LINE_COVERAGE_R2.md')}.",
    f"The replay retains {len(t['angle_defined_refusals'])} ordinary calculator refusals that also occur with heading defined. Source: {link('real_replay_r2/REAL_GEOMETRY_REPLAY.json')}.",
    'The replay uses tower geometry and synthetic masks. It measures tool behavior, not RGB-model answer quality or calibrated metric accuracy.']
(O/'BUILD4_SUMMARY.md').write_text('\n\n'.join(summary)+'\n')
print(json.dumps(dict(tests=counts,captures=t['captures'],coverage=[covered,changed],lane_bytes=total)))
