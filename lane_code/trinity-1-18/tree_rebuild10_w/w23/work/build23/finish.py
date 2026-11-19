"""Verify native evidence and write the compact build report."""
from pathlib import Path
import json,math,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23';O=D/'proofs/capacity'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.p3_provenance import digest
from student_pilot.source_seal import inventory
kit=J.load(D/'KIT.json');scan=J.load(D/'SCAN.json');suites=J.load(D/'SUITES.json')
assert scan['status']=='PASS' and len(suites)==6 and all(x['returncode']==0 for x in suites)
assert J.seal(B/'kits/q')==kit['kit_seal']
assert digest(inventory(L/'work/tree_r1'))==kit['tree_seal']
before=J.load(D/'LOOKAHEAD_BEFORE.json');after=J.load(D/'LOOKAHEAD_AFTER.json')
assert before['result']['refusal']=='ValueError:R1_PROOF_NATIVE_ROUTING_REQUIRED'
assert after['result']['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED'
assert after['kit_seal']==kit['kit_seal']
capacity=J.load(O/'RESULT.json');assert capacity['milestones']['400']['status']=='ADMIT'
assert J.load(D/'BOOTSTRAP.json')['status']=='PASS'
fixture=[]
for step,result in capacity['milestones'].items():
    assert result['status']=='ADMIT',result.get('refusal')
    assert 'r1_routing.compose_native' not in result['steps']
    cfg=J.load(Path(result['config']['path']));binding=cfg['r2_sampling']
    pop=J.load(Path(binding['population']['path']));card=J.load(Path(binding['card']['path']))
    deferred={c['type']:pop['counts'][c['type']] for c in card['cells'] if c['stream']=='routing' and c['type']!='routing_base'}
    assert all(n==0 for n in deferred.values())
    audit=result['audit']
    assert all(audit['eligible'].get(k,0)==0 and audit['draws'].get(k,0)==0 for k in deferred)
    assert all(float(c['rows_per_step'])==0 for c in card['cells'] if c['type'] in deferred)
    member=J.load(Path(pop['source_membership']['path']));assert member['sources']=={} and member['base']==cfg['streams']['routing']
    base=J.load(Path(cfg['streams']['routing']['path']));assert 'source_membership' not in base
    proof_root=Path(result.get('proof_root',O/step/'q'))
    forward=J.load(proof_root/'f.json')['records']
    by_rank={}
    for row in forward:
        assert row['finite'] is True and math.isfinite(row['loss'])
        by_rank.setdefault(str(row['rank']),[]).append(dict(stream=row['stream'],loss=row['loss']))
    assert set(by_rank)=={'0','1','2','3'}
    fixture.append(dict(step=int(step),status=result['status'],steps=result['steps'],rows=pop['counts'],deferred_cells=deferred,
        losses_by_rank=by_rank,first_loss_by_rank={k:v[0]['loss'] for k,v in by_rank.items()},regenerated_base=cfg['streams']['routing'],
        base_membership_equal=True,proof_root=str(proof_root),reused_data=result.get('reused_data'),
        loader_deferred_draws={k:audit['draws'].get(k,0) for k in deferred},
        native_frame_host_flag_during_minimal=False,opaque_frame_host_flag_during_minimal=False))
J.write(D/'FIXTURE.json',dict(status='PASS',GO=False,milestones=fixture,stand_ins=capacity['stand_ins'],
    env_proof='native23.py and checkpoint600.py assert both flags absent on the MINIMAL path. Only native23.py synthetic fixture production sets the native flag.'))
tests=[]
for group in ('final_focused','edges','producer_edges','b23_resolver','b23_kit','b23_naming21c','b23_naming21d','b23_scanner'):
    value=J.load(B/'proofs'/group/'TESTS.json');assert value['successful'],group
    tests.append(dict(name=group,tests=value['tests']))
for name in ('TESTS.json','RESOLVER_TESTS.json'):
    value=J.load(D/name);assert value['successful'];tests.append(dict(name=name,tests=value['tests']))
J.write(D/'TEST_COUNTS.json',dict(groups=tests,total=sum(x['tests'] for x in tests)))
coverage=J.load(D/'COVERAGE.json');covered=sum(v['covered'] for v in coverage.values());changed=sum(v['changed_statements'] for v in coverage.values())
uploads=J.load(D/'UPLOAD_DIFF.json')['new_uploads']
lines=[
 'PASS: MINIMAL CPU preparation and all-rank first batches; production remains NO-GO. GO=false.',
 '',
 'The pinned declaration is `r1_training.routing_slices: "deferred_first_boundary"`.',
 'Absent declaration retains FULL. Unknown values, supplied routing_inputs, appended-source rows and nonzero deferred cells refuse.',
 'The config and request bind the same P routing receipt. Native S1 regeneration supplies the final streams.routing without compose_native.',
 'The routing_base cell receives 64 slots per step; P’s existing distance rows remain in the base. Every deferred routing cell has zero rows and draws.',
 'Sources: work/build21/inputs/mix.json; work/build23/FIXTURE.json; out/MINIMAL_TREE.patch.',
 '',
 'Tree changes: student_pilot/{r1_coverage,r1_population,r1_rooms,s1_admission}.py and launch_r1/{build,entry,production_proof}.py.',
 'The final launch entry defers recovery/unit minimums only under the declaration. Admission, legality, removals, wording, room/K1 and DEFERRED checks remain.',
 'Kit-only resolver fix: preserve N’s non-routing streams and bind P’s routing base; a different base refuses E55.',
 'The kit supplies an explicitly incomplete preparation population. The sampler refuses it until native population binding replaces it (work/build23/BOOTSTRAP.json).',
 'Resolver identity functions, P’s trained opener policy and step-544 lineage remain unchanged (work/build23/INTEGRITY.json).',
 'The env-alias proposal is not applied: the look-ahead stops before readers, and the MINIMAL fixture readers pass without either flag. Only fixture production sets the native flag.',
 '',
 'P base receipt: ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984.',
 'P database: 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84.',
 'Source: ../ext/m400real/r.json and work/build23/KIT.json. The real database was neither copied nor read here.',
 f'Tree seal: {kit["tree_seal"]} (out/TREE_SEAL.json).',
 f'Kit q seal: {kit["kit_seal"]} (work/build21/kits/q/SHA256SUMS.txt).',
 '',
 f'Tests: {sum(x["tests"] for x in tests)} passed (work/build23/TEST_COUNTS.json); decoded scan PASS (work/build23/SCAN.json).',
 'Before/after evidence: work/build23/BEFORE.json, ENTRY_BEFORE_AFTER.json, RESOLVER.json and LOOKAHEAD_{BEFORE,AFTER}.json.',
 'Mutations cover unknown declarations, envelopes present with MINIMAL, nonzero deferred requests/counts/indices, stream relabeling, appended rows and changed base pins.',
 f'Changed-statement coverage: {covered}/{changed}; exact uncovered lines are in work/build23/COVERAGE.json.',
 'Harness fixes restore packaged fixture aliases, regenerate the partial synthetic constant fixture, and make the room-report test self-contained.',
 '',
 '| Look-ahead stage | Result | Interpretation |',
 '| --- | --- | --- |',
 '| bwrap mounts and sealed extraction | PASS | Same stand-in view as build 21g |',
 '| Real GPU guard | E42 | CPU/GPU boundary; unchanged |',
 '| Old kit’s decoded config | R1_PROOF_NATIVE_ROUTING_REQUIRED | Reproduced defect |',
 '| MINIMAL kit’s decoded config | R1_PROOF_FRAME_HOST_REQUIRED | Passed routing/card/room gates; deliberate Trinity boundary |',
 'Sources: work/build23/LOOKAHEAD_BEFORE.json and LOOKAHEAD_AFTER.json. Production stores, RGB and large weights remain unproved.',
 '',
 '| Capacity milestone | Status | First loss on ranks 0, 1, 2, 3 |',
 '| --- | --- | --- |',
 ]
for row in fixture:
    lines.append('| '+str(row['step'])+' | '+row['status']+' | '+', '.join(f'{row["first_loss_by_rank"][str(rank)]:.8g}' for rank in range(4))+' |')
lines += [
 'Every recorded loss is finite. Full per-stream/rank losses, zero deferred-cell counts and retained-base pins: work/build23/FIXTURE.json.',
 'If present, step 600 reuses the step-400 native stores, population and sampler audit; its persisted checkpoint admission and all-rank forward run at 600.',
 'The fixture uses synthetic frames/labels, tiny native model dimensions and the declared processor/host boundaries; native producers, readers, audit and forward run.',
 '',
 f'Upload diff versus 21g: {len(uploads)} files, {sum(x["bytes"] for x in uploads)} bytes; largest {max(x["bytes"] for x in uploads)} bytes.',
 'Every changed upload exists locally and is small. Exact names, bytes and sha256: out/UPLOADS_NEW.json; full diff: work/build23/UPLOAD_DIFF.json.',
 'No upload, network, Orchard, GPU, scheduler, Git, SSH, other agent or deletion was used.',
 'Build 22 is not merged here. out/MINIMAL_MERGE_NOTES.md specifies how its camera slice stays deferred and its removals/twins remain active.',
 'Package checksum, byte count and stream verification: work/build23/DELIVERY.json (external record created after packaging).',
 'The package omits generated capacity databases and model payloads; work/build23/native23.py reconstructs them under the stated limits.',
 'The inherited r1 kit retains its base seal. This delivery certifies kit q only.',
 ]
assert len(lines)<100
(L/'out/BUILD23_REPORT.md').write_text('\n'.join(lines)+'\n')
(B/'STATUS.md').write_text('Build 23 supplies the explicit MINIMAL kit q. GO=false. See out/BUILD23_REPORT.md and work/build23/DELIVERY.json.\n')
J.write(D/'STATUS.json',dict(status='VALIDATED',GO=False,tree_seal=kit['tree_seal'],kit_seal=kit['kit_seal'],
    tests=sum(x['tests'] for x in tests),capacity_milestones=[r['step'] for r in fixture],package='See DELIVERY.json after packaging.'))
print(json.dumps(dict(report_lines=len(lines),tests=sum(x['tests'] for x in tests),fixture=[r['step'] for r in fixture],coverage=[covered,changed])))
