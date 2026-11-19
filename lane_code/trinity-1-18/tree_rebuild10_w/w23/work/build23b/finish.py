from pathlib import Path
import ast,difflib,json,math,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23b';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T)]
import joblib as J
from student_pilot.p3_provenance import digest
from student_pilot.source_seal import inventory
kit=J.load(D/'KIT.json');assert digest(inventory(T))==kit['tree_seal'];assert J.seal(B/'kits/q')==kit['kit_seal']
suites=J.load(D/'SUITES.json');assert len(suites)==6 and all(x['returncode']==0 for x in suites)
scan=J.load(D/'SCAN.json');assert scan['status']=='PASS' and scan['kit_seal']==kit['kit_seal']
look=J.load(D/'LOOKAHEAD_AFTER.json');assert look['kit_seal']==kit['kit_seal'] and look['result']['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED'
assert J.load(D/'BEFORE.json')['result']['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED'
assert J.load(D/'AFTER.json')['result']['refusal']=='ValueError:R1_MINIMAL_SLICE_BOUND:r1_training.row_slice_inputs:recovery'
assert J.load(D/'INTEGRITY.json')['status']=='PASS'
counts=[]
for group in ('final_focused','edges','producer_edges','b23b_resolver','b23b_kit','b23b_naming21c','b23b_naming21d','b23b_scanner'):
 v=J.load(B/'proofs'/group/'TESTS.json');assert v['successful'],group;counts.append(dict(group=group,tests=v['tests']))
for path in (L/'work/build23/TESTS.json',L/'work/build23/RESOLVER_TESTS.json',D/'TESTS.json'):
 v=J.load(path);assert v['successful'];counts.append(dict(group=str(path.relative_to(L)),tests=v['tests']))
assert sum(x['tests'] for x in counts[:-1])==204
J.write(D/'TEST_COUNTS.json',dict(total=sum(x['tests'] for x in counts),inherited=204,mutations=counts[-1]['tests'],groups=counts))
capacity=J.load(D/'CAPACITY.json');assert capacity['status']=='PASS' and capacity['source_seal']==kit['tree_seal']
fixture=[]
for step,r in capacity['milestones'].items():
 assert r['status']=='ADMIT';cfg=J.load(Path(r['config']['path']))
 assert J.load(Path(cfg['code']['path']))['tree_sha256']==kit['tree_seal']
 binding=cfg['r2_sampling'];pop=J.load(Path(binding['population']['path']));card=J.load(Path(binding['card']['path']))
 names=[c['type'] for c in card['cells'] if c['stream']=='routing' and c['type']!='routing_base']
 assert all(pop['counts'][n]==0 and r['audit']['draws'].get(n,0)==0 and r['audit']['eligible'].get(n,0)==0 for n in names)
 member=J.load(Path(pop['source_membership']['path']));assert member['sources']=={} and member['base']==cfg['streams']['routing']
 root=Path(r.get('proof_root',D/'proofs'/step/'q'));records=J.load(root/'f.json')['records'];by_rank={}
 for v in records:
  assert v['finite'] and math.isfinite(v['loss']);by_rank.setdefault(str(v['rank']),[]).append(dict(stream=v['stream'],loss=v['loss']))
 assert set(by_rank)=={'0','1','2','3'}
 fixture.append(dict(step=int(step),status='ADMIT',rows=pop['counts'],deferred_counts={n:pop['counts'][n] for n in names},losses_by_rank=by_rank,first_loss_by_rank={k:v[0]['loss'] for k,v in by_rank.items()},steps=r['steps'],proof_root=str(root),source_seal=kit['tree_seal']))
J.write(D/'FIXTURE.json',dict(status='PASS',GO=False,milestones=fixture,stand_ins=capacity['stand_ins'],storage=capacity['storage'],checkpoint_scope='600 reuses final 400 native stores, population and sampler audit; native checkpoint handover and all-rank forward rerun at 600.'))
# Count changed executable statements against the required b262e7a7 base.
old=J.load(D/'BASE_SOURCES.json');coverage={}
roots=[D/'unit',D/'proofs',*[B/'proofs'/g for g in ('final_focused','edges','producer_edges','b23b_resolver','b23b_kit','b23b_naming21c','b23b_naming21d','b23b_scanner')]]
for name,prior in old.items():
 p=T/name;source=p.read_text();changed=set();hits=set();h=J.sha(p)
 for tag,_,_,a,b in difflib.SequenceMatcher(a=prior.splitlines(),b=source.splitlines(),autojunk=False).get_opcodes():
  if tag!='equal':changed.update(range(a+1,b+1))
 for root in roots:
  if (root/'source_hashes.json').exists() and J.load(root/'source_hashes.json').get(name)==h:hits.update(J.load(root/'hits.json').get(name,[]))
 statements={n.lineno for n in ast.walk(ast.parse(source)) if isinstance(n,ast.stmt)}&changed
 coverage[name]=dict(changed_statements=len(statements),covered=len(statements&hits),missing=sorted(statements-hits),sha256=h)
J.write(D/'COVERAGE.json',coverage)
J.write(B/'FINAL_KITS.json',dict(status='PASS',GO=False,tree_seal=kit['tree_seal'],kits={'q':J.load(B/'kits/q/BUILD.json')},decoded_scan=scan,upload_bytes=J.load(B/'UPLOADS.json')['total_bytes'],upload_files=len(J.load(B/'UPLOADS.json')['files']),inherited_kit_note='This delivery certifies q only.'))
uploads=J.load(L/'out/UPLOADS_NEW_23B.json');total=sum(x['tests'] for x in counts);covered=sum(v['covered'] for v in coverage.values());changed=sum(v['changed_statements'] for v in coverage.values())
lines=[
'PASS: review 23 MUST fixed; MINIMAL CPU proof ADMIT. Production GO=false.',
'',
'Central gate: work/tree_r1/student_pilot/r1_coverage.py:deferred; named refusal R1_MINIMAL_SLICE_BOUND:<field>:<name>.',
'Callers: production_proof; entry.admit/frame_host; s1_admission; population produce/bind_prepared/Membership; room census/verify_audit; build before replacing inputs.',
'Entry checks inline fields before staging and authenticated metadata after localization. Native source/row readers run only after these checks.',
'',
'Refused fields (config means r1_training; request means top-level request):',
'- Config/request row_slice_inputs: every entry; only an empty mapping is allowed.',
'- Config/request routing_inputs: any supplied field, including empty/null.',
'- Config/request row_sources: recovery, absolute_distance, units, coverage_distance, coverage_units, camera_wording, all EXTRA_PINS and unknown slice entries.',
'- Config/request source_membership.sources; direct population membership; r2_sampling.population.source_membership: every source entry.',
'- streams.routing.source_membership and request.routing_base.source_membership: any composed binding; mismatched base pins retain R1_ROUTING_BASE_DIFFERS.',
'- r1_training.mix, r2_sampling.card, request.card: rows_per_step/ceiling_rows_per_step of every routing cell except routing_base; deferred population counts and indices, including omitted cells.',
'Sources: work/build23b/SOURCE_FIELDS.json, TREE_CHANGES.json, TESTS.json; out/MINIMAL_TREE.patch.',
'',
'Allowed: row_sources.room and room_programs_excluded are audit provenance; FULL never composes them. The active membership catalog is empty.',
'Allowed: P S1 selection/catalog/base, removal lists, wording exclusions, extent receipts, room authority, component evidence and staged hash inventories; these do not select new slices.',
'The kit omits all five FULL slice entries and rebinds its empty slice audit to the new catalog; store certification and removal/room checks are unchanged.',
'Sources: work/build21/inputs/{a23b,b23b,c23b}.json; work/build23b/INTEGRITY.json.',
'',
'Before: reviewer recovery mutation on b4edc475 reached R1_PROOF_FRAME_HOST_REQUIRED. After: R1_MINIMAL_SLICE_BOUND:r1_training.row_slice_inputs:recovery.',
'Sources: work/build23b/BEFORE.json and AFTER.json. Only CPU stand-in inputs/output paths were used.',
f'Tests: {total} passed = 204 inherited + {counts[-1]["tests"]} binding/path regressions; FULL regression behavior preserved (work/build23b/TEST_COUNTS.json).',
f'Changed-statement coverage: {covered}/{changed}; uncovered lines are explicit in work/build23b/COVERAGE.json.',
f'Decoded scan: PASS, {scan["checked_strings"]} strings (work/build23b/SCAN.json).',
'Look-ahead: final kit own decoded config, mounts and sealed extraction pass; GPU guard E42; native proof reaches R1_PROOF_FRAME_HOST_REQUIRED.',
'The latter is the deliberate Trinity frame-host boundary, not a routing defect (work/build23b/LOOKAHEAD_AFTER.json).',
'',
]
for row in fixture:lines.append(f"Capacity {row['step']}: ADMIT; first losses ranks 0–3: "+', '.join(f"{row['first_loss_by_rank'][str(k)]:.8g}" for k in range(4))+'.')
lines += [
'Every recorded loss is finite; every deferred count/draw is zero. Final-tree source pins, rows and all per-stream losses: work/build23b/FIXTURE.json.',
'400 reruns native preparation, population, production audit, handover and forward; 600 reuses those stores and reruns checkpoint handover/forward.',
'Stand-ins: synthetic RGB/labels, tiny native model, processor constructor, CPU publication collectives. SQLite page size changes storage layout only.',
'',
f'Tree seal: {kit["tree_seal"]} (out/TREE_SEAL.json).',
f'Kit q seal: {kit["kit_seal"]} (work/build21/kits/q/SHA256SUMS.txt).',
f'Upload diff versus bb04241c: {len(uploads)} files, {sum(x["bytes"] for x in uploads)} bytes; every file exists locally and is small.',
'Names, bytes, SHA-256 and local_path: out/UPLOADS_NEW_23B.json; full additions/retirements: work/build23b/UPLOAD_DIFF.json.',
'Patch base b262e7a7 and build-22 integration rules: out/MINIMAL_TREE.patch and out/MINIMAL_MERGE_NOTES.md.',
'P opener rows, step-544 lineage, resolver identities, legality, removals and the DEFERRED boundary remain unchanged (work/build23b/INTEGRITY.json).',
'Build-23 tar remains byte-identical. Superseded fixture bytes remain losslessly compressed in attic; retention hashes are in work/build23b/RETAINED*.json.',
'Package seal, SHA-256, size, stream verification and workspace bytes: work/build23b/DELIVERY.json, external to avoid a circular checksum.',
'Production stores, RGB, large weights, GPU execution and build-22 integration remain unproved. No upload or submission occurred.',
'Writing rule: the requested before/after comparison is retained as regression evidence; the report states the delivered behavior.',
]
assert len(lines)<60,len(lines)
(L/'out/BUILD23B_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='PASS',tests=total,coverage=[covered,changed],report_lines=len(lines))))
